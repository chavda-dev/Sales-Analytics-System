"""
api.py — Bonus Flask REST API
Exposes KPI, insights, and filtered revenue endpoints.
Run: python app/api.py
"""

import os
import sys
import json
import warnings
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

app = Flask(__name__)
CORS(app)

# ─── Load data at startup ─────────────────────

_cache = {}


def get_data():
    if not _cache:
        _cache["fact"] = pd.read_parquet(os.path.join(PROCESSED_DIR, "fact_final.parquet"))
        _cache["fact"]["date"] = pd.to_datetime(_cache["fact"]["date"])
        _cache["monthly"] = pd.read_parquet(os.path.join(PROCESSED_DIR, "monthly_revenue.parquet"))
        _cache["cat_stats"] = pd.read_parquet(os.path.join(PROCESSED_DIR, "category_stats.parquet"))
        _cache["region_stats"] = pd.read_parquet(os.path.join(PROCESSED_DIR, "region_stats.parquet"))
        _cache["rfm"] = pd.read_parquet(os.path.join(PROCESSED_DIR, "rfm.parquet"))
        _cache["forecast"] = pd.read_parquet(os.path.join(PROCESSED_DIR, "forecast.parquet"))
    return _cache


# ─────────────────────────────────────────────
# GET /api/health
# ─────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Sales Analytics API is running."})


# ─────────────────────────────────────────────
# GET /api/kpis
# ─────────────────────────────────────────────

@app.route("/api/kpis", methods=["GET"])
def get_kpis():
    data = get_data()
    fact = data["fact"]
    monthly = data["monthly"]

    total_revenue = float(fact["revenue"].sum())
    total_profit = float(fact["profit"].sum())
    total_orders = int(fact["order_id"].nunique())
    total_customers = int(fact["customer_id"].nunique())
    aov = round(total_revenue / total_orders, 2) if total_orders else 0
    profit_margin = round(total_profit / total_revenue * 100, 2) if total_revenue else 0
    return_rate = round(float(fact["return_flag"].mean()) * 100, 2)

    mom_growth = 0.0
    monthly_sorted = monthly.sort_values("month_label")
    if len(monthly_sorted) >= 2:
        last = float(monthly_sorted["revenue"].iloc[-1])
        prev = float(monthly_sorted["revenue"].iloc[-2])
        mom_growth = round((last - prev) / prev * 100, 2) if prev else 0

    return jsonify({
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "aov": aov,
        "profit_margin_pct": profit_margin,
        "return_rate_pct": return_rate,
        "mom_growth_pct": mom_growth,
    })


# ─────────────────────────────────────────────
# GET /api/insights
# ─────────────────────────────────────────────

@app.route("/api/insights", methods=["GET"])
def get_insights():
    data = get_data()
    fact = data["fact"]
    cat_stats = data["cat_stats"]
    region_stats = data["region_stats"]
    monthly = data["monthly"]
    rfm = data["rfm"]

    insights = []

    # Region insight
    top_r = region_stats.iloc[0]
    insights.append(
        f"Region '{top_r['region']}' contributes {top_r['revenue_share_pct']:.1f}% of total revenue."
    )

    # Category return rate
    max_ret = cat_stats.loc[cat_stats["return_rate_pct"].idxmax()]
    insights.append(
        f"'{max_ret['category']}' has the highest return rate at {max_ret['return_rate_pct']:.1f}%."
    )

    # MoM change
    monthly_s = monthly.sort_values("month_label")
    monthly_s["prev"] = monthly_s["revenue"].shift(1)
    monthly_s["mom"] = ((monthly_s["revenue"] - monthly_s["prev"]) / monthly_s["prev"] * 100).round(2)
    valid = monthly_s.dropna(subset=["mom"])
    if not valid.empty:
        worst = valid.loc[valid["mom"].idxmin()]
        insights.append(f"Revenue dropped {abs(worst['mom']):.1f}% in {worst['month_label']} vs prior month.")
        best = valid.loc[valid["mom"].idxmax()]
        insights.append(f"Revenue grew {best['mom']:.1f}% in {best['month_label']} — best month on record.")

    # CLV
    if "clv_segment" in fact.columns:
        high = fact[fact["clv_segment"] == "High Value"]
        if not high.empty:
            pct = high["revenue"].sum() / fact["revenue"].sum() * 100
            cust_pct = high["customer_id"].nunique() / fact["customer_id"].nunique() * 100
            insights.append(
                f"Top {cust_pct:.1f}% of customers (High Value) generate {pct:.1f}% of revenue."
            )

    # Overall KPIs
    total_revenue = fact["revenue"].sum()
    profit_margin = fact["profit"].sum() / total_revenue * 100
    return_rate = fact["return_flag"].mean() * 100
    insights.append(f"Overall profit margin: {profit_margin:.1f}% on ${total_revenue:,.0f} total revenue.")
    insights.append(f"Overall return rate: {return_rate:.1f}% across {fact['order_id'].nunique():,} orders.")

    return jsonify({"count": len(insights), "insights": insights})


