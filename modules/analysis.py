"""
Module: analysis.py
Season-wise analysis based on DURATION-NORMALISED intensity
(sales per month of season) so short seasons aren't penalised.
Includes KMeans area clustering.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from modules.preprocessing import SEASON_ORDER, SEASON_DURATION


def season_analysis(df: pd.DataFrame) -> dict:
    """
    Season-wise analysis with duration-normalised intensity.
    - Total_Sales: raw units sold
    - Season_Months: how long that season is
    - Sales_Per_Month: Total_Sales / Season_Months  ← the key metric
    - Intensity_Rank: ranked by Sales_Per_Month
    This ensures a 2-month Festive season is fairly compared to
    a 4-month Monsoon.
    """
    seasonal = (df.groupby("Season")
                  .agg(Total_Sales=("Sales_Quantity", "sum"),
                       Total_Revenue=("Revenue", "sum"),
                       Avg_Price=("Price", "mean"),
                       Num_Orders=("Sales_Quantity", "count"))
                  .reset_index())

    # Attach duration and compute intensity
    seasonal["Season_Months"]  = seasonal["Season"].map(SEASON_DURATION)
    seasonal["Sales_Per_Month"] = (
        seasonal["Total_Sales"] / seasonal["Season_Months"]
    ).round(0).astype(int)
    seasonal["Rev_Per_Month"]  = (
        seasonal["Total_Revenue"] / seasonal["Season_Months"]
    ).round(0).astype(int)

    # Sort by Indian season order
    seasonal["Season"] = pd.Categorical(
        seasonal["Season"], categories=SEASON_ORDER, ordered=True)
    seasonal.sort_values("Season", inplace=True)
    seasonal.reset_index(drop=True, inplace=True)

    best_intensity  = seasonal.loc[seasonal["Sales_Per_Month"].idxmax(), "Season"]
    worst_intensity = seasonal.loc[seasonal["Sales_Per_Month"].idxmin(), "Season"]
    best_raw        = seasonal.loc[seasonal["Total_Sales"].idxmax(), "Season"]

    # ── Chart 1: Grouped bar — raw sales vs normalised intensity ─────────────
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("Raw Total Sales by Season",
                                        "Duration-Normalised Sales Intensity (per month)"))
    colours = {"Winter":"#60a5fa","Summer":"#f97316","Monsoon":"#34d399","Festive":"#a78bfa"}
    for _, row in seasonal.iterrows():
        c = colours.get(str(row["Season"]), "#94a3b8")
        fig.add_trace(go.Bar(name=str(row["Season"]), x=[str(row["Season"])],
                             y=[row["Total_Sales"]], marker_color=c,
                             showlegend=False), row=1, col=1)
        fig.add_trace(go.Bar(name=str(row["Season"]), x=[str(row["Season"])],
                             y=[row["Sales_Per_Month"]], marker_color=c,
                             showlegend=True), row=1, col=2)
    fig.update_layout(template="plotly_white", title="Season-wise Sales Analysis",
                      legend_title="Season", barmode="group")

    # ── Chart 2: Revenue per month ────────────────────────────────────────────
    rev_fig = px.bar(seasonal, x="Season", y="Rev_Per_Month",
                     color="Season",
                     color_discrete_map=colours,
                     title="Revenue Intensity per Month of Season",
                     text="Season_Months",
                     template="plotly_white")
    rev_fig.update_traces(texttemplate="Duration: %{text} months",
                          textposition="outside")

    # ── Chart 3: Heatmap category × season ───────────────────────────────────
    pivot = (df.groupby(["Category","Season"])["Sales_Quantity"]
               .sum().reset_index()
               .pivot(index="Category", columns="Season", values="Sales_Quantity"))
    pivot = pivot[[s for s in SEASON_ORDER if s in pivot.columns]]
    heatmap_fig = px.imshow(pivot, text_auto=".0f", aspect="auto",
                             color_continuous_scale="YlOrRd",
                             title="Category × Season Heatmap (Raw Sales)")
    heatmap_fig.update_layout(template="plotly_white")

    print(f"[Analysis] Seasonal (normalised):\n"
          f"{seasonal[['Season','Total_Sales','Season_Months','Sales_Per_Month']].to_string(index=False)}")
    print(f"  Highest intensity: {best_intensity} | Lowest: {worst_intensity}")

    return {
        "summary":        seasonal,
        "chart":          fig,
        "rev_chart":      rev_fig,
        "heatmap":        heatmap_fig,
        "best_season":    str(best_intensity),   # by intensity
        "worst_season":   str(worst_intensity),
        "best_raw":       str(best_raw),          # by sheer volume
    }


def area_analysis(df: pd.DataFrame) -> dict:
    """Area performance with KMeans clustering."""
    area_df = (df.groupby("Area")
                 .agg(Total_Sales=("Sales_Quantity","sum"),
                      Total_Revenue=("Revenue","sum"),
                      Avg_Price=("Price","mean"),
                      Num_Transactions=("Sales_Quantity","count"))
                 .reset_index()
                 .sort_values("Total_Revenue", ascending=False)
                 .reset_index(drop=True))

    area_df["Revenue_Share_%"] = (
        area_df["Total_Revenue"] / area_df["Total_Revenue"].sum() * 100).round(1)
    area_df["vs_Top_%"] = (
        (area_df["Total_Revenue"] - area_df["Total_Revenue"].max())
        / area_df["Total_Revenue"].max() * 100).round(1)

    area_df = _cluster_areas(area_df)

    bar_fig = px.bar(
        area_df.sort_values("Total_Revenue"),
        x="Total_Revenue", y="Area", orientation="h",
        color="Cluster_Label",
        color_discrete_map={"🟢 High Performer":"#22c55e","🔴 Low Performer":"#ef4444"},
        title="Area Revenue (KMeans Clustered)", text="Revenue_Share_%",
        template="plotly_white"
    )
    bar_fig.update_traces(texttemplate="%{text}%", textposition="outside")

    zc = df.groupby(["Area","Category"])["Sales_Quantity"].sum().reset_index()
    group_fig = px.bar(zc, x="Area", y="Sales_Quantity", color="Category",
                       barmode="group", title="Area × Category Breakdown",
                       template="plotly_white")

    return {"summary": area_df, "bar_chart": bar_fig, "group_chart": group_fig,
            "top_area": area_df.iloc[0]["Area"]}


def _cluster_areas(area_df: pd.DataFrame, n_clusters: int = 2) -> pd.DataFrame:
    if len(area_df) < 2:
        area_df["Cluster_Label"] = "🟢 Only Zone"
        return area_df
    n = min(n_clusters, len(area_df))
    feats = ["Total_Sales","Total_Revenue","Avg_Price","Num_Transactions"]
    X = StandardScaler().fit_transform(area_df[feats].fillna(0))
    area_df = area_df.copy()
    area_df["Cluster"] = KMeans(n_clusters=n, random_state=42, n_init=10).fit_predict(X)
    high = area_df.groupby("Cluster")["Total_Revenue"].mean().idxmax()
    area_df["Cluster_Label"] = area_df["Cluster"].apply(
        lambda c: "🟢 High Performer" if c == high else "🔴 Low Performer")
    return area_df


def monthly_trend(df: pd.DataFrame) -> go.Figure:
    monthly = (df.groupby(["Year","Month","Category"])["Sales_Quantity"]
                 .sum().reset_index())
    monthly["Period"] = pd.to_datetime(
        monthly["Year"].astype(str)+"-"+monthly["Month"].astype(str).str.zfill(2))
    fig = px.line(monthly.sort_values("Period"), x="Period",
                  y="Sales_Quantity", color="Category", markers=True,
                  title="Monthly Sales Trend by Category", template="plotly_white")
    return fig
