"""
app.py — Smart Sales Forecasting System v4
- No data visible until dataset is uploaded
- Full Category & Product analysis tab
- Auto-analysis on upload
- Pop-out validation errors
- Dynamic forecast periods
- Duration-normalised seasonal analysis
- KMeans area clustering
- Analysis History tab
"""

import streamlit as st
import pandas as pd
import tempfile, shutil, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from modules.preprocessing    import (load_and_clean, get_weekly_series,
                                       get_daily_series, get_monthly_series,
                                       extend_series_through,
                                       validate_dataframe)
from modules.forecasting      import (fit_and_forecast, plot_forecast,
                                       periods_for_horizon)
from modules.analysis         import season_analysis, area_analysis, monthly_trend
from modules.product_analysis import (category_summary, category_revenue_chart,
                                       category_monthly_trend, category_avg_price_chart,
                                       category_season_heatmap, category_vs_zone_chart,
                                       product_summary, top_products_chart,
                                       product_units_chart, product_monthly_trend,
                                       product_price_distribution)
from modules.price_optimizer  import (compute_elasticity, optimal_price_range,
                                       revenue_optimal_price, plot_price_demand,
                                       plot_all_categories_elasticity)
from modules.insights         import generate_insights, format_insights_text
from modules.history_manager  import save_session, load_history, delete_session, clear_all
from salespulse_utils.helpers import (summary_kpis, dataset_signal_metrics,
                                      PRIORITY_COLORS, PRIORITY_EMOJIS,
                                      fmt_currency, fmt_number)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SalePulse",
    page_icon=r"C:\Users\Piyush sharma\OneDrive\Documents\Desktop\SalesPulse\app_logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Landing screen ── */
