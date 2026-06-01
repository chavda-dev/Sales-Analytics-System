"""
analytics.py â€” Advanced Analytics Engine
Computes KPIs, cohort analysis, RFM, trend detection,
anomaly detection, forecasting, and auto-generated insights.
"""

import os
import warnings
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


def load_fact() -> pd.DataFrame:
    path = os.path.join(PROCESSED_DIR, "fact_final.parquet")
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])
    return df


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 1. KPI Calculations
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def compute_kpis(df: pd.DataFrame) -> dict:
    """Compute top-level business KPIs."""
    total_revenue = df["revenue"].sum()
    total_profit = df["profit"].sum()
    total_orders = df["order_id"].nunique()
    total_customers = df["customer_id"].nunique()
    aov = total_revenue / total_orders if total_orders else 0
    profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0
    return_rate = df["return_flag"].mean() * 100

    # MoM growth on the most recent full month vs previous
    monthly = df.groupby("month_label")["revenue"].sum().sort_index()
    if len(monthly) >= 2:
        last_rev = monthly.iloc[-1]
        prev_rev = monthly.iloc[-2]
        mom_growth = ((last_rev - prev_rev) / prev_rev * 100) if prev_rev else 0
    else:
        mom_growth = 0.0

    return {
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "total_orders": int(total_orders),
        "total_customers": int(total_customers),
        "aov": round(aov, 2),
        "profit_margin_pct": round(profit_margin, 2),
        "return_rate_pct": round(return_rate, 2),
        "mom_growth_pct": round(mom_growth, 2),
    }


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 2. Monthly Revenue + Moving Averages
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def compute_time_series(df: pd.DataFrame) -> pd.DataFrame:
    """Daily revenue with 7-day and 30-day rolling averages."""
    daily = df.groupby(df["date"].dt.date)["revenue"].sum().reset_index()
    daily.columns = ["date", "revenue"]
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date").reset_index(drop=True)
    daily["ma_7"] = daily["revenue"].rolling(7, min_periods=1).mean().round(2)
    daily["ma_30"] = daily["revenue"].rolling(30, min_periods=1).mean().round(2)
    return daily