# ─────────────────────────────────────────────
# GET /api/revenue
# Optional params: region, category, year
# ─────────────────────────────────────────────

@app.route("/api/revenue", methods=["GET"])
def get_revenue():
    data = get_data()
    fact = data["fact"].copy()

    region = request.args.get("region")
    category = request.args.get("category")
    year = request.args.get("year")

    if region:
        fact = fact[fact["region"].str.lower() == region.lower()]
    if category:
        fact = fact[fact["category"].str.lower() == category.lower()]
    if year:
        fact = fact[fact["year"] == int(year)]

    if fact.empty:
        return jsonify({"error": "No data matches the specified filters."}), 404

    monthly_agg = fact.groupby("month_label").agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
    ).reset_index().sort_values("month_label")

    return jsonify({
        "filters": {"region": region, "category": category, "year": year},
        "total_revenue": float(monthly_agg["revenue"].sum()),
        "months": monthly_agg.to_dict(orient="records"),
    })


# ─────────────────────────────────────────────
# GET /api/forecast
# ─────────────────────────────────────────────

@app.route("/api/forecast", methods=["GET"])
def get_forecast():
    data = get_data()
    forecast = data["forecast"]
    return jsonify({
        "method": forecast["method"].iloc[0] if not forecast.empty else "N/A",
        "periods": len(forecast),
        "forecast": forecast[["month_label", "forecast_revenue", "lower_ci", "upper_ci"]].to_dict(orient="records"),
    })


# ─────────────────────────────────────────────
# GET /api/categories
# ─────────────────────────────────────────────

@app.route("/api/categories", methods=["GET"])
def get_categories():
    data = get_data()
    cat = data["cat_stats"]
    return jsonify(cat.to_dict(orient="records"))


# ─────────────────────────────────────────────
# GET /api/rfm
# ─────────────────────────────────────────────

@app.route("/api/rfm", methods=["GET"])
def get_rfm():
    data = get_data()
    rfm = data["rfm"]
    seg_counts = rfm["rfm_segment"].value_counts().to_dict()
    return jsonify({
        "total_customers": len(rfm),
        "segments": seg_counts,
        "top_customers": rfm.nlargest(10, "monetary")[
            ["customer_id", "recency", "frequency", "monetary", "rfm_segment"]
        ].to_dict(orient="records"),
    })


if __name__ == "__main__":
    print("=" * 50)
    print("Sales Analytics REST API")
    print("=" * 50)
    print("Endpoints:")
    print("  GET /api/health")
    print("  GET /api/kpis")
    print("  GET /api/insights")
    print("  GET /api/revenue?region=X&category=Y&year=Z")
    print("  GET /api/forecast")
    print("  GET /api/categories")
    print("  GET /api/rfm")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
