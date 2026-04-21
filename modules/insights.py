"""
Module: insights.py
Generates actionable business recommendations from analysis results.
"""

import pandas as pd
from dataclasses import dataclass
from typing import List


@dataclass
class Insight:
    category: str
    priority: str
    title: str
    detail: str
    action: str


def _forecast_insights(result: dict) -> List[Insight]:
    insights = []
    history  = result["history"]
    forecast = result["forecast"]
    hist_avg = history[-min(8, len(history)):].mean()
    fore_avg = forecast.mean()
    growth   = (fore_avg - hist_avg) / (hist_avg + 1e-9)

    if growth > 0.05:
        insights.append(Insight("📈 Forecasting","High","Demand surge expected",
            f"Forecast avg ({fore_avg:.0f} units) is {growth*100:.1f}% above recent ({hist_avg:.0f}).",
            "Increase procurement 15–20%. Pre-position stock in top zones."))
    elif growth < -0.05:
        insights.append(Insight("📈 Forecasting","Medium","Slowdown expected",
            f"Forecast avg ({fore_avg:.0f}) is {abs(growth)*100:.1f}% below recent ({hist_avg:.0f}).",
            "Reduce inventory orders. Launch promotions to clear existing stock."))
    else:
        insights.append(Insight("📈 Forecasting","Low","Demand stable",
            f"Forecast tracks recent performance (~{fore_avg:.0f} units).",
            "Maintain stock levels. Optimise warehouse operations."))

    cv = forecast.std() / (forecast.mean() + 1e-9)
    if cv > 0.15:
        insights.append(Insight("📈 Forecasting","Medium","High forecast volatility",
            f"CV = {cv*100:.1f}% — demand is unpredictable.",
            "Keep 20% safety stock buffer. Review supplier lead times."))
    return insights


def _seasonal_insights(seasonal_summary: pd.DataFrame) -> List[Insight]:
    # Use duration-normalised intensity if available
    metric = "Sales_Per_Month" if "Sales_Per_Month" in seasonal_summary.columns else "Total_Sales"
    best  = seasonal_summary.loc[seasonal_summary[metric].idxmax()]
    worst = seasonal_summary.loc[seasonal_summary[metric].idxmin()]

    dur_note = ""
    if "Season_Months" in seasonal_summary.columns:
        bm = int(best["Season_Months"])
        wm = int(worst["Season_Months"])
        dur_note = f" (season lasts {bm} months)"

    return [
        Insight("🌸 Seasonality","High",
            f"{best['Season']} is peak season{dur_note}",
            f"Highest intensity: {best[metric]:,.0f} units/month. "
            f"Raw total: {best['Total_Sales']:,.0f} units.",
            f"Ramp stock 4–6 weeks before {best['Season']}. "
            f"Prioritise Electronics & Fashion bundles for Festive."),
        Insight("🌸 Seasonality","Medium",
            f"{worst['Season']} is slowest season",
            f"Lowest intensity: {worst[metric]:,.0f} units/month.",
            f"Run clearance sales in {worst['Season']}. Offer free shipping + combo deals.")
    ]


def _area_insights(area_summary: pd.DataFrame) -> List[Insight]:
    insights = []
    top    = area_summary.iloc[0]
    bottom = area_summary.iloc[-1]
    gap    = float(top["Revenue_Share_%"]) - float(bottom["Revenue_Share_%"])

    insights.append(Insight("🌍 Area","High",
        f"{top['Area']} is top zone",
        f"Contributes {top['Revenue_Share_%']}% of revenue.",
        f"Increase delivery slots, warehouse space, and ad spend in {top['Area']}."))

    if gap > 10:
        insights.append(Insight("🌍 Area","Medium",
            f"Gap: {top['Area']} vs {bottom['Area']}",
            f"{gap:.1f}% revenue gap.",
            f"Reduce delivery fees in {bottom['Area']}. Investigate stock availability."))

    if "Cluster_Label" in area_summary.columns:
        low = area_summary[area_summary["Cluster_Label"]=="🔴 Low Performer"]["Area"].tolist()
        if low:
            insights.append(Insight("🌍 Area","Medium",
                f"Low-performer clusters: {', '.join(low)}",
                "KMeans flagged these zones across all metrics.",
                "Run zone-specific promotions. Lower delivery fees to stimulate demand."))
    return insights


def _pricing_insights(df: pd.DataFrame, elasticity_map: dict,
                       optimal_map: dict) -> List[Insight]:
    insights = []
    for cat, e_data in elasticity_map.items():
        e   = e_data.get("elasticity")
        opt = optimal_map.get(cat, {})
        if e is None:
            continue
        if e < -1:
            insights.append(Insight("💰 Pricing","High",
                f"{cat} is price-sensitive",
                f"Elasticity = {e:.2f}. 10% cut → ~{abs(e)*10:.0f}% more volume.",
                f"Test 5–10% discount. Optimal range: ₹{opt.get('min_price','?')}–₹{opt.get('max_price','?')}."))
        elif -1 <= e < 0:
            insights.append(Insight("💰 Pricing","Medium",
                f"{cat} is price-insensitive",
                f"Elasticity = {e:.2f}. Demand holds despite price rises.",
                f"Raise {cat} prices 5–8%. Revenue-max price: ₹{opt.get('best_price','?')}."))
    return insights


def _growth_insights(df: pd.DataFrame) -> List[Insight]:
    monthly = (df.groupby(["Year","Month"])["Sales_Quantity"]
                 .sum().reset_index().sort_values(["Year","Month"]))
    if len(monthly) < 3:
        return []
    r = monthly.tail(3)["Sales_Quantity"].values
    g = (r[-1] - r[0]) / (r[0] + 1e-9) * 100
    if g > 10:
        return [Insight("📊 Growth","High",f"+{g:.1f}% 3-month growth",
            "Business is on a positive trajectory.",
            "Scale winning categories. Negotiate better bulk rates.")]
    elif g < -10:
        return [Insight("📊 Growth","High",f"{g:.1f}% 3-month decline",
            "Sales falling — needs attention.",
            "Audit top categories for stock-outs, pricing issues, or delivery failures.")]
    return []


def generate_insights(df, forecast_result, seasonal_summary,
                      area_summary, elasticity_map, optimal_map) -> List[Insight]:
    all_ins = []
    all_ins += _forecast_insights(forecast_result)
    all_ins += _seasonal_insights(seasonal_summary)
    all_ins += _area_insights(area_summary)
    all_ins += _pricing_insights(df, elasticity_map, optimal_map)
    all_ins += _growth_insights(df)
    order = {"High":0,"Medium":1,"Low":2}
    all_ins.sort(key=lambda x: order.get(x.priority, 3))
    print(f"[Insights] {len(all_ins)} recommendations "
          f"({sum(1 for i in all_ins if i.priority=='High')} high).")
    return all_ins


def format_insights_text(insights: List[Insight]) -> str:
    lines = ["="*60, "  SMART SALES RECOMMENDATIONS", "="*60]
    for i, ins in enumerate(insights, 1):
        lines += [f"\n[{i}] {ins.category}  |  {ins.priority} Priority",
                  f"    📌 {ins.title}", f"    {ins.detail}",
                  f"    ✅ {ins.action}"]
    return "\n".join(lines)
