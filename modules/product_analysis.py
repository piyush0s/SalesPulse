"""
Module: product_analysis.py
Purpose: Deep category-wise and product-wise analysis with full charts.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ─── Category-level analysis ─────────────────────────────────────────────────

def category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Full aggregated stats per category."""
    stats = (df.groupby("Category")
               .agg(Total_Revenue=("Revenue",        "sum"),
                    Total_Units=  ("Sales_Quantity",  "sum"),
                    Avg_Price=    ("Price",            "mean"),
                    Num_Orders=   ("Sales_Quantity",   "count"),
                    Num_Products= ("Product",          "nunique"))
               .reset_index()
               .sort_values("Total_Revenue", ascending=False)
               .reset_index(drop=True))
    stats["Revenue_Share_%"] = (
        stats["Total_Revenue"] / stats["Total_Revenue"].sum() * 100).round(1)
    stats["Avg_Price"] = stats["Avg_Price"].round(2)
    return stats


def category_revenue_chart(cat_df: pd.DataFrame) -> go.Figure:
    """Donut + bar side-by-side for category revenue share."""
    fig = make_subplots(rows=1, cols=2,
                        specs=[[{"type":"domain"}, {"type":"xy"}]],
                        subplot_titles=("Revenue Share", "Units Sold by Category"))

    fig.add_trace(go.Pie(
        labels=cat_df["Category"], values=cat_df["Total_Revenue"],
        hole=0.45, textinfo="label+percent",
        marker=dict(colors=px.colors.qualitative.Set2)
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=cat_df["Category"], y=cat_df["Total_Units"],
        marker_color=px.colors.qualitative.Set2[:len(cat_df)],
        text=cat_df["Total_Units"].apply(
            lambda x: f"{x/1000:.1f}K" if x >= 1000 else str(x)),
        textposition="outside"
    ), row=1, col=2)

    fig.update_layout(title="Category Performance Overview",
                      template="plotly_white", showlegend=False,
                      height=420)
    return fig


