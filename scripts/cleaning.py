# -*- coding: utf-8 -*-
"""
cleaning.py - Data Cleaning Layer
Handles missing values, deduplication, type coercion, outlier capping,
and category normalization. Saves cleaned data to data/processed/ as Parquet.
"""

import os
import numpy as np
import pandas as pd
from dateutil import parser as date_parser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# Generic Cleaning Utilities
# ─────────────────────────────────────────────

def load_csv(name: str) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, f"{name}.csv")
    df = pd.read_csv(path, low_memory=False)
    print(f"  Loaded {name}.csv — {len(df):,} rows, {df.isnull().sum().sum()} NaNs")
    return df


def remove_duplicates(df: pd.DataFrame, subset: list = None) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=subset)
    removed = before - len(df)
    if removed:
        print(f"    Removed {removed:,} duplicate rows")
    return df.reset_index(drop=True)


def impute_numeric(df: pd.DataFrame, cols: list, strategy: str = "median") -> pd.DataFrame:
    for col in cols:
        if col in df.columns and df[col].isnull().any():
            fill_val = df[col].median() if strategy == "median" else df[col].mean()
            df[col] = df[col].fillna(fill_val)
    return df


def impute_categorical(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    for col in cols:
        if col in df.columns and df[col].isnull().any():
            mode_val = df[col].mode(dropna=True)
            if len(mode_val) > 0:
                df[col] = df[col].fillna(mode_val[0])
    return df


def normalize_category(val: str) -> str:
    """Normalize a category string: strip, lowercase, then title-case."""
    if pd.isna(val):
        return val
    return str(val).strip().title()


def cap_outliers_iqr(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Cap outliers at 1.5×IQR fence (Winsorization, not removal)."""
    for col in cols:
        if col not in df.columns or df[col].dtype not in [np.float64, np.int64, float, int]:
            continue
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        before_outliers = ((df[col] < lower) | (df[col] > upper)).sum()
        df[col] = df[col].clip(lower=lower, upper=upper)
        if before_outliers:
            print(f"    Capped {before_outliers} outliers in '{col}' [{lower:.2f}, {upper:.2f}]")
    return df


def parse_date_robust(val) -> pd.Timestamp:
    """Parse a date string in any common format."""
    if pd.isna(val):
        return pd.NaT
    try:
        return pd.Timestamp(date_parser.parse(str(val), dayfirst=False))
    except Exception:
        return pd.NaT


# ─────────────────────────────────────────────
# Dataset-Specific Cleaning
# ─────────────────────────────────────────────

def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    print("\n  [Products] Cleaning...")
    df = remove_duplicates(df, subset=["product_id"])
    df["category"] = df["category"].apply(normalize_category)
    df = impute_numeric(df, ["cost_price", "selling_price"])
    df = impute_categorical(df, ["category", "product_name"])
    df = cap_outliers_iqr(df, ["cost_price", "selling_price"])
    # Ensure selling_price >= cost_price
    mask = df["selling_price"] < df["cost_price"]
    df.loc[mask, "selling_price"] = df.loc[mask, "cost_price"] * 1.20
    print(f"    Products clean: {len(df):,} rows")
    return df


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    print("\n  [Customers] Cleaning...")
    df = remove_duplicates(df, subset=["customer_id"])
    df = impute_categorical(df, ["location", "region", "segment"])
    df["segment"] = df["segment"].apply(normalize_category)
    df["region"] = df["region"].apply(normalize_category)
    # Parse signup_date
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
    # Fill missing signup_date with reasonable default
    df["signup_date"] = df["signup_date"].fillna(pd.Timestamp("2022-01-01"))
    print(f"    Customers clean: {len(df):,} rows")
    return df


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    print("\n  [Orders] Cleaning...")
    df = remove_duplicates(df, subset=["order_id"])
    # Parse mixed-format dates
    print("    Parsing mixed date formats...")
    df["date"] = df["date"].apply(parse_date_robust)
    missing_dates = df["date"].isna().sum()
    if missing_dates:
        df["date"] = df["date"].fillna(method="ffill")
        print(f"    Forward-filled {missing_dates} missing dates")
    # Numeric coercion
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = impute_numeric(df, ["quantity", "price"])
    df = cap_outliers_iqr(df, ["quantity", "price"])
    # Ensure positive values
    df["quantity"] = df["quantity"].abs().clip(lower=1)
    df["price"] = df["price"].abs().clip(lower=0.01)
    # Region / status normalization
    df = impute_categorical(df, ["region", "status"])
    df["region"] = df["region"].apply(normalize_category)
    df["status"] = df["status"].apply(normalize_category)
    print(f"    Orders clean: {len(df):,} rows")
    return df


def clean_returns(df: pd.DataFrame) -> pd.DataFrame:
    print("\n  [Returns] Cleaning...")
    df = remove_duplicates(df, subset=["order_id"])
    df["return_flag"] = pd.to_numeric(df["return_flag"], errors="coerce").fillna(1).astype(int)
    df = impute_categorical(df, ["reason"])
    df["return_date"] = pd.to_datetime(df["return_date"], errors="coerce")
    print(f"    Returns clean: {len(df):,} rows")
    return df


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("DATA CLEANING LAYER")
    print("=" * 60)

    raw = {name: load_csv(name) for name in ["orders", "products", "customers", "returns"]}

    cleaned = {
        "orders": clean_orders(raw["orders"]),
        "products": clean_products(raw["products"]),
        "customers": clean_customers(raw["customers"]),
        "returns": clean_returns(raw["returns"]),
    }

    for name, df in cleaned.items():
        path = os.path.join(PROCESSED_DIR, f"{name}_clean.parquet")
        df.to_parquet(path, index=False)
        remaining_nulls = df.isnull().sum().sum()
        print(f"\n  [OK] Saved {name}_clean.parquet -- {len(df):,} rows | remaining NaNs: {remaining_nulls}")

    print("\n[DONE] Data cleaning complete. Clean data saved to data/processed/")
    print("=" * 60)
    return cleaned


if __name__ == "__main__":
    main()
