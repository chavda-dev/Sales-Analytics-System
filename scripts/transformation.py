# -*- coding: utf-8 -*-
"""
transformation.py - Feature Engineering & Data Transformation Layer
Merges cleaned datasets, engineers features (Revenue, Profit, CLV, RFM, Cohorts).
Saves final analytical dataset to data/processed/fact_final.parquet.
"""

import os
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


def load_clean(name: str) -> pd.DataFrame:
    path = os.path.join(PROCESSED_DIR, f"{name}_clean.parquet")
    return pd.read_parquet(path)


# ─────────────────────────────────────────────
# 1. Merge & Basic Features
# ─────────────────────────────────────────────

def build_fact_table(orders: pd.DataFrame, products: pd.DataFrame,
                     customers: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    print("  Merging datasets...")
    # Merge products info
    fact = orders.merge(
        products[["product_id", "category", "cost_price", "selling_price"]],
        on="product_id", how="left"
    )
    # Merge customer info
    fact = fact.merge(
        customers[["customer_id", "region", "segment"]].rename(
            columns={"region": "cust_region", "segment": "cust_segment"}
        ),
        on="customer_id", how="left"
    )
    # Merge returns
    returns_slim = returns[["order_id", "return_flag", "reason"]].copy()
    fact = fact.merge(returns_slim, on="order_id", how="left")
    fact["return_flag"] = fact["return_flag"].fillna(0).astype(int)
    fact["reason"] = fact["reason"].fillna("No Return")
    return fact


def engineer_revenue_profit(df: pd.DataFrame) -> pd.DataFrame:
    print("  Engineering revenue & profit features...")
    # Use price from orders (actual selling price), cost from products
    df["revenue"] = (df["quantity"] * df["price"]).round(2)
    df["cost"] = (df["quantity"] * df["cost_price"]).round(2)
    df["profit"] = (df["revenue"] - df["cost"]).round(2)
    df["profit_margin"] = np.where(
        df["revenue"] > 0,
        (df["profit"] / df["revenue"] * 100).round(2),
        0.0
    )
    return df


def engineer_time_features(df: pd.DataFrame) -> pd.DataFrame:
    print("  Engineering time features...")
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["month_label"] = df["date"].dt.to_period("M").astype(str)
    df["day_of_week"] = df["date"].dt.day_name()
    return df


# ─────────────────────────────────────────────
# 2. Customer Lifetime Value (CLV)
# ─────────────────────────────────────────────

def compute_clv(df: pd.DataFrame) -> pd.DataFrame:
    print("  Computing Customer Lifetime Value (CLV)...")
    clv = df.groupby("customer_id")["profit"].sum().reset_index()
    clv.columns = ["customer_id", "clv"]
    df = df.merge(clv, on="customer_id", how="left")
    return df


# ─────────────────────────────────────────────
# 3. RFM Segmentation
# ─────────────────────────────────────────────

def compute_rfm(df: pd.DataFrame) -> pd.DataFrame:
    print("  Computing RFM scores...")
    snapshot_date = df["date"].max() + pd.Timedelta(days=1)

    rfm = df.groupby("customer_id").agg(
        recency=("date", lambda x: (snapshot_date - x.max()).days),
        frequency=("order_id", "nunique"),
        monetary=("revenue", "sum"),
    ).reset_index()

    # Score each dimension 1–5 (5 is best)
    rfm["r_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop")
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates="drop")
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates="drop")

    rfm["rfm_score"] = (
        rfm["r_score"].astype(str) +
        rfm["f_score"].astype(str) +
        rfm["m_score"].astype(str)
    )

    def rfm_segment(row):
        r, f, m = int(row["r_score"]), int(row["f_score"]), int(row["m_score"])
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif r >= 3 and f >= 3 and m >= 3:
            return "Loyal Customers"
        elif r >= 4 and f <= 2:
            return "New Customers"
        elif r >= 3 and m >= 4:
            return "Potential Loyalists"
        elif r <= 2 and f >= 3:
            return "At Risk"
        elif r <= 2 and f <= 2 and m <= 2:
            return "Lost"
        else:
            return "Needs Attention"

    rfm["rfm_segment"] = rfm.apply(rfm_segment, axis=1)

    df = df.merge(
        rfm[["customer_id", "recency", "frequency", "monetary", "rfm_score", "rfm_segment"]],
        on="customer_id", how="left"
    )
    return df, rfm


