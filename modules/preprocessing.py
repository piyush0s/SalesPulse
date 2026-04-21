"""
Module: preprocessing.py
Purpose: Load, clean, and engineer features from any sales CSV/XLSX.
Supports dynamic column detection + validation with user-friendly error messages.
"""

import pandas as pd
import numpy as np

# ─── Indian Season Map ───────────────────────────────────────────────────────
SEASON_MAP = {
    12: "Winter",  1: "Winter",   2: "Winter",
     3: "Summer",  4: "Summer",   5: "Summer",
     6: "Monsoon", 7: "Monsoon",  8: "Monsoon", 9: "Monsoon",
    10: "Festive", 11: "Festive"
}

# Season duration in months (used for normalised intensity calculation)
SEASON_DURATION = {"Winter": 3, "Summer": 3, "Monsoon": 4, "Festive": 2}
SEASON_ORDER    = ["Winter", "Summer", "Monsoon", "Festive"]

# ─── Column aliases ──────────────────────────────────────────────────────────
# Maps common variant names → standard internal name
COLUMN_ALIASES = {
    "Date":           ["date", "orderdate", "order_date", "order date",
                       "sale_date", "saledate", "transaction_date"],
    "Sales_Quantity": ["order quantity", "order_quantity", "qty", "quantity",
                       "sales_quantity", "sales quantity", "units_sold",
                       "units sold", "amount"],
    "Price":          ["sale price", "sale_price", "price", "selling_price",
                       "unit_price", "unitprice", "revenue_per_unit"],
    "Product":        ["product", "item", "product_name", "item_name",
                       "product name", "sku", "description"],
    "Area":           ["zone", "area", "region", "location", "city",
                       "state", "territory"],
    "Category":       ["product category", "product_category", "category",
                       "subcategory", "department", "type"],
}


def _detect_columns(df: pd.DataFrame) -> dict:
    """
    Try to map actual DataFrame columns to standard names using aliases.
    Returns dict of {standard_name: actual_col} for found columns.
    """
    found = {}
    lower_cols = {c.lower().strip(): c for c in df.columns}
    for std_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_cols:
                found[std_name] = lower_cols[alias]
                break
    return found


def validate_dataframe(df: pd.DataFrame) -> tuple[bool, list]:
    """
    Validate uploaded data. Returns (is_valid, list_of_errors).
    Errors are human-readable strings shown as pop-out notifications.
    """
    errors = []
    col_map = _detect_columns(df)
    required = ["Date", "Sales_Quantity", "Price"]

    # Check required columns are findable
    for col in required:
        if col not in col_map:
            errors.append(
                f"❌ Required column '{col}' not found.\n"
                f"   Expected one of: {COLUMN_ALIASES[col][:4]}\n"
                f"   Found columns: {list(df.columns)[:8]}"
            )

    if errors:
        return False, errors

    # Peek at data types
    date_col = col_map["Date"]
    qty_col  = col_map["Sales_Quantity"]
    price_col = col_map["Price"]

    try:
        pd.to_datetime(df[date_col].dropna().head(5))
    except Exception:
        errors.append(f"❌ Column '{date_col}' cannot be parsed as dates. "
                      f"Sample values: {df[date_col].head(3).tolist()}")

    try:
        pd.to_numeric(df[qty_col].dropna().head(5))
    except Exception:
        errors.append(f"❌ Column '{qty_col}' contains non-numeric values. "
                      f"Sample: {df[qty_col].head(3).tolist()}")

    try:
        pd.to_numeric(df[price_col].dropna().head(5))
    except Exception:
        errors.append(f"❌ Column '{price_col}' contains non-numeric values. "
                      f"Sample: {df[price_col].head(3).tolist()}")

    if len(df) < 10:
        errors.append(f"❌ Dataset too small ({len(df)} rows). "
                      "Need at least 10 rows for meaningful analysis.")

    return len(errors) == 0, errors


def load_and_clean(filepath: str) -> pd.DataFrame:
    """
    Load any sales CSV/XLSX, auto-detect columns, engineer features.
    """
    if filepath.endswith(".xlsx") or filepath.endswith(".xls"):
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath)

    # Auto-detect and rename columns
    col_map = _detect_columns(df)
    rename = {v: k for k, v in col_map.items() if v != k}
    df.rename(columns=rename, inplace=True)

    # Specific Flipkart renames that aren't covered by aliases
    explicit = {
        "OrderDate": "Date", "Order Quantity": "Sales_Quantity",
        "Sale Price": "Price", "Zone": "Area",
        "Product Category": "Category", "Unit Price": "Unit_Price",
        "Shipping Fee": "Shipping_Fee",
    }
    df.rename(columns={k: v for k, v in explicit.items() if k in df.columns},
              inplace=True)

    required = {"Date", "Sales_Quantity", "Price"}
    missing  = required - set(df.columns)
    if missing:
        raise ValueError(f"Cannot find required columns: {missing}")

    # Add Product column if missing
    if "Product" not in df.columns:
        if "Category" in df.columns:
            df["Product"] = df["Category"]
        else:
            df["Product"] = "All Products"

    # Add Area if missing
    if "Area" not in df.columns:
        df["Area"] = "Default"

    # Add Category if missing
    if "Category" not in df.columns:
        df["Category"] = df["Product"]

    df["Date"]           = pd.to_datetime(df["Date"])
    df["Sales_Quantity"] = pd.to_numeric(df["Sales_Quantity"], errors="coerce")
    df["Price"]          = pd.to_numeric(df["Price"], errors="coerce")

    df.sort_values("Date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    before = len(df)
    df.dropna(subset=["Date", "Sales_Quantity", "Price"], inplace=True)
    df = df[(df["Sales_Quantity"] > 0) & (df["Price"] > 0)]
    dropped = before - len(df)
    if dropped:
        print(f"[Preprocessing] Dropped {dropped} invalid rows.")

    for col in ["Product", "Area", "Category"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    df["Year"]      = df["Date"].dt.year
    df["Month"]     = df["Date"].dt.month
    df["Week"]      = df["Date"].dt.isocalendar().week.astype(int)
    df["Season"]    = df["Month"].map(SEASON_MAP)
    df["Revenue"]   = df["Sales_Quantity"] * df["Price"]
    df["WeekLabel"] = df["Date"].dt.to_period("W").astype(str)
    df["Quarter"]   = df["Date"].dt.quarter.map(
        {1: "Q1 (Jan-Mar)", 2: "Q2 (Apr-Jun)",
         3: "Q3 (Jul-Sep)", 4: "Q4 (Oct-Dec)"}
    )

    print(f"[Preprocessing] ✅ {len(df):,} rows | "
          f"{df['Product'].nunique()} products | "
          f"{df['Area'].nunique()} areas | "
          f"{df['Date'].min().date()} → {df['Date'].max().date()}")
    return df


def get_weekly_series(df: pd.DataFrame, product=None, category=None) -> pd.Series:
    subset = df.copy()
    if product:   subset = subset[subset["Product"]  == product]
    if category:  subset = subset[subset["Category"] == category]
    return (subset.groupby(pd.Grouper(key="Date", freq="W"))["Sales_Quantity"]
            .sum().rename("Sales_Quantity").asfreq("W").ffill())


def get_daily_series(df: pd.DataFrame, product=None, category=None) -> pd.Series:
    subset = df.copy()
    if product:   subset = subset[subset["Product"]  == product]
    if category:  subset = subset[subset["Category"] == category]
    return (subset.groupby("Date")["Sales_Quantity"]
            .sum().asfreq("D").ffill())
