"""
Module: price_optimizer.py
Fixed imports — all from standard packages only (no Pylance issues).
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sklearn.linear_model import LinearRegression  # noqa: F401


def compute_elasticity(df: pd.DataFrame, product: str = None,
                       category: str = None) -> dict:
    if category:
        subset = df[df["Category"] == category][["Price","Sales_Quantity"]].dropna()
        label  = f"Category: {category}"
    else:
        subset = df[df["Product"] == product][["Price","Sales_Quantity"]].dropna()
        label  = f"Product: {product}"

    if len(subset) < 5:
        return {"elasticity": None, "label": label, "note": "Insufficient data"}

    X = np.log(subset["Price"].values + 1e-9).reshape(-1, 1)
    y = np.log(subset["Sales_Quantity"].values + 1e-9)
    model = LinearRegression().fit(X, y)
    e     = round(float(model.coef_[0]), 3)

    interp = ("Elastic — price-sensitive" if e < -1
              else "Inelastic — price-insensitive" if -1 <= e < 0
              else "Positive relationship")

    return {"elasticity": e, "label": label, "interpretation": interp,
            "r_squared": round(float(model.score(X, y)), 3)}


def optimal_price_range(df: pd.DataFrame, product: str = None,
                        category: str = None) -> dict:
    subset  = df[df["Category"] == category] if category else df[df["Product"] == product]
    grouped = (subset.groupby("Price")["Sales_Quantity"]
                     .mean().reset_index()
                     .rename(columns={"Sales_Quantity":"Avg_Sales"}))
    if grouped.empty:
        return {}
    q75 = grouped["Avg_Sales"].quantile(0.75)
    top = grouped[grouped["Avg_Sales"] >= q75]
    return {
        "min_price":      round(float(top["Price"].min()), 2),
        "max_price":      round(float(top["Price"].max()), 2),
        "best_price":     round(float(grouped.loc[grouped["Avg_Sales"].idxmax(),"Price"]), 2),
        "peak_avg_sales": round(float(grouped["Avg_Sales"].max()), 1),
    }


def revenue_optimal_price(df: pd.DataFrame, product: str = None,
                           category: str = None) -> float:
    subset = df[df["Category"] == category] if category else df[df["Product"] == product]
    subset = subset.copy()
    subset["Avg_Rev"] = subset["Price"] * subset["Sales_Quantity"]
    grouped = subset.groupby("Price")["Avg_Rev"].mean()
    return round(float(grouped.idxmax()), 2) if not grouped.empty else None


def plot_price_demand(df: pd.DataFrame, category: str) -> go.Figure:
    subset = df[df["Category"] == category]
    fig = px.scatter(subset, x="Price", y="Sales_Quantity",
                     color="Season", size="Revenue",
                     title=f"Price vs Demand — {category}",
                     labels={"Price":"Sale Price","Sales_Quantity":"Qty Sold"},
                     template="plotly_white", trendline="lowess")
    return fig


def plot_all_categories_elasticity(df: pd.DataFrame) -> go.Figure:
    records = []
    for cat in df["Category"].unique():
        e = compute_elasticity(df, category=cat)
        if e.get("elasticity") is not None:
            records.append({"Category": cat, "Elasticity": e["elasticity"],
                            "Interpretation": e.get("interpretation","")})
    if not records:
        return go.Figure()
    edf    = pd.DataFrame(records)
    colors = ["#ef4444" if e < -1 else "#3b82f6" for e in edf["Elasticity"]]
    fig    = go.Figure(go.Bar(x=edf["Category"], y=edf["Elasticity"],
                              text=edf["Elasticity"], textposition="outside",
                              marker_color=colors))
    n = len(edf)
    fig.update_layout(title="Price Elasticity by Category",
                      xaxis_title="Category", yaxis_title="Elasticity",
                      template="plotly_white",
                      shapes=[dict(type="line", x0=-0.5, x1=n-0.5,
                                   y0=-1, y1=-1,
                                   line=dict(color="orange",dash="dash",width=1.5))])
    return fig
