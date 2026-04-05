# -*- coding: utf-8 -*-
"""
ingestion.py - Data Ingestion Layer
Generates realistic synthetic datasets with intentional data quality issues.
Saves raw CSVs to data/raw/.
"""

import os
import random
import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
N_ORDERS = 10_000
N_CUSTOMERS = 2_000
N_PRODUCTS = 200
REGIONS = ["North", "South", "East", "West", "Central"]
CATEGORIES = ["Electronics", "Clothing", "Furniture", "Sports", "Books", "Food & Beverage", "Health & Beauty"]
SEGMENTS = ["Enterprise", "SMB", "Consumer"]
RETURN_REASONS = ["Defective", "Wrong Item", "Changed Mind", "Quality Issue", "Damaged in Shipping"]

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%Y/%m/%d"]  # inconsistent formats to inject


def random_date(start: datetime, end: datetime) -> datetime:
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))


def inject_missing(df: pd.DataFrame, frac: float = 0.05) -> pd.DataFrame:
    """Randomly set ~frac of values to NaN, excluding primary key columns."""
    df = df.copy()
    skip_cols = [c for c in df.columns if c.endswith("_id")]
    eligible = [c for c in df.columns if c not in skip_cols]
    total_cells = len(df) * len(eligible)
    n_missing = int(total_cells * frac)
    rows = np.random.randint(0, len(df), n_missing)
    cols = np.random.choice(eligible, n_missing)
    for r, c in zip(rows, cols):
        df.iat[r, df.columns.get_loc(c)] = np.nan
    return df


def inject_duplicates(df: pd.DataFrame, frac: float = 0.03) -> pd.DataFrame:
    """Duplicate ~frac of rows and append them."""
    n_dups = int(len(df) * frac)
    dup_rows = df.sample(n=n_dups, random_state=42)
    return pd.concat([df, dup_rows], ignore_index=True)


def inject_outliers(series: pd.Series, frac: float = 0.02) -> pd.Series:
    """Spike ~frac of numeric values to extreme outlier range."""
    series = series.copy()
    n = int(len(series) * frac)
    idx = np.random.choice(series.dropna().index, n, replace=False)
    series.loc[idx] = series.mean() * np.random.uniform(8, 12, n)
    return series


def random_inconsistent_date(dt: datetime) -> str:
    fmt = random.choice(DATE_FORMATS)
    return dt.strftime(fmt)


# ─────────────────────────────────────────────
# 1. Products Dataset
# ─────────────────────────────────────────────
def generate_products() -> pd.DataFrame:
    print("  Generating products dataset...")
    records = []
    for i in range(1, N_PRODUCTS + 1):
        category = random.choice(CATEGORIES)
        # Randomise category case to simulate inconsistency
        raw_cat = random.choice([category, category.upper(), category.lower(), category.title()])
        cost = round(random.uniform(5, 500), 2)
        margin = random.uniform(0.15, 0.60)
        selling = round(cost * (1 + margin), 2)
        records.append({
            "product_id": f"P{i:04d}",
            "product_name": fake.catch_phrase(),
            "category": raw_cat,
            "cost_price": cost,
            "selling_price": selling,
        })
    df = pd.DataFrame(records)
    df = inject_missing(df, frac=0.03)
    df = inject_duplicates(df, frac=0.02)
    return df


# ─────────────────────────────────────────────
# 2. Customers Dataset
# ─────────────────────────────────────────────
def generate_customers() -> pd.DataFrame:
    print("  Generating customers dataset...")
    records = []
    for i in range(1, N_CUSTOMERS + 1):
        records.append({
            "customer_id": f"C{i:05d}",
            "name": fake.name(),
            "email": fake.email(),
            "location": fake.city(),
            "region": random.choice(REGIONS),
            "segment": random.choice(SEGMENTS),
            "signup_date": fake.date_between(start_date="-5y", end_date="-1y").strftime("%Y-%m-%d"),
        })
    df = pd.DataFrame(records)
    df = inject_missing(df, frac=0.04)
    df = inject_duplicates(df, frac=0.02)
    return df


# ─────────────────────────────────────────────
# 3. Orders Dataset
# ─────────────────────────────────────────────
def generate_orders(customer_ids: list, product_ids: list) -> pd.DataFrame:
    print("  Generating orders dataset...")
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 12, 31)
    records = []
    for i in range(1, N_ORDERS + 1):
        cid = random.choice(customer_ids)
        pid = random.choice(product_ids)
        dt = random_date(start_date, end_date)
        qty = random.randint(1, 20)
        price = round(random.uniform(10, 600), 2)
        region = random.choice(REGIONS)
        date_str = random_inconsistent_date(dt)
        records.append({
            "order_id": f"O{i:06d}",
            "customer_id": cid,
            "product_id": pid,
            "date": date_str,
            "quantity": qty,
            "price": price,
            "region": region,
            "status": random.choice(["Completed", "Completed", "Completed", "Pending", "Cancelled"]),
        })
    df = pd.DataFrame(records)
    # Inject outliers in price and quantity
    df["price"] = inject_outliers(df["price"].astype(float))
    df["quantity"] = inject_outliers(df["quantity"].astype(float))
    df = inject_missing(df, frac=0.05)
    df = inject_duplicates(df, frac=0.03)
    return df


# ─────────────────────────────────────────────
# 4. Returns Dataset
# ─────────────────────────────────────────────
def generate_returns(order_ids: list) -> pd.DataFrame:
    print("  Generating returns dataset...")
    # ~15% of orders get returned
    returned_orders = random.sample(order_ids, int(len(order_ids) * 0.15))
    records = []
    for oid in returned_orders:
        records.append({
            "order_id": oid,
            "return_flag": 1,
            "reason": random.choice(RETURN_REASONS),
            "return_date": fake.date_between(start_date="-2y", end_date="today").strftime("%Y-%m-%d"),
        })
    df = pd.DataFrame(records)
    df = inject_missing(df, frac=0.03)
    df = inject_duplicates(df, frac=0.02)
    return df


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print("=" * 60)
    print("DATA INGESTION LAYER — Generating Raw Datasets")
    print("=" * 60)

    products = generate_products()
    customers = generate_customers()

    # Use clean IDs for referential integrity before injecting issues
    clean_customer_ids = [f"C{i:05d}" for i in range(1, N_CUSTOMERS + 1)]
    clean_product_ids = [f"P{i:04d}" for i in range(1, N_PRODUCTS + 1)]

    orders = generate_orders(clean_customer_ids, clean_product_ids)
    clean_order_ids = [f"O{i:06d}" for i in range(1, N_ORDERS + 1)]
    returns = generate_returns(clean_order_ids)

    # Save to CSV
    datasets = {
        "orders": orders,
        "products": products,
        "customers": customers,
        "returns": returns,
    }

    for name, df in datasets.items():
        path = os.path.join(RAW_DIR, f"{name}.csv")
        df.to_csv(path, index=False)
        print(f"  [OK] Saved {name}.csv -- {len(df):,} rows x {len(df.columns)} cols | "
              f"missing: {df.isnull().sum().sum()} cells")

    print("\n[DONE] Data ingestion complete. Raw CSVs saved to data/raw/")
    print("=" * 60)


if __name__ == "__main__":
    main()
