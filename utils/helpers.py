"""Utils: helpers.py — shared formatting utilities."""

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
        "Regions/Zones":    str(df["Area"].nunique()),
        "Date Range":       f"{df['Date'].min().date()} → {df['Date'].max().date()}",
    }
