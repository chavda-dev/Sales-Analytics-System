"""
db_loader.py — Database Layer
Loads cleaned/transformed data into SQLite via SQLAlchemy.
Creates star schema, loads all dimension and fact tables,
creates views, and runs validation queries.
"""

import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(BASE_DIR, "data", "sales_analytics.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "sql", "schema.sql")


def get_engine():
    return create_engine(f"sqlite:///{DB_PATH}", echo=False)


def execute_schema(engine):
    print("  Executing schema DDL...")
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()

    # SQLite needs statements executed one at a time for CREATE VIEW
    with engine.connect() as conn:
        # Split by semicolons but keep non-empty statements
        statements = [s.strip() for s in schema_sql.split(";") if s.strip() and not s.strip().startswith("--")]
        for stmt in statements:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                print(f"    Warning executing statement: {e}")
        conn.commit()
    print("  ✓ Schema created")


def load_dimensions(engine, fact: pd.DataFrame, products: pd.DataFrame, customers: pd.DataFrame):
    print("  Loading dimension tables...")

    # dim_customers
    dim_cust = fact.groupby("customer_id").agg(
        location=("cust_region", "first"),
        region=("cust_region", "first"),
        segment=("cust_segment", "first"),
        clv=("clv", "first"),
        rfm_segment=("rfm_segment", "first"),
        clv_segment=("clv_segment", "first"),
    ).reset_index()
    dim_cust.to_sql("dim_customers", engine, if_exists="replace", index=False)
    print(f"    ✓ dim_customers: {len(dim_cust):,} rows")

    # dim_products
    products_db = products[["product_id", "product_name", "category", "cost_price", "selling_price"]].drop_duplicates("product_id")
    products_db.to_sql("dim_products", engine, if_exists="replace", index=False)
    print(f"    ✓ dim_products: {len(products_db):,} rows")

    # dim_time
    fact["date"] = pd.to_datetime(fact["date"])
    dim_time = fact[["date", "year", "month", "quarter", "week_of_year", "day_of_week", "month_label"]].drop_duplicates("date").copy()
    dim_time["date_id"] = dim_time["date"].dt.strftime("%Y-%m-%d")
    dim_time["date"] = dim_time["date"].dt.strftime("%Y-%m-%d")
    dim_time.to_sql("dim_time", engine, if_exists="replace", index=False)
    print(f"    ✓ dim_time: {len(dim_time):,} rows")


def load_fact(engine, fact: pd.DataFrame):
    print("  Loading fact_sales table...")
    fact_db = fact.copy()
    fact_db["date"] = pd.to_datetime(fact_db["date"])
    fact_db["date_id"] = fact_db["date"].dt.strftime("%Y-%m-%d")

    cols = [
        "order_id", "customer_id", "product_id", "date_id", "region", "status",
        "quantity", "price", "revenue", "cost", "profit", "profit_margin",
        "return_flag", "reason", "rfm_segment", "clv_segment", "cohort_month"
    ]
    available_cols = [c for c in cols if c in fact_db.columns]
    fact_db = fact_db[available_cols].rename(columns={"reason": "return_reason"})

    fact_db.to_sql("fact_sales", engine, if_exists="replace", index=False)
    print(f"    ✓ fact_sales: {len(fact_db):,} rows")


def run_validation(engine):
    print("\n  Running validation queries...")
    queries = {
        "Total Revenue": "SELECT ROUND(SUM(revenue), 2) FROM fact_sales",
        "Total Orders": "SELECT COUNT(DISTINCT order_id) FROM fact_sales",
        "Return Rate %": "SELECT ROUND(AVG(return_flag)*100, 2) FROM fact_sales",
        "Distinct Customers": "SELECT COUNT(DISTINCT customer_id) FROM fact_sales",
        "Regions": "SELECT COUNT(DISTINCT region) FROM fact_sales",
    }
    with engine.connect() as conn:
        for label, q in queries.items():
            result = conn.execute(text(q)).fetchone()[0]
            print(f"    {label}: {result}")


def main():
    print("=" * 60)
    print("DATABASE LOADER — SQLite Star Schema")
    print("=" * 60)

    fact_path = os.path.join(PROCESSED_DIR, "fact_final.parquet")
    if not os.path.exists(fact_path):
        raise FileNotFoundError("fact_final.parquet not found. Run transformation.py first.")

    fact = pd.read_parquet(fact_path)
    products = pd.read_parquet(os.path.join(PROCESSED_DIR, "products_clean.parquet"))
    customers = pd.read_parquet(os.path.join(PROCESSED_DIR, "customers_clean.parquet"))

    print(f"\n  Loaded fact_final: {len(fact):,} rows")

    engine = get_engine()
    execute_schema(engine)
    load_dimensions(engine, fact, products, customers)
    load_fact(engine, fact)
    run_validation(engine)

    print(f"\n✅ Database loaded: {DB_PATH}")
    print("=" * 60)
    return engine


if __name__ == "__main__":
    main()
