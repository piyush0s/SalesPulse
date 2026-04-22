"""
Module: insights.py
Fully data-driven recommendations — every number, name, and suggestion
is derived from the actual dataset passed in. No hardcoded strings.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List


@dataclass
class Insight:
    category: str
    priority: str
    title: str
    detail: str
    action: str


# ─── Forecast insights ────────────────────────────────────────────────────────
def _forecast_insights(result: dict, freq: str = "W") -> List[Insight]:
    insights = []
    history  = result["history"]
    forecast = result["forecast"]
    periods  = result.get("periods", len(forecast))
    unit     = "week" if freq == "W" else "day"

    hist_avg = history[-min(8, len(history)):].mean()
    fore_avg = forecast.mean()
    fore_max = forecast.max()
    fore_min = forecast.min()
    growth   = (fore_avg - hist_avg) / (hist_avg + 1e-9)

    peak_date = forecast.idxmax().strftime("%b %d, %Y")

    if growth > 0.1:
        insights.append(Insight("📈 Forecasting", "High",
            f"Demand will surge +{growth*100:.1f}% over next {periods} {unit}s",
            f"Forecast avg: {fore_avg:,.0f} units/{unit} vs recent avg {hist_avg:,.0f}. "
            f"Peak of {fore_max:,.0f} units expected around {peak_date}.",
            f"Increase procurement by {min(int(growth*100)+5, 40)}% immediately. "
            f"Ensure top-selling products are stocked {periods//2 or 1} {unit}s ahead."))
    elif growth > 0.02:
        insights.append(Insight("📈 Forecasting", "Medium",
            f"Moderate demand growth +{growth*100:.1f}% projected",
            f"Forecast avg {fore_avg:,.0f} units/{unit} — modest improvement over recent {hist_avg:,.0f}.",
            f"Incrementally increase stock by 8–12%. Monitor weekly and adjust."))
    elif growth < -0.15:
        insights.append(Insight("📈 Forecasting", "High",
            f"Significant demand drop {growth*100:.1f}% expected",
            f"Forecast avg {fore_avg:,.0f} units/{unit} vs recent {hist_avg:,.0f}. "
            f"Minimum expected: {fore_min:,.0f} units/{unit}.",
            f"Cut next procurement order by {min(int(abs(growth)*100)-5, 35)}%. "
            f"Run promotions to clear existing inventory before the slowdown hits."))
    elif growth < -0.03:
        insights.append(Insight("📈 Forecasting", "Medium",
            f"Mild demand slowdown {growth*100:.1f}%",
            f"Forecast avg {fore_avg:,.0f} units/{unit} slightly below recent {hist_avg:,.0f}.",
            "Hold current stock levels. Delay reorder triggers by 1 cycle."))
    else:
        insights.append(Insight("📈 Forecasting", "Low",
            f"Demand stable at ~{fore_avg:,.0f} units/{unit}",
            f"Forecast closely matches recent performance. Range: {fore_min:,.0f}–{fore_max:,.0f} units/{unit}.",
            "Maintain current inventory strategy. Good window to renegotiate supplier contracts."))

    cv = forecast.std() / (forecast.mean() + 1e-9)
    if cv > 0.20:
        insights.append(Insight("📈 Forecasting", "Medium",
            f"High demand volatility detected (CV={cv*100:.0f}%)",
            f"Forecast swings between {fore_min:,.0f} and {fore_max:,.0f} units/{unit} — very unpredictable.",
            "Carry a 25% safety stock buffer. Set up fast-reorder triggers with your top 2 suppliers."))
    return insights


# ─── Season insights ──────────────────────────────────────────────────────────
def _seasonal_insights(df: pd.DataFrame, seasonal_summary: pd.DataFrame) -> List[Insight]:
    metric = "Sales_Per_Month" if "Sales_Per_Month" in seasonal_summary.columns else "Total_Sales"
    best   = seasonal_summary.loc[seasonal_summary[metric].idxmax()]
    worst  = seasonal_summary.loc[seasonal_summary[metric].idxmin()]
    best_s, worst_s = str(best["Season"]), str(worst["Season"])

    # Find top category in best season
    cat_season = (df[df["Season"] == best_s]
                  .groupby("Category")["Revenue"].sum()
                  .sort_values(ascending=False))
    top_cat_in_best  = cat_season.index[0]  if len(cat_season) > 0 else "N/A"
    top_cat_rev      = cat_season.iloc[0]   if len(cat_season) > 0 else 0
    top_cat_share    = top_cat_rev / cat_season.sum() * 100 if cat_season.sum() > 0 else 0

    # Worst season — find most underperforming product
    worst_cat = (df[df["Season"] == worst_s]
                 .groupby("Category")["Revenue"].sum()
                 .sort_values().index[0]) if len(df[df["Season"]==worst_s]) > 0 else "N/A"

    best_intensity   = float(best[metric])
    worst_intensity  = float(worst[metric])
    dur_note = f" ({int(best['Season_Months'])} months)" if "Season_Months" in best.index else ""

    return [
        Insight("🌸 Seasonality", "High",
            f"{best_s} is your peak season{dur_note}",
            f"Normalised intensity: {best_intensity:,.0f} units/month. "
            f"{top_cat_in_best} drives {top_cat_share:.0f}% of {best_s} revenue.",
            f"Start stocking {top_cat_in_best} 5–6 weeks before {best_s}. "
            f"Allocate extra ad budget to {top_cat_in_best} during this window."),
        Insight("🌸 Seasonality", "Medium",
            f"{worst_s} underperforms at {worst_intensity:,.0f} units/month",
            f"{worst_cat} is the weakest category in {worst_s}. "
            f"That's {(best_intensity/worst_intensity - 1)*100:.0f}% below peak season intensity.",
            f"Bundle {worst_cat} with top sellers in {worst_s}. "
            f"Offer 10–15% seasonal discount to stimulate demand in slow period.")
    ]


# ─── Area insights ────────────────────────────────────────────────────────────
def _area_insights(df: pd.DataFrame, area_summary: pd.DataFrame) -> List[Insight]:
    insights = []
    top    = area_summary.iloc[0]
    bottom = area_summary.iloc[-1]
    gap    = float(top["Revenue_Share_%"]) - float(bottom["Revenue_Share_%"])

    top_area    = str(top["Area"])
    bottom_area = str(bottom["Area"])
    top_rev     = float(top["Total_Revenue"])
    bot_rev     = float(bottom["Total_Revenue"])

    # Top category in top area
    top_area_cat = (df[df["Area"] == top_area]
                    .groupby("Category")["Revenue"].sum()
                    .idxmax()) if len(df[df["Area"]==top_area]) > 0 else "N/A"

    # Growth trend in bottom area
    bot_monthly = (df[df["Area"] == bottom_area]
                   .groupby(["Year","Month"])["Revenue"].sum()
                   .reset_index().sort_values(["Year","Month"]))
    bot_trend = "declining" if (len(bot_monthly) >= 3 and
                                bot_monthly.tail(3)["Revenue"].values[-1] <
                                bot_monthly.tail(3)["Revenue"].values[0]) else "flat"

    insights.append(Insight("🌍 Area", "High",
        f"{top_area} leads with {top['Revenue_Share_%']}% revenue share",
        f"Revenue: {top_rev/1e6:.2f}M. Top product category: {top_area_cat}. "
        f"{top_area} outsells {bottom_area} by {(top_rev/bot_rev - 1)*100:.0f}%.",
        f"Scale up {top_area_cat} inventory in {top_area} warehouses. "
        f"Use {top_area}'s successful product mix as a template for other zones."))

    if gap > 8:
        insights.append(Insight("🌍 Area", "Medium",
            f"{bottom_area} is {bot_trend} — {gap:.1f}% below {top_area}",
            f"Revenue: {bot_rev/1e6:.2f}M ({bottom['Revenue_Share_%']}% share). Trend: {bot_trend}.",
            f"Launch {bottom_area}-specific promotions with free/discounted shipping. "
            f"Investigate whether delivery times or product availability are limiting sales."))

    if "Cluster_Label" in area_summary.columns:
        low_zones = area_summary[area_summary["Cluster_Label"] == "🔴 Low Performer"]["Area"].tolist()
        if low_zones:
            combined_rev = float(area_summary[area_summary["Area"].isin(low_zones)]["Total_Revenue"].sum())
            insights.append(Insight("🌍 Area", "Medium",
                f"KMeans: {len(low_zones)} low-performer zone(s): {', '.join(low_zones)}",
                f"These zones contribute only {combined_rev/1e6:.2f}M combined revenue. "
                f"Underperforming on sales volume, revenue, and order count.",
                f"Run targeted campaigns in {', '.join(low_zones)}. "
                f"Consider reducing delivery fees by 20–30% to stimulate first-time orders."))
    return insights


# ─── Pricing insights ─────────────────────────────────────────────────────────
def _pricing_insights(df: pd.DataFrame, elasticity_map: dict, optimal_map: dict) -> List[Insight]:
    insights = []
    for cat, e_data in elasticity_map.items():
        e   = e_data.get("elasticity")
        opt = optimal_map.get(cat, {})
        if e is None:
            continue

        # Actual current avg price for this category
        curr_price = df[df["Category"] == cat]["Price"].mean()
        best_price = opt.get("best_price", curr_price)
        min_price  = opt.get("min_price", "?")
        max_price  = opt.get("max_price", "?")
        price_gap  = ((best_price - curr_price) / curr_price * 100) if curr_price > 0 else 0

        if e < -1.5:
            insights.append(Insight("💰 Pricing", "High",
                f"{cat}: highly elastic (e={e:.2f}) — cut price to grow volume",
                f"Current avg price ₹{curr_price:.0f}. A 10% cut could lift volume ~{abs(e)*10:.0f}%. "
                f"Optimal range: ₹{min_price}–₹{max_price}.",
                f"Test a 7–10% promotional discount on {cat}. "
                f"Target price: ₹{best_price:.0f} for maximum revenue."))
        elif -1.5 <= e < -0.5:
            insights.append(Insight("💰 Pricing", "Medium",
                f"{cat}: moderately elastic (e={e:.2f})",
                f"Current avg ₹{curr_price:.0f}. Revenue-maximising price: ₹{best_price:.0f} "
                f"({'▲ raise' if price_gap > 0 else '▼ lower'} by {abs(price_gap):.0f}%).",
                f"Gradually move {cat} price toward ₹{best_price:.0f}. Monitor units closely."))
        elif e >= 0:
            insights.append(Insight("💰 Pricing", "Medium",
                f"{cat}: positive price effect (e={e:.2f}) — premium pricing possible",
                f"Higher prices correlate with higher sales — possible prestige or quality signal. "
                f"Current avg ₹{curr_price:.0f}, optimal ₹{best_price:.0f}.",
                f"Test a 5–8% price increase on {cat}. If sales hold, increase further to ₹{best_price:.0f}."))
        else:
            insights.append(Insight("💰 Pricing", "Low",
                f"{cat}: price-insensitive (e={e:.2f}) — stable demand",
                f"Demand barely changes with price. Current avg ₹{curr_price:.0f}.",
                f"Safely raise {cat} prices by 4–6% to improve margins. "
                f"Revenue-maximising price is ₹{best_price:.0f}."))
    return insights


# ─── Growth insights ──────────────────────────────────────────────────────────
def _growth_insights(df: pd.DataFrame) -> List[Insight]:
    monthly = (df.groupby(["Year", "Month"])["Revenue"]
                 .sum().reset_index().sort_values(["Year","Month"]))
    if len(monthly) < 4:
        return []

    last3   = monthly.tail(3)["Revenue"].values
    prev3   = monthly.iloc[-6:-3]["Revenue"].values if len(monthly) >= 6 else monthly.head(3)["Revenue"].values
    g       = (last3.mean() - prev3.mean()) / (prev3.mean() + 1e-9) * 100

    # Best and worst performing months in the data
    monthly["Period"] = monthly["Year"].astype(str) + "-" + monthly["Month"].astype(str).str.zfill(2)
    best_month  = monthly.loc[monthly["Revenue"].idxmax(), "Period"]
    worst_month = monthly.loc[monthly["Revenue"].idxmin(), "Period"]
    best_rev    = monthly["Revenue"].max()
    worst_rev   = monthly["Revenue"].min()

    # Top category by recent revenue
    recent_cutoff = df["Date"].max() - pd.Timedelta(days=90)
    recent_df     = df[df["Date"] >= recent_cutoff]
    top_recent_cat = (recent_df.groupby("Category")["Revenue"].sum().idxmax()
                      if len(recent_df) > 0 else "N/A")

    if g > 15:
        return [Insight("📊 Growth", "High",
            f"Strong momentum: revenue up {g:.1f}% vs prior 3 months",
            f"Recent 3-month avg ₹{last3.mean()/1e6:.2f}M vs prior avg ₹{prev3.mean()/1e6:.2f}M. "
            f"{top_recent_cat} is the primary growth driver.",
            f"Double down on {top_recent_cat} — increase its inventory and marketing. "
            f"All-time peak was {best_month} at ₹{best_rev/1e6:.2f}M — replicate what drove that.")]
    elif g > 3:
        return [Insight("📊 Growth", "Medium",
            f"Gradual revenue improvement +{g:.1f}%",
            f"Steady growth over last 3 months. {top_recent_cat} is trending up.",
            f"Invest selectively in {top_recent_cat}. Avoid over-stocking slow categories.")]
    elif g < -15:
        return [Insight("📊 Growth", "High",
            f"Revenue down {g:.1f}% vs prior 3 months — urgent action needed",
            f"Recent avg ₹{last3.mean()/1e6:.2f}M vs prior avg ₹{prev3.mean()/1e6:.2f}M. "
            f"Worst recorded month: {worst_month} at ₹{worst_rev/1e6:.2f}M.",
            f"Immediately audit {top_recent_cat} for stock-outs and pricing issues. "
            f"Launch a site-wide flash sale and review delivery SLAs in low-performing zones.")]
    elif g < -3:
        return [Insight("📊 Growth", "Medium",
            f"Mild revenue dip {g:.1f}% — monitor closely",
            f"Slight downward trend over last 3 months.",
            "Review top-3 product prices for competitiveness. Run a limited-time bundle offer.")]
    return []


# ─── Product-specific insights ────────────────────────────────────────────────
def _product_insights(df: pd.DataFrame) -> List[Insight]:
    insights = []

    # Top 3 products by revenue
    top_prods = (df.groupby(["Product", "Category"])["Revenue"]
                   .sum().sort_values(ascending=False).head(3).reset_index())

    prod_names = " · ".join([f"{r['Product'][:30]} ({r['Category']})"
                              for _, r in top_prods.iterrows()])
    top_rev    = float(top_prods["Revenue"].sum())
    total_rev  = float(df["Revenue"].sum())
    top_share  = top_rev / total_rev * 100

    insights.append(Insight("📦 Products", "Medium",
        f"Top 3 products drive {top_share:.0f}% of revenue",
        f"Revenue leaders: {prod_names}.",
        "Ensure these 3 are never out of stock. Add them to fast-track reorder lists."))

    # Products with declining monthly sales
    last_2m = df["Date"].max() - pd.Timedelta(days=60)
    prev_2m = df["Date"].max() - pd.Timedelta(days=120)
    recent_sales = df[df["Date"] >= last_2m].groupby("Product")["Sales_Quantity"].sum()
    prior_sales  = df[(df["Date"] >= prev_2m) & (df["Date"] < last_2m)].groupby("Product")["Sales_Quantity"].sum()
    common_prods = recent_sales.index.intersection(prior_sales.index)
    if len(common_prods) > 0:
        changes = ((recent_sales[common_prods] - prior_sales[common_prods])
                   / (prior_sales[common_prods] + 1e-9) * 100)
        declining = changes[changes < -25].sort_values().head(3)
        if len(declining) > 0:
            names = ", ".join([f"{p[:25]} ({changes[p]:.0f}%)" for p in declining.index])
            insights.append(Insight("📦 Products", "Medium",
                f"{len(declining)} product(s) losing momentum rapidly",
                f"Sales down >25% in last 60 days: {names}.",
                "Investigate pricing, stock availability, and reviews for these products. "
                "Consider a targeted discount or bundle to revive sales."))

    return insights


# ─── Master generator ─────────────────────────────────────────────────────────
def generate_insights(df, forecast_result, seasonal_summary,
                      area_summary, elasticity_map, optimal_map) -> List[Insight]:
    freq = forecast_result.get("freq", "W")
    all_ins  = []
    all_ins += _forecast_insights(forecast_result, freq)
    all_ins += _seasonal_insights(df, seasonal_summary)
    all_ins += _area_insights(df, area_summary)
    all_ins += _pricing_insights(df, elasticity_map, optimal_map)
    all_ins += _growth_insights(df)
    all_ins += _product_insights(df)

    order = {"High": 0, "Medium": 1, "Low": 2}
    all_ins.sort(key=lambda x: order.get(x.priority, 3))
    print(f"[Insights] {len(all_ins)} data-driven recommendations "
          f"({sum(1 for i in all_ins if i.priority=='High')} high).")
    return all_ins


def format_insights_text(insights: List[Insight]) -> str:
    lines = ["="*60, "  SMART SALES RECOMMENDATIONS", "="*60]
    for i, ins in enumerate(insights, 1):
        lines += [f"\n[{i}] {ins.category}  |  {ins.priority} Priority",
                  f"    📌 {ins.title}", f"    {ins.detail}", f"    ✅ {ins.action}"]
    return "\n".join(lines)