def compute_monthly_growth(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly revenue and MoM growth rate."""
    monthly = df.groupby("month_label").agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
    ).reset_index().sort_values("month_label")
    monthly["prev_revenue"] = monthly["revenue"].shift(1)
    monthly["mom_growth_pct"] = (
        (monthly["revenue"] - monthly["prev_revenue"]) /
        monthly["prev_revenue"].replace(0, np.nan) * 100
    ).round(2)
    return monthly


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 3. Cohort Retention Analysis
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def compute_cohort_retention(df: pd.DataFrame) -> pd.DataFrame:
    """Build cohort retention matrix (cohort_month Ã- months_since_first_purchase)."""
    df = df.copy()
    df["period_month"] = df["date"].dt.to_period("M")

    # First purchase month per customer  
    fp = df.groupby("customer_id")["period_month"].min().reset_index()
    fp.columns = ["customer_id", "cohort"]
    df = df.merge(fp, on="customer_id", how="left")
    df["months_since"] = (df["period_month"] - df["cohort"]).apply(lambda x: x.n if hasattr(x, "n") else 0)

    cohort_data = df.groupby(["cohort", "months_since"])["customer_id"].nunique().reset_index()
    cohort_data.columns = ["cohort", "months_since", "active_customers"]

    # Pivot
    cohort_pivot = cohort_data.pivot(index="cohort", columns="months_since", values="active_customers")
    cohort_size = cohort_pivot[0]
    retention = cohort_pivot.divide(cohort_size, axis=0).round(4) * 100

    # Keep only first 12 months to avoid sparse data
    retention = retention[[c for c in retention.columns if c <= 12]]
    return retention.fillna(0)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 4. Anomaly Detection
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def detect_anomalies(daily: pd.DataFrame, window: int = 30, z_thresh: float = 2.5) -> pd.DataFrame:
    """Flag days where revenue deviates > z_thresh Ïƒ from rolling mean."""
    daily = daily.copy()
    rolling_mean = daily["revenue"].rolling(window, min_periods=5).mean()
    rolling_std = daily["revenue"].rolling(window, min_periods=5).std()
    daily["z_score"] = ((daily["revenue"] - rolling_mean) / rolling_std.replace(0, np.nan)).round(3)
    daily["is_anomaly"] = daily["z_score"].abs() > z_thresh
    daily["anomaly_type"] = daily.apply(
        lambda r: "Spike" if r["is_anomaly"] and r["z_score"] > 0 else
                  ("Drop" if r["is_anomaly"] else "Normal"), axis=1
    )
    return daily


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 5. Seasonality Detection (STL - simplified)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def detect_seasonality(df: pd.DataFrame) -> dict:
    """Detect seasonal patterns: best/worst months and peak day of week."""
    by_month = df.groupby("month")["revenue"].mean()
    by_dow = df.groupby("day_of_week")["revenue"].mean().sort_values(ascending=False)
    by_quarter = df.groupby("quarter")["revenue"].mean()

    return {
        "best_month": int(by_month.idxmax()),
        "worst_month": int(by_month.idxmin()),
        "best_day_of_week": by_dow.index[0],
        "worst_day_of_week": by_dow.index[-1],
        "best_quarter": int(by_quarter.idxmax()),
        "monthly_avg": by_month.round(2).to_dict(),
        "quarterly_avg": by_quarter.round(2).to_dict(),
    }


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 6. Forecasting (ARIMA or Linear Fallback)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def forecast_revenue(monthly: pd.DataFrame, periods: int = 6) -> pd.DataFrame:
    """Forecast next N months of revenue using ARIMA(2,1,2) or linear trend."""
    from statsmodels.tsa.arima.model import ARIMA

    series = monthly["revenue"].values.astype(float)

    try:
        model = ARIMA(series, order=(2, 1, 2))
        result = model.fit()
        forecast = result.forecast(steps=periods)
        conf_int = result.get_forecast(steps=periods).conf_int(alpha=0.20)
        lower = conf_int.iloc[:, 0].values
        upper = conf_int.iloc[:, 1].values
        method = "ARIMA(2,1,2)"
    except Exception:
        # Linear fallback
        x = np.arange(len(series))
        slope, intercept, *_ = stats.linregress(x, series)
        forecast = np.array([slope * (len(series) + i) + intercept for i in range(periods)])
        std_err = np.std(series) * 0.15
        lower = forecast - 1.96 * std_err
        upper = forecast + 1.96 * std_err
        method = "Linear Regression (fallback)"

    last_period = pd.Period(monthly["month_label"].iloc[-1], freq="M")
    future_periods = [str(last_period + i) for i in range(1, periods + 1)]

    forecast_df = pd.DataFrame({
        "month_label": future_periods,
        "forecast_revenue": np.maximum(forecast, 0).round(2),
        "lower_ci": np.maximum(lower, 0).round(2),
        "upper_ci": np.maximum(upper, 0).round(2),
        "method": method,
    })
    return forecast_df


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 7. Category & Region Analytics
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def compute_category_stats(df: pd.DataFrame) -> pd.DataFrame:
    cat = df.groupby("category").agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
        returns=("return_flag", "sum"),
        total_rows=("order_id", "count"),
    ).reset_index()
    cat["profit_margin_pct"] = (cat["profit"] / cat["revenue"] * 100).round(2)
    cat["return_rate_pct"] = (cat["returns"] / cat["total_rows"] * 100).round(2)
    cat["revenue_share_pct"] = (cat["revenue"] / cat["revenue"].sum() * 100).round(2)
    return cat.sort_values("revenue", ascending=False)


def compute_region_stats(df: pd.DataFrame) -> pd.DataFrame:
    region = df.groupby("region").agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
    ).reset_index()
    region["revenue_share_pct"] = (region["revenue"] / region["revenue"].sum() * 100).round(2)
    region["profit_margin_pct"] = (region["profit"] / region["revenue"] * 100).round(2)
    return region.sort_values("revenue", ascending=False)


def compute_top_products(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    top = df.groupby(["product_id", "product_id"]).agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        units_sold=("quantity", "sum"),
        orders=("order_id", "nunique"),
    ).reset_index()
    return top.nlargest(n, "revenue")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 8. Auto-Generated Insights
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def generate_insights(kpis: dict, cat_stats: pd.DataFrame, region_stats: pd.DataFrame,
                      monthly: pd.DataFrame, anomalies: pd.DataFrame, rfm: pd.DataFrame) -> list:
    """Compute dynamic, data-driven insight strings."""
    insights = []

    # 1. Top region revenue share
    top_region = region_stats.iloc[0]
    insights.append(
        f"ðŸŒ Region '{top_region['region']}' contributes {top_region['revenue_share_pct']:.1f}% "
        f"of total revenue (${top_region['revenue']:,.0f})."
    )

    # 2. Highest return rate category
    max_return_cat = cat_stats.loc[cat_stats["return_rate_pct"].idxmax()]
    insights.append(
        f"ðŸ”„ '{max_return_cat['category']}' has the highest return rate at "
        f"{max_return_cat['return_rate_pct']:.1f}%, warranting quality review."
    )

    # 3. MoM revenue change (largest drop)
    monthly_sorted = monthly.dropna(subset=["mom_growth_pct"])
    if not monthly_sorted.empty:
        worst_month = monthly_sorted.loc[monthly_sorted["mom_growth_pct"].idxmin()]
        insights.append(
            f"ðŸ“‰ Largest revenue drop: {worst_month['mom_growth_pct']:.1f}% in "
            f"{worst_month['month_label']} vs the prior month."
        )
        best_month = monthly_sorted.loc[monthly_sorted["mom_growth_pct"].idxmax()]
        insights.append(
            f"ðŸ“ˆ Best growth month: {best_month['month_label']} saw +{best_month['mom_growth_pct']:.1f}% "
            f"MoM revenue growth."
        )

    # 4. Top customer revenue concentration
    total_rev = kpis["total_revenue"]
    insights.append(
        f"ðŸ’° Overall profit margin is {kpis['profit_margin_pct']:.1f}% "
        f"on ${total_rev:,.0f} total revenue."
    )

    # 5. Return rate overall
    insights.append(
        f"ðŸ“¦ Overall return rate is {kpis['return_rate_pct']:.1f}% "
        f"across {kpis['total_orders']:,} orders."
    )

    # 6. Average Order Value
    insights.append(
        f"ðŸ›’ Average Order Value (AOV) is ${kpis['aov']:,.2f} "
        f"from {kpis['total_customers']:,} unique customers."
    )

    # 7. Best performing category
    best_cat = cat_stats.iloc[0]
    insights.append(
        f"â­ '{best_cat['category']}' is the top revenue-generating category "
        f"contributing {best_cat['revenue_share_pct']:.1f}% (${best_cat['revenue']:,.0f})."
    )

    # 8. Anomalies detected
    n_anomalies = anomalies["is_anomaly"].sum()
    n_spikes = (anomalies["anomaly_type"] == "Spike").sum()
    n_drops = (anomalies["anomaly_type"] == "Drop").sum()
    insights.append(
        f"âš ï¸ {n_anomalies} revenue anomalies detected: {n_spikes} spikes and {n_drops} drops "
        f"over the analysis period."
    )

    # 9. RFM Champions
    if not rfm.empty and "rfm_segment" in rfm.columns:
        champions_pct = (rfm["rfm_segment"] == "Champions").mean() * 100
        insights.append(
            f"ðŸ† {champions_pct:.1f}% of customers are classified as 'Champions' "
            f"(high recency, frequency & monetary value)."
        )

    # 10. Current MoM growth
    insights.append(
        f"ðŸ“Š Latest MoM revenue growth: {kpis['mom_growth_pct']:+.1f}%."
    )

    return insights


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Main
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main():
    print("=" * 60)
    print("ANALYTICS ENGINE")
    print("=" * 60)

    df = load_fact()
    rfm = pd.read_parquet(os.path.join(PROCESSED_DIR, "rfm.parquet"))

    print("\n  Computing KPIs...")
    kpis = compute_kpis(df)
    for k, v in kpis.items():
        print(f"    {k}: {v}")

    print("\n  Computing time series & moving averages...")
    daily = compute_time_series(df)
    monthly = compute_monthly_growth(df)

    print("  Detecting anomalies...")
    daily_anomalies = detect_anomalies(daily)
    n_anomalies = daily_anomalies["is_anomaly"].sum()
    print(f"    Anomalies detected: {n_anomalies}")

    print("  Detecting seasonality...")
    seasonality = detect_seasonality(df)
    print(f"    Best month: {seasonality['best_month']}, Best day: {seasonality['best_day_of_week']}")

    print("  Building cohort retention matrix...")
    cohort = compute_cohort_retention(df)
    print(f"    Cohort matrix: {cohort.shape}")

    print("  Forecasting 6-month revenue...")
    forecast = forecast_revenue(monthly)
    print(f"    Method: {forecast['method'].iloc[0]}")

    print("  Computing category & region stats...")
    cat_stats = compute_category_stats(df)
    region_stats = compute_region_stats(df)

    print("\n  Generating insights...")
    insights = generate_insights(kpis, cat_stats, region_stats, monthly, daily_anomalies, rfm)
    for ins in insights:
        print(f"    {ins}")

    # Save outputs
    daily_anomalies.to_parquet(os.path.join(PROCESSED_DIR, "daily_revenue.parquet"), index=False)
    monthly.to_parquet(os.path.join(PROCESSED_DIR, "monthly_revenue.parquet"), index=False)
    forecast.to_parquet(os.path.join(PROCESSED_DIR, "forecast.parquet"), index=False)
    cohort.to_parquet(os.path.join(PROCESSED_DIR, "cohort_retention.parquet"), index=False)
    cat_stats.to_parquet(os.path.join(PROCESSED_DIR, "category_stats.parquet"), index=False)
    region_stats.to_parquet(os.path.join(PROCESSED_DIR, "region_stats.parquet"), index=False)

    print("\nâœ… Analytics complete. All outputs saved to data/processed/")
    print("=" * 60)
    return kpis, insights, daily_anomalies, monthly, forecast, cohort, cat_stats, region_stats


if __name__ == "__main__":
    main()