def category_monthly_trend(df: pd.DataFrame) -> go.Figure:
    """Monthly revenue trend split by category."""
    monthly = (df.groupby([pd.Grouper(key="Date", freq="ME"), "Category"])
                 ["Revenue"].sum().reset_index())
    fig = px.area(monthly, x="Date", y="Revenue", color="Category",
                  title="Monthly Revenue Trend by Category",
                  template="plotly_white",
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(hovermode="x unified", legend_title="Category")
    return fig


def category_avg_price_chart(cat_df: pd.DataFrame) -> go.Figure:
    """Average selling price per category."""
    fig = px.bar(cat_df.sort_values("Avg_Price"),
                 x="Avg_Price", y="Category", orientation="h",
                 color="Category", text="Avg_Price",
                 title="Average Selling Price by Category",
                 template="plotly_white",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_traces(texttemplate="₹%{text:.2f}", textposition="outside")
    fig.update_layout(showlegend=False)
    return fig


def category_season_heatmap(df: pd.DataFrame) -> go.Figure:
    """Revenue heatmap: category × season."""
    from modules.preprocessing import SEASON_ORDER
    pivot = (df.groupby(["Category", "Season"])["Revenue"]
               .sum().reset_index()
               .pivot(index="Category", columns="Season", values="Revenue"))
    pivot = pivot[[s for s in SEASON_ORDER if s in pivot.columns]]
    pivot_k = (pivot / 1000).round(0)   # display in thousands

    fig = px.imshow(pivot_k, text_auto=".0f", aspect="auto",
                    color_continuous_scale="YlOrRd",
                    title="Category × Season Revenue Heatmap (₹ Thousands)")
    fig.update_layout(template="plotly_white")
    return fig


# ─── Product-level analysis ───────────────────────────────────────────────────

def product_summary(df: pd.DataFrame, category: str = None,
                    top_n: int = 15) -> pd.DataFrame:
    """Top N products by revenue, optionally filtered by category."""
    subset = df[df["Category"] == category] if category else df
    stats  = (subset.groupby(["Category", "Product"])
                    .agg(Total_Revenue=("Revenue",       "sum"),
                         Total_Units=  ("Sales_Quantity", "sum"),
                         Avg_Price=    ("Price",          "mean"),
                         Num_Orders=   ("Sales_Quantity", "count"))
                    .reset_index()
                    .sort_values("Total_Revenue", ascending=False)
                    .head(top_n)
                    .reset_index(drop=True))
    stats["Avg_Price"] = stats["Avg_Price"].round(2)
    stats["Revenue_Share_%"] = (
        stats["Total_Revenue"] / df["Revenue"].sum() * 100).round(2)
    return stats


def top_products_chart(prod_df: pd.DataFrame, title: str = "Top Products by Revenue") -> go.Figure:
    """Horizontal bar chart for top products."""
    # Truncate long product names
    prod_df = prod_df.copy()
    prod_df["Short_Name"] = prod_df["Product"].str[:40] + "…"

    fig = px.bar(prod_df.sort_values("Total_Revenue"),
                 x="Total_Revenue", y="Short_Name",
                 orientation="h", color="Category",
                 text="Total_Units",
                 title=title,
                 template="plotly_white",
                 color_discrete_sequence=px.colors.qualitative.Set2,
                 labels={"Total_Revenue":"Revenue","Short_Name":"Product"})
    fig.update_traces(texttemplate="%{text:,} units", textposition="outside")
    fig.update_layout(height=max(400, len(prod_df) * 32),
                      showlegend=True, legend_title="Category",
                      yaxis=dict(tickfont=dict(size=11)))
    return fig


def product_units_chart(prod_df: pd.DataFrame) -> go.Figure:
    """Scatter: revenue vs units for each product, sized by avg price."""
    prod_df = prod_df.copy()
    prod_df["Short"] = prod_df["Product"].str[:30] + "…"
    fig = px.scatter(prod_df, x="Total_Units", y="Total_Revenue",
                     size="Avg_Price", color="Category",
                     hover_name="Product",
                     text="Short",
                     title="Revenue vs Units Sold (bubble size = avg price)",
                     template="plotly_white",
                     color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_traces(textposition="top center", textfont=dict(size=9))
    fig.update_layout(height=500)
    return fig


def product_monthly_trend(df: pd.DataFrame, product: str) -> go.Figure:
    """Monthly sales trend for a single product."""
    subset = df[df["Product"] == product].copy()
    monthly = (subset.groupby(pd.Grouper(key="Date", freq="ME"))["Sales_Quantity"]
                     .sum().reset_index())
    fig = px.bar(monthly, x="Date", y="Sales_Quantity",
                 title=f"Monthly Sales — {product[:50]}",
                 template="plotly_white",
                 color_discrete_sequence=["#3B82F6"])
    fig.update_layout(xaxis_title="Month", yaxis_title="Units Sold")
    return fig


def product_price_distribution(df: pd.DataFrame, category: str) -> go.Figure:
    """Box plot of price distribution per product in a category."""
    subset = df[df["Category"] == category].copy()
    subset["Short"] = subset["Product"].str[:35] + "…"
    fig = px.box(subset, x="Short", y="Price",
                 title=f"Price Distribution — {category}",
                 template="plotly_white",
                 color="Short",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(showlegend=False, xaxis_tickangle=-30,
                      xaxis_title="Product", yaxis_title="Price (₹)")
    return fig


def category_vs_zone_chart(df: pd.DataFrame) -> go.Figure:
    """Stacked bar: revenue per zone broken down by category."""
    grp = (df.groupby(["Area", "Category"])["Revenue"]
             .sum().reset_index())
    fig = px.bar(grp, x="Area", y="Revenue", color="Category",
                 barmode="stack",
                 title="Revenue by Zone and Category",
                 template="plotly_white",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(legend_title="Category",
                      yaxis_title="Revenue (₹)")
    return fig
