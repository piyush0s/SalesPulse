"""Shared formatting utilities for SalesPulse."""

import pandas as pd

PRIORITY_COLORS = {"High":"#EF4444","Medium":"#F59E0B","Low":"#10B981"}
PRIORITY_EMOJIS = {"High":"🔴","Medium":"🟡","Low":"🟢"}


def fmt_currency(value: float, symbol: str = "₹") -> str:
    return f"{symbol}{value:,.0f}"


def fmt_number(value: float) -> str:
    if value >= 1_000_000: return f"{value/1_000_000:.1f}M"
    if value >= 1_000:     return f"{value/1_000:.1f}K"
    return str(int(value))


def summary_kpis(df: pd.DataFrame) -> dict:
    return {
        "Total Revenue":    fmt_currency(df["Revenue"].sum()),
        "Units Sold":       fmt_number(df["Sales_Quantity"].sum()),
        "Avg Weekly Sales": fmt_number(
            df.groupby(pd.Grouper(key="Date",freq="W"))["Sales_Quantity"].sum().mean()),
        "Products":         str(df["Product"].nunique()),
        (df["Area_Level"].iloc[0] if "Area_Level" in df.columns else "Areas"):
            str(df["Area"].nunique()),
        "Date Range":       f"{df['Date'].min().date()} → {df['Date'].max().date()}",
    }


def dataset_signal_metrics(df: pd.DataFrame) -> tuple[dict, dict]:
    """Summarize optional customer-trust and commercial signals when present."""
    def numeric_values(column: str) -> pd.Series:
        values = df[column].astype(str).str.replace(
            r"[^0-9.\-]", "", regex=True)
        return pd.to_numeric(values, errors="coerce").dropna()

    customer = {}
    for column, label, suffix in [
        ("Customer_Satisfaction", "Avg customer satisfaction", ""),
        ("Rating", "Avg product rating", ""),
        ("Return_Rate_Percent", "Avg return rate", "%"),
        ("Delivery_Days", "Avg delivery time", " days"),
        ("Reviews_Count", "Avg reviews / row", ""),
    ]:
        if column in df.columns:
            values = numeric_values(column)
            if not values.empty:
                customer[label] = f"{values.mean():,.1f}{suffix}"

    if "Repeat_Customer" in df.columns:
        values = df["Repeat_Customer"].dropna()
        numeric = pd.to_numeric(values, errors="coerce")
        if numeric.notna().any():
            customer["Repeat customer share"] = (
                f"{numeric.dropna().gt(0).mean() * 100:.1f}%")
        else:
            truthy = {"yes", "true", "1", "repeat", "returning"}
            normalized = values.astype(str).str.strip().str.lower()
            customer["Repeat customer share"] = (
                f"{normalized.isin(truthy).mean() * 100:.1f}%")

    business = {}
    for column, label, suffix in [
        ("Discount_Percent", "Avg discount", "%"),
        ("Profit_Margin_Percent", "Avg profit margin", "%"),
        ("Conversion_Rate_Percent", "Avg conversion rate", "%"),
        ("Stock_Available", "Avg stock available", ""),
        ("Website_Visits", "Avg website visits / row", ""),
        ("Cart_Additions", "Avg cart additions / row", ""),
        ("Ad_Spend", "Avg ad spend / row", ""),
        ("Competitor_Price", "Avg competitor price", ""),
    ]:
        if column in df.columns:
            values = numeric_values(column)
            if not values.empty:
                value = values.mean()
                if column in {"Ad_Spend", "Competitor_Price"}:
                    business[label] = f"₹{value:,.1f}"
                else:
                    business[label] = f"{value:,.1f}{suffix}"

    if "Demand_Level" in df.columns:
        levels = df["Demand_Level"].dropna().astype(str).str.strip()
        if not levels.empty:
            business["Demand levels tracked"] = str(levels.nunique())

    return customer, business