.landing-wrap {
    display:flex; flex-direction:column; align-items:center;
    justify-content:center; padding:5rem 2rem; text-align:center;
}
.landing-icon { font-size:5rem; margin-bottom:1rem; }
.landing-title { font-size:2.4rem; font-weight:800; color:#1e3a5f; margin:0; }
.landing-sub   { font-size:1.1rem; color:#64748b; margin:.6rem 0 2rem; }
.landing-hint  {
    background:#f0f9ff; border:1px solid #bae6fd; border-radius:10px;
    padding:1.2rem 2rem; color:#0369a1; font-size:.95rem; max-width:520px;
}
.landing-hint b { color:#0c4a6e; }
/* ── Header ── */
.main-header {
    background:linear-gradient(135deg,#1e3a5f 0%,#F97316 100%);
    padding:1.2rem 2rem; border-radius:12px; color:white; margin-bottom:1rem;
}
/* ── KPI cards ── */
.kpi-card {
    background:white; border:1px solid #e2e8f0; border-radius:10px;
    padding:.85rem; text-align:center; box-shadow:0 1px 4px rgba(0,0,0,.06);
}
.kpi-value { font-size:1.35rem; font-weight:700; color:#1e3a5f; }
.kpi-label { font-size:.72rem; color:#64748b; margin-top:2px; }
/* ── Section headers ── */
.section-title {
    font-size:1.15rem; font-weight:700; color:#1e3a5f;
    border-left:4px solid #F97316; padding-left:.7rem; margin:1rem 0 .5rem;
}
/* ── Insight cards ── */
.insight-card {
    border-left:4px solid; border-radius:8px;
    padding:.85rem 1rem; margin-bottom:.6rem; background:#f8fafc;
}
/* ── Error box ── */
.err-box {
    background:#fef2f2; border:1.5px solid #ef4444; border-radius:8px;
    padding:.9rem 1.1rem; color:#991b1b; margin-bottom:.5rem;
    font-family:monospace; font-size:.87rem;
}
/* ── History card ── */
.hist-card {
    background:#f8fafc; border:1px solid #cbd5e1; border-radius:10px;
    padding:.9rem 1.1rem; margin-bottom:.5rem;
}
/* ── Season note ── */
.season-note {
    background:#fffbeb; border:1px solid #f59e0b; border-radius:6px;
    padding:.5rem .85rem; font-size:.83rem; color:#92400e; margin-bottom:.8rem;
}
/* ── Tab font ── */
[data-testid="stTab"] { font-size:.92rem; font-weight:600; }
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df           = None
if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = None
if "last_saved_key" not in st.session_state:
    st.session_state.last_saved_key = None

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Smart Sales Forecast")
    st.markdown("---")

    st.markdown("### 📂 Dataset")
    uploaded = st.file_uploader(
        "Upload CSV or XLSX",
        type=["csv","xlsx","xls"],
        help="Any sales file — columns auto-detected"
    )
    use_sample = st.checkbox(
        "Use built-in Flipkart dataset",
        value=False,
        help="133,503 orders · 5 categories · 4 zones · 2015-2020"
    )

    st.markdown("---")
    st.markdown("### 🔮 Forecast Settings")
    freq_mode = st.radio("Forecast granularity", ["Weekly", "Daily", "Monthly"])
    horizon_label = st.selectbox(
        "Analysis & forecast duration",
        ["1 month", "3 months (Quarterly)",
         "6 months (Half-yearly)", "12 months (1 year)"],
    )
    horizon_months = {
        "1 month": 1,
        "3 months (Quarterly)": 3,
        "6 months (Half-yearly)": 6,
        "12 months (1 year)": 12,
    }[horizon_label]
    st.caption(
        "KPIs and analysis use this trailing historical window; forecasting "
        "trains on all available history."
    )

    st.markdown("---")
    st.markdown("### 🔍 Forecast Filter")
    filter_by = st.radio("Scope", ["All Data", "Category", "Product"])

# ─────────────────────────────────────────────────────────────────────────────
# FILE LOADING & VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
def _save_temp(file) -> str:
    ext = ".xlsx" if file.name.lower().endswith(("xlsx","xls")) else ".csv"
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    shutil.copyfileobj(file, tmp); tmp.close()
    return tmp.name


def _show_validation_errors(errors: list):
    st.error("🚫 **Invalid Dataset — Cannot Analyse**")
    for err in errors:
        st.markdown(f'<div class="err-box">{err}</div>', unsafe_allow_html=True)
    st.info(
        "💡 **Required columns (any of these names work):**\n"
        "- **Date**: `OrderDate`, `date`, `sale_date`, `transaction_date`\n"
        "- **Quantity**: `Order Quantity`, `qty`, `units_sold`, `amount`\n"
        "- **Price**: `Sale Price`, `price`, `Unit Price`, `selling_price`, `Price_INR`\n\n"
        "Optional: product/category, City or Region, discounts, stock, profit margin, "
        "customer satisfaction/rating, reviews, returns, delivery time and repeat-customer data."
    )


# Handle upload trigger
if uploaded is not None:
    file_key = f"{uploaded.name}_{uploaded.size}"
    if st.session_state.dataset_name != file_key:
        # New file — validate first
        ext = ".xlsx" if uploaded.name.lower().endswith(("xlsx","xls")) else ".csv"
        tmp_path = _save_temp(uploaded)
        try:
            raw = pd.read_excel(tmp_path, nrows=50) if ext==".xlsx" else pd.read_csv(tmp_path, nrows=50)
            is_valid, errors = validate_dataframe(raw)
            if not is_valid:
                _show_validation_errors(errors)
                st.stop()
            with st.spinner(f"⚙️ Loading **{uploaded.name}**…"):
                st.session_state.df           = load_and_clean(tmp_path)
                st.session_state.dataset_name = file_key
                st.session_state.last_saved_key = None
            st.toast(f"✅ {uploaded.name} loaded — {len(st.session_state.df):,} rows!", icon="✅")
        except Exception as e:
            st.error(f"🚫 **Failed to read file:** {e}")
            st.stop()

elif use_sample:
    sample_key = "Flipkart_Sales_Dataset.xlsx_builtin"
    if st.session_state.dataset_name != sample_key:
        with st.spinner("Loading Flipkart dataset…"):
            st.session_state.df           = load_and_clean("data/Flipkart_Sales_Dataset.xlsx")
            st.session_state.dataset_name = sample_key
            st.session_state.last_saved_key = None
        st.toast("✅ Flipkart dataset loaded!", icon="✅")

# ─────────────────────────────────────────────────────────────────────────────
# LANDING SCREEN — shown until data is loaded
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.df is None:
    st.markdown("""
    <div class="landing-wrap">
      <div class="landing-icon">📊</div>
      <h1 class="landing-title">Smart Sales Forecasting System</h1>
      <p class="landing-sub">AI-powered demand forecasting, product analytics &amp; business insights</p>
      <div class="landing-hint">
        <b>👈 Upload your dataset from the sidebar to begin</b><br><br>
        Accepts any <code>.csv</code> or <code>.xlsx</code> file with columns for
        <b>Date</b>, <b>Quantity</b> and <b>Price</b>.<br>
        Column names are auto-detected — no reformatting needed.<br><br>
        Or tick <b>"Use built-in Flipkart dataset"</b> to explore a live demo instantly.
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("### What data improves your analysis?")
    st.markdown(
        "**Required for sales forecasts:** a transaction/order date, units/quantity sold, "
        "and sale/unit price. Common headers such as `OrderDate`, `Sale_Date`, "
        "`Order Quantity`, `Units_Sold`, `Sale Price`, and `Price_INR` are recognized.\n\n"
        "**For customer reliability:** add `Customer_Satisfaction` or `Rating`, "
        "`Reviews_Count`, `Return_Rate_Percent`, `Delivery_Days`, and `Repeat_Customer`. "
        "These allow the dashboard to summarize satisfaction, feedback, returns, delivery "
        "experience, and repeat-customer share.\n\n"
        "**For richer business decisions:** product/category, `Discount_Percent`, "
        "`Profit_Margin_Percent`, `Stock_Available`, `Demand_Level`, "
        "`Competitor_Price_INR`, `Website_Visits`, `Cart_Additions`, "
        "`Conversion_Rate_Percent`, and `Ad_Spend_INR` add pricing, inventory, and "
        "marketing context. Location analysis uses **City** when both City and Region "
        "are present; Region is used when City is unavailable."
    )

    # Feature preview cards
    st.markdown("---")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    for col, icon, label in [
        (c1,"📈","ARIMA Forecast"),
        (c2,"🛍️","Category & Product Analysis"),
        (c3,"🌸","Season Analysis"),
        (c4,"🌍","Zone Clustering"),
        (c5,"💰","Price Optimisation"),
        (c6,"🕐","History Log"),
    ]:
        col.markdown(f"""<div class="kpi-card">
          <div style="font-size:1.8rem;">{icon}</div>
          <div class="kpi-label" style="font-size:.8rem;margin-top:4px;">{label}</div>
        </div>""", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# DATA IS LOADED — show everything below
# ─────────────────────────────────────────────────────────────────────────────
source_df = st.session_state.df
analysis_end = source_df["Date"].max()
analysis_start = analysis_end - pd.DateOffset(months=horizon_months)
df = source_df.loc[source_df["Date"] >= analysis_start].copy()
if df.empty:
    st.error("No sales records fall within the selected analysis duration.")
    st.stop()
dataset_name = uploaded.name if uploaded else "Flipkart_Sales_Dataset.xlsx"

# ── App header ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
  <h1 style="margin:0;font-size:1.65rem;">📊 Smart Sales Forecasting System</h1>
  <p style="margin:3px 0 0;opacity:.85;font-size:.85rem;">
    Dataset: <b>{dataset_name}</b> &nbsp;·&nbsp;
    Analysis window: <b>{df['Date'].min().date()} → {df['Date'].max().date()}</b>
    &nbsp;·&nbsp; {len(df):,} rows &nbsp;·&nbsp; Forecast: {horizon_label}
  </p>
</div>""", unsafe_allow_html=True)

# ── KPI bar ───────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="section-title">📌 Summary for selected window · {horizon_label}</div>',
    unsafe_allow_html=True,
)
kpis = summary_kpis(df)
kpi_cols = st.columns(len(kpis))
for col, (label, value) in zip(kpi_cols, kpis.items()):
    col.markdown(f"""<div class="kpi-card">
      <div class="kpi-value">{value}</div>
      <div class="kpi-label">{label}</div></div>""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

customer_signals, business_signals = dataset_signal_metrics(df)
st.markdown(
    f'<div class="section-title">🛡️ Customer reliability & business signals · '
    f'{horizon_label}</div>',
            unsafe_allow_html=True)
st.caption(
    f"Calculated from {len(df):,} rows dated "
    f"{df['Date'].min().date()} through {df['Date'].max().date()}."
)
if customer_signals:
    signal_cols = st.columns(min(5, len(customer_signals)))
    for col, (label, value) in zip(signal_cols, customer_signals.items()):
        col.metric(label, value)
else:
    st.info(
        "No customer reliability fields detected yet. Add satisfaction or ratings, "
        "review counts, return rate, delivery days, or repeat-customer status to "
        "measure customer experience and loyalty."
    )
if business_signals:
    st.markdown("**Available commercial signals**")
    signal_cols = st.columns(min(5, len(business_signals)))
    for col, (label, value) in zip(signal_cols, business_signals.items()):
        col.metric(label, value)
else:
    st.caption(
        "Optional discount, margin, inventory, demand, competitor, and marketing "
        "columns can unlock additional business summaries."
    )

# ── Dynamic sidebar filter options ───────────────────────────────────────────
categories    = sorted(df["Category"].unique().tolist()) if "Category" in df.columns else []
products      = sorted(df["Product"].unique().tolist())
selected_cat  = None
selected_prod = None
selected_area = None
filter_label  = "All Data"

if filter_by == "Category" and categories:
    selected_cat  = st.sidebar.selectbox("Category", categories)
    filter_label  = f"Category: {selected_cat}"
elif filter_by == "Product":
    selected_prod = st.sidebar.selectbox("Product", products)
    filter_label  = f"Product: {selected_prod}"

area_level = df["Area_Level"].iloc[0] if "Area_Level" in df.columns else "Area"
if area_level == "City" or df["Area"].nunique() > 1:
    area_label = "City" if area_level == "City" else "Location"
    area_options = sorted(df["Area"].dropna().unique().tolist())
    selected_area = st.sidebar.selectbox(
        f"Forecast {area_label.lower()}",
        [None, *area_options],
        format_func=lambda value: f"All {area_label}s" if value is None else value,
    )
    if selected_area is not None:
        filter_label = f"{filter_label} · {area_label}: {selected_area}"

# ─────────────────────────────────────────────────────────────────────────────
# RUN ALL ANALYSES (cached)
# ─────────────────────────────────────────────────────────────────────────────
freq = {"Daily": "D", "Weekly": "W", "Monthly": "MS"}[freq_mode]

@st.cache_data(show_spinner=False)
def run_analyses(source_df, analysis_df, freq, horizon_months,
                 category, product, area, dataset_end):
    forecast_df = source_df
    if area is not None:
        forecast_df = forecast_df[forecast_df["Area"] == area]
    if freq == "D":
        series = get_daily_series(
            forecast_df, product=product, category=category)
    elif freq == "MS":
        series = get_monthly_series(
            forecast_df, product=product, category=category)
    else:
        series = get_weekly_series(
            forecast_df, product=product, category=category)
    series = extend_series_through(series, dataset_end, freq)
    periods = periods_for_horizon(
        series.index[-1], horizon_months, freq, horizon_from=dataset_end)
    if periods < 1:
        raise ValueError(
            "The selected duration is too short to contain a forecast period "
            "at this granularity."
        )
    fr  = fit_and_forecast(series, periods=periods, freq=freq)
    sa  = season_analysis(analysis_df)
    area_label = (
        analysis_df["Area_Level"].iloc[0]
        if "Area_Level" in analysis_df.columns else "Area"
    )
    aa  = area_analysis(analysis_df, area_label=area_label)
    em = {
        c: compute_elasticity(analysis_df, category=c)
        for c in analysis_df["Category"].unique()
    }
    om = {
        c: optimal_price_range(analysis_df, category=c)
        for c in analysis_df["Category"].unique()
    }
    ins = generate_insights(
        analysis_df, fr, sa["summary"], aa["summary"], em, om)
    return fr, sa, aa, em, om, ins

with st.spinner("🔄 Running analysis…"):
    try:
        fr, sa, aa, em, om, insights = run_analyses(
            source_df, df, freq, horizon_months,
            selected_cat, selected_prod, selected_area, analysis_end)
    except ValueError as ve:
        st.error(f"🚫 {ve}"); st.stop()

# Auto-save session
forecast_periods = fr["periods"]
_sk = f"{dataset_name}|{freq}|{horizon_months}|{filter_label}"
if st.session_state.last_saved_key != _sk:
    save_session(
        dataset_name=dataset_name, total_rows=len(df),
        date_range=f"{df['Date'].min().date()} → {df['Date'].max().date()}",
        num_products=df["Product"].nunique(), num_areas=df["Area"].nunique(),
        total_revenue=float(df["Revenue"].sum()),
        total_units=int(df["Sales_Quantity"].sum()),
        forecast_periods=int(forecast_periods), forecast_freq=freq_mode,
        forecast_avg=float(fr["forecast"].mean()),
        best_season=sa["best_season"], top_area=aa["top_area"],
        insights_count=len(insights),
        high_priority_count=sum(1 for i in insights if i.priority=="High"),
        filter_used=filter_label, insights_text=format_insights_text(insights),
    )
    st.session_state.last_saved_key = _sk

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 Forecast",
    "🛍️ Categories",
    "📦 Products",
    "🌸 Seasonality",
    f"🌍 {df['Area_Level'].iloc[0] if 'Area_Level' in df.columns else 'Areas'} & Zones",
    "💰 Price Analysis",
    "🤖 AI Insights & History",
])

# ══════════════════════════ TAB 1 — FORECAST ══════════════════════════════════
with tab1:
    freq_lbl = freq_mode
    scope    = selected_cat or selected_prod or "All Data"
    if selected_area is not None:
        scope = f"{scope} · {area_label}: {selected_area}"
    title    = f"{scope} — {horizon_label} {freq_lbl.lower()} forecast"

    st.markdown(f'<div class="section-title">🔮 ARIMA {freq_lbl} Forecast · {scope}</div>',
                unsafe_allow_html=True)
    st.plotly_chart(
        plot_forecast(fr, title=title, show_history=False),
        use_container_width=True,
    )
    st.caption(
        f"Forecast dates: {fr['forecast'].index.min().date()} to "
        f"{fr['forecast'].index.max().date()} "
        f"({len(fr['forecast'])} {freq_lbl.lower()} forecast points)."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**📋 Forecast Values**")
        fdf = fr["forecast"].reset_index()
        period_column = {"Daily": "Date", "Weekly": "Week", "Monthly": "Month"}[freq_mode]
        fdf.columns = [period_column, "Forecast (units)"]
        fdf["Forecast (units)"] = fdf["Forecast (units)"].round(0).astype(int)
        fdf[period_column] = fdf[period_column].dt.date
        st.dataframe(fdf, use_container_width=True, hide_index=True)

    with c2:
        st.markdown("**🔢 Model Details**")
        h_avg = fr["hist_avg"]; f_avg = fr["fore_avg"]
        chg   = (f_avg - h_avg) / (h_avg + 1e-9) * 100
        st.code(
            f"ARIMA Order     : {fr['order']}\n"
            f"Frequency       : {freq_lbl}\n"
            f"Forecast period : {horizon_label}\n"
            f"Steps ahead     : {forecast_periods}\n"
            f"Training obs    : {len(fr['history'])}\n"
            f"AIC             : {fr.get('aic','N/A')}\n"
            f"Recent avg      : {h_avg:.0f} units\n"
            f"Forecast avg    : {f_avg:.0f} units\n"
            f"Change          : {chg:+.1f}%\n"
            f"Scope           : {filter_label}"
        )
    with st.expander("ARIMA model summary"):
        st.text(fr["model_summary"])

# ══════════════════════════ TAB 2 — CATEGORIES ════════════════════════════════
with tab2:
    st.markdown('<div class="section-title">🛍️ Category-wise Analysis</div>',
                unsafe_allow_html=True)

    cat_df = category_summary(df)

    # KPI row for categories
    cat_kpi_cols = st.columns(len(cat_df))
    for col, (_, row) in zip(cat_kpi_cols, cat_df.iterrows()):
        col.markdown(f"""<div class="kpi-card">
          <div class="kpi-value" style="font-size:1.1rem;">{row['Category']}</div>
          <div style="font-size:1rem;font-weight:700;color:#F97316;">
              {fmt_currency(row['Total_Revenue'])}</div>
          <div class="kpi-label">{fmt_number(row['Total_Units'])} units · 
              {row['Revenue_Share_%']}% share</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Revenue share donut + units bar
    st.plotly_chart(category_revenue_chart(cat_df), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(category_avg_price_chart(cat_df), use_container_width=True)
    with c2:
        st.plotly_chart(category_vs_zone_chart(df),       use_container_width=True)

    # Monthly area chart
    st.plotly_chart(category_monthly_trend(df), use_container_width=True)

    # Season heatmap
    st.plotly_chart(category_season_heatmap(df), use_container_width=True)

    # Full stats table
    st.markdown("**📊 Category Summary Table**")
    display_cat = cat_df.copy()
    display_cat["Total_Revenue"] = display_cat["Total_Revenue"].apply(
        lambda x: fmt_currency(float(x)))
    display_cat["Avg_Price"] = display_cat["Avg_Price"].apply(
        lambda x: f"₹{x:.2f}")
    st.dataframe(display_cat, use_container_width=True, hide_index=True)

# ══════════════════════════ TAB 3 — PRODUCTS ══════════════════════════════════
with tab3:
    st.markdown('<div class="section-title">📦 Product-wise Analysis</div>',
                unsafe_allow_html=True)

    # Filter controls
    pc1, pc2 = st.columns([2, 1])
    with pc1:
        prod_cat_filter = st.selectbox(
            "Filter by Category (or 'All')",
            ["All"] + categories,
            key="prod_cat_filter"
        )
    with pc2:
        top_n = st.slider("Show top N products", 5, 44, 15, key="top_n_slider")

    cat_arg  = None if prod_cat_filter == "All" else prod_cat_filter
    prod_df  = product_summary(df, category=cat_arg, top_n=top_n)

    # Top products horizontal bar
    title_str = (f"Top {top_n} Products" +
                 (f" — {prod_cat_filter}" if cat_arg else " — All Categories"))
    st.plotly_chart(top_products_chart(prod_df, title=title_str),
                    use_container_width=True)

    # Revenue vs units bubble
    st.plotly_chart(product_units_chart(prod_df), use_container_width=True)

    # Product stats table
    st.markdown("**📊 Product Summary Table**")
    display_prod = prod_df.copy()
    display_prod["Total_Revenue"] = display_prod["Total_Revenue"].apply(
        lambda x: fmt_currency(float(x)))
    display_prod["Avg_Price"] = display_prod["Avg_Price"].apply(
        lambda x: f"₹{x:.2f}")
    display_prod["Product"] = display_prod["Product"].str[:60]
    st.dataframe(display_prod, use_container_width=True, hide_index=True)

    st.markdown("---")
    # Drill-down: single product trend
    st.markdown('<div class="section-title">🔎 Single Product Deep Dive</div>',
                unsafe_allow_html=True)
    drill_cat  = st.selectbox("Category", categories, key="drill_cat")
    drill_prods = sorted(df[df["Category"]==drill_cat]["Product"].unique().tolist())
    drill_prod = st.selectbox("Product", drill_prods, key="drill_prod")

    dc1, dc2 = st.columns(2)
    with dc1:
        st.plotly_chart(product_monthly_trend(df, drill_prod),
                        use_container_width=True)
    with dc2:
        st.plotly_chart(product_price_distribution(df, drill_cat),
                        use_container_width=True)

    # Single product stats — direct column ops (named agg on DF returns transposed DF, not Series)
    _sub   = df[df["Product"] == drill_prod]
    _rev   = float(_sub["Revenue"].sum())
    _units = float(_sub["Sales_Quantity"].sum())
    _price = float(_sub["Price"].mean())
    _ord   = int(len(_sub))
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Total Revenue", fmt_currency(_rev))
    sc2.metric("Units Sold",    fmt_number(_units))
    sc3.metric("Avg Price",     f"₹{_price:.2f}")
    sc4.metric("Orders",        f"{_ord:,}")

# ══════════════════════════ TAB 4 — SEASONALITY ═══════════════════════════════
with tab4:
    st.markdown('<div class="section-title">🌸 Season-wise Analysis (Indian Calendar)</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="season-note">📌 <b>Duration-Normalised Intensity:</b> '
        'Sales ÷ season length (months) — fairly compares Festive (2mo) vs Monsoon (4mo). '
        'Winter=3mo · Summer=3mo · Monsoon=4mo · Festive=2mo</div>',
        unsafe_allow_html=True)

    st.plotly_chart(sa["chart"],     use_container_width=True)
    st.plotly_chart(sa["rev_chart"], use_container_width=True)
    st.plotly_chart(sa["heatmap"],   use_container_width=True)

    sc1, sc2 = st.columns(2)
    with sc1:
        st.plotly_chart(monthly_trend(df), use_container_width=True)
    with sc2:
        st.markdown("**📊 Season Summary**")
        ssdf = sa["summary"].copy()
        ssdf["Total_Revenue"] = ssdf["Total_Revenue"].apply(
            lambda x: fmt_currency(float(x)))
        show_cols = [c for c in
                     ["Season","Total_Sales","Season_Months",
                      "Sales_Per_Month","Rev_Per_Month","Total_Revenue"]
                     if c in ssdf.columns]
        st.dataframe(ssdf[show_cols], use_container_width=True, hide_index=True)
        st.success(f"🏆 Highest intensity: **{sa['best_season']}**")
        st.warning(f"📉 Lowest intensity:  **{sa['worst_season']}**")
        st.info(   f"📦 Highest raw volume: **{sa['best_raw']}**")

# ══════════════════════════ TAB 5 — AREAS ════════════════════════════════════
with tab5:
    area_label = df["Area_Level"].iloc[0] if "Area_Level" in df.columns else "Area"
    st.markdown(f'<div class="section-title">🌍 {area_label} Performance</div>',
                unsafe_allow_html=True)

    ac1, ac2 = st.columns(2)
    with ac1:
        st.plotly_chart(aa["bar_chart"],   use_container_width=True)
    with ac2:
        st.plotly_chart(aa["group_chart"], use_container_width=True)

    st.markdown(f"**📊 {area_label} Summary Table**")
    adf = aa["summary"].copy()
    adf.rename(columns={"Area": area_label}, inplace=True)
    adf["Total_Revenue"] = adf["Total_Revenue"].apply(lambda x: fmt_currency(float(x)))
    st.dataframe(adf, use_container_width=True, hide_index=True)
    st.info(f"🏅 Top {area_label.lower()}: **{aa['top_area']}**")

# ══════════════════════════ TAB 6 — PRICE ═════════════════════════════════════
with tab6:
    st.markdown('<div class="section-title">💰 Price vs Demand Analysis</div>',
                unsafe_allow_html=True)

    st.plotly_chart(plot_all_categories_elasticity(df), use_container_width=True)

    if categories:
        sel_cat_p = st.selectbox("Category for scatter", categories, key="price_cat_sel")
        st.plotly_chart(plot_price_demand(df, sel_cat_p), use_container_width=True)

    price_rows = []
    for cat in categories:
        e   = em.get(cat, {})
        o   = om.get(cat, {})
        rev = revenue_optimal_price(df, category=cat)
        price_rows.append({
            "Category":       cat,
            "Elasticity":     e.get("elasticity", "N/A"),
            "Interpretation": e.get("interpretation", ""),
            "Optimal Range":  f"₹{o.get('min_price','?')} – ₹{o.get('max_price','?')}",
            "Best Rev. Price":f"₹{rev}",
        })
    st.dataframe(pd.DataFrame(price_rows), use_container_width=True, hide_index=True)

# ══════════════════════════ TAB 7 — INSIGHTS + HISTORY ═══════════════════════
with tab7:
    ins_tab, hist_tab = st.tabs(["🤖 AI Recommendations", "🕐 Analysis History"])

    # ── Insights ─────────────────────────────────────────────────────────────
    with ins_tab:
        st.markdown('<div class="section-title">🤖 AI-Powered Recommendations</div>',
                    unsafe_allow_html=True)
        prio_filter = st.multiselect(
            "Filter by priority", ["High","Medium","Low"],
            default=["High","Medium","Low"])
        filtered = [i for i in insights if i.priority in prio_filter]

        st.markdown(f"**{len(filtered)} recommendations** · "
                    f"{sum(1 for i in filtered if i.priority=='High')} high priority")

        for ins in filtered:
            color = PRIORITY_COLORS[ins.priority]
            emoji = PRIORITY_EMOJIS[ins.priority]
            st.markdown(f"""
            <div class="insight-card" style="border-color:{color};">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <b>{ins.category} — {ins.title}</b>
                <span style="color:{color};font-weight:600;font-size:.8rem;">
                    {emoji} {ins.priority}</span>
              </div>
              <p style="margin:5px 0 3px;color:#334155;font-size:.9rem;">{ins.detail}</p>
              <p style="margin:0;color:#16a34a;font-size:.88rem;">
                  <b>✅ Action:</b> {ins.action}</p>
            </div>""", unsafe_allow_html=True)

        st.download_button(
            "📥 Download Recommendations",
            format_insights_text(insights),
            f"recommendations_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            "text/plain"
        )

    # ── History ───────────────────────────────────────────────────────────────
    with hist_tab:
        st.markdown('<div class="section-title">🕐 Analysis History</div>',
                    unsafe_allow_html=True)
        history = load_history()

        hc1, hc2 = st.columns([4, 1])
        with hc1:
            st.markdown(f"**{len(history)} sessions recorded** — auto-saved after each analysis.")
        with hc2:
            if st.button("🗑️ Clear All", key="clear_hist"):
                clear_all()
                st.success("Cleared.")
                st.rerun()

        if not history:
            st.info("No history yet. Analyses are saved automatically.")
        else:
            for idx, sess in enumerate(history):
                # Use idx in key to guarantee uniqueness even if session_ids collide
                _exp_key = f"hist_exp_{idx}_{sess['session_id']}"
                with st.expander(
                    f"📁 {sess['timestamp']}  ·  {sess['dataset_name']}  ·  "
                    f"{sess['total_rows']:,} rows  ·  Filter: {sess['filter_used']}",
                    expanded=False
                ):
                    hm1, hm2, hm3 = st.columns(3)
                    hm1.metric("Revenue",      fmt_currency(sess["total_revenue"]))
                    hm2.metric("Units Sold",   fmt_number(sess["total_units"]))
                    forecast_unit = {
                        "Weekly": "wk", "Daily": "day", "Monthly": "mo"
                    }.get(sess["forecast_freq"], "period")
                    hm3.metric(
                        "Forecast Avg",
                        f"{sess['forecast_avg']:.0f}/{forecast_unit}",
                    )

                    hm4, hm5, hm6 = st.columns(3)
                    hm4.metric("Best Season", sess["best_season"])
                    hm5.metric("Top Zone",    sess["top_area"])
                    hm6.metric("High-Pri Insights", sess["high_priority_count"])

                    st.markdown(
                        f'<div class="hist-card">'
                        f'📅 {sess["date_range"]} &nbsp;·&nbsp; '
                        f'📦 {sess["num_products"]} products &nbsp;·&nbsp; '
                        f'🌍 {sess["num_areas"]} zones &nbsp;·&nbsp; '
                        f'🔮 {sess["forecast_periods"]} {sess["forecast_freq"].lower()}s ahead &nbsp;·&nbsp; '
                        f'💡 {sess["insights_count"]} insights'
                        f'</div>', unsafe_allow_html=True)

                    # Nested expanders not supported on Streamlit Cloud — use toggle instead
                    show_recs = st.checkbox(
                        "📄 Show recommendations", key=f"show_rec_{idx}_{sess['session_id']}")
                    if show_recs:
                        st.text(sess["insights_text"])

                    if st.button("🗑️ Delete", key=f"del_btn_{idx}_{sess['session_id']}"):
                        delete_session(sess["session_id"])
                        st.rerun()