# ─────────────────────────────────────────────
# 4. Cohort Analysis Prep
# ─────────────────────────────────────────────

def compute_cohort_features(df: pd.DataFrame) -> pd.DataFrame:
    print("  Computing cohort features...")
    # First purchase month per customer
    first_purchase = df.groupby("customer_id")["date"].min().reset_index()
    first_purchase.columns = ["customer_id", "first_purchase_date"]
    first_purchase["cohort_month"] = first_purchase["first_purchase_date"].dt.to_period("M").astype(str)
    df = df.merge(first_purchase[["customer_id", "cohort_month"]], on="customer_id", how="left")
    # Months since first purchase
    df["period_month"] = df["date"].dt.to_period("M")
    df["cohort_period"] = df["period_month"] - first_purchase.set_index("customer_id").loc[
        df["customer_id"].values, "first_purchase_date"
    ].apply(lambda x: x.to_period("M")).values
    return df


# ─────────────────────────────────────────────
# 5. CLV Segmentation (High / Medium / Low)
# ─────────────────────────────────────────────

def clv_segment(clv: float, p33: float, p66: float) -> str:
    if clv >= p66:
        return "High Value"
    elif clv >= p33:
        return "Medium Value"
    return "Low Value"


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("TRANSFORMATION LAYER — Feature Engineering")
    print("=" * 60)

    orders = load_clean("orders")
    products = load_clean("products")
    customers = load_clean("customers")
    returns = load_clean("returns")

    fact = build_fact_table(orders, products, customers, returns)
    fact = engineer_revenue_profit(fact)
    fact = engineer_time_features(fact)
    fact = compute_clv(fact)
    fact, rfm = compute_rfm(fact)

    # CLV segments
    p33 = fact["clv"].quantile(0.33)
    p66 = fact["clv"].quantile(0.66)
    fact["clv_segment"] = fact["clv"].apply(lambda x: clv_segment(x, p33, p66))

    # Cohort features (simplified — just attach cohort_month)
    first_purchase = fact.groupby("customer_id")["date"].min().reset_index()
    first_purchase.columns = ["customer_id", "first_purchase_date"]
    first_purchase["cohort_month"] = first_purchase["first_purchase_date"].dt.to_period("M").astype(str)
    fact = fact.merge(first_purchase[["customer_id", "cohort_month"]], on="customer_id", how="left")

    # Final schema cleanup
    fact = fact.sort_values("date").reset_index(drop=True)

    # Save
    fact_path = os.path.join(PROCESSED_DIR, "fact_final.parquet")
    rfm_path = os.path.join(PROCESSED_DIR, "rfm.parquet")
    fact.to_parquet(fact_path, index=False)
    rfm.to_parquet(rfm_path, index=False)

    print(f"\n  [OK] fact_final.parquet -- {len(fact):,} rows x {len(fact.columns)} cols")
    print(f"  [OK] rfm.parquet -- {len(rfm):,} customer rows")
    print(f"  [OK] Revenue range: ${fact['revenue'].min():.2f} - ${fact['revenue'].max():.2f}")
    print(f"  [OK] Profit margin avg: {fact['profit_margin'].mean():.1f}%")
    print(f"  [OK] Return rate: {fact['return_flag'].mean()*100:.1f}%")
    print("\n[DONE] Transformation complete.")
    print("=" * 60)
    return fact, rfm


if __name__ == "__main__":
    main()
