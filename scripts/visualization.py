"""
visualization.py — Static Visualization Layer
Generates publication-quality charts saved to outputs/charts/.
All charts have titles, labels, legends, and are presentation-ready.
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
CHARTS_DIR = os.path.join(BASE_DIR, "outputs", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

# ─── Styling ─────────────────────────────────
PALETTE = sns.color_palette("husl", 10)
DARK_BG = "#1a1a2e"
CARD_BG = "#16213e"
ACCENT = "#e94560"
TEXT_COLOR = "#eaeaea"

plt.rcParams.update({
    "figure.facecolor": DARK_BG,
    "axes.facecolor": CARD_BG,
    "axes.edgecolor": "#444",
    "axes.labelcolor": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "text.color": TEXT_COLOR,
    "legend.facecolor": CARD_BG,
    "legend.edgecolor": "#444",
    "grid.color": "#2a2a4a",
    "grid.linewidth": 0.5,
    "font.family": "DejaVu Sans",
    "font.size": 11,
})


def savefig(name: str):
    path = os.path.join(CHARTS_DIR, name)
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close("all")
    print(f"  ✓ Saved: {name}")


# ─────────────────────────────────────────────
# 1. Revenue Trend + 7-day & 30-day MA
# ─────────────────────────────────────────────

def plot_revenue_trend(daily: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.fill_between(daily["date"], daily["revenue"], alpha=0.15, color=ACCENT)
    ax.plot(daily["date"], daily["revenue"], color="#aaa", linewidth=0.6, alpha=0.6, label="Daily Revenue")
    ax.plot(daily["date"], daily["ma_7"], color="#f7b731", linewidth=1.5, label="7-Day MA")
    ax.plot(daily["date"], daily["ma_30"], color=ACCENT, linewidth=2.2, label="30-Day MA")
    ax.set_title("Revenue Trend Over Time", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Date")
    ax.set_ylabel("Revenue ($)")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.4)
    fig.tight_layout()
    savefig("01_revenue_trend.png")


# ─────────────────────────────────────────────
# 2. Category Revenue (Horizontal Bar)
# ─────────────────────────────────────────────

def plot_category_revenue(cat_stats: pd.DataFrame):
    cat = cat_stats.sort_values("revenue", ascending=True).tail(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [ACCENT if i == len(cat) - 1 else "#5c7cfa" for i in range(len(cat))]
    bars = ax.barh(cat["category"], cat["revenue"] / 1e6, color=colors, edgecolor="none", height=0.65)
    for bar, val in zip(bars, cat["revenue"]):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"${val/1e6:.2f}M", va="center", fontsize=9, color=TEXT_COLOR)
    ax.set_title("Category-Wise Revenue", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Revenue (Millions $)")
    ax.set_ylabel("Category")
    ax.grid(True, axis="x", alpha=0.4)
    fig.tight_layout()
    savefig("02_category_revenue.png")


# ─────────────────────────────────────────────
# 3. Region Heatmap (Month × Region)
# ─────────────────────────────────────────────

def plot_region_heatmap(df: pd.DataFrame):
    pivot = df.pivot_table(index="month_label", columns="region", values="revenue", aggfunc="sum")
    pivot = pivot.iloc[-18:]  # last 18 months
    pivot = pivot / 1e3  # to thousands

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.heatmap(
        pivot, ax=ax, cmap="YlOrRd", fmt=".0f", annot=True,
        linewidths=0.4, linecolor="#333",
        cbar_kws={"label": "Revenue ($K)", "shrink": 0.7},
    )
    ax.set_title("Region × Month Revenue Heatmap ($K)", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Region")
    ax.set_ylabel("Month")
    plt.xticks(rotation=0)
    plt.yticks(rotation=0)
    fig.tight_layout()
    savefig("03_region_heatmap.png")


# ─────────────────────────────────────────────
# 4. RFM Customer Segmentation (Donut Chart)
# ─────────────────────────────────────────────

def plot_rfm_segments(rfm: pd.DataFrame):
    seg_counts = rfm["rfm_segment"].value_counts()
    colors = ["#e94560", "#f7b731", "#5c7cfa", "#20bf6b", "#fd9644", "#a55eea", "#45aaf2"]
    fig, ax = plt.subplots(figsize=(9, 7))
    wedges, texts, autotexts = ax.pie(
        seg_counts.values, labels=seg_counts.index, autopct="%1.1f%%",
        colors=colors[:len(seg_counts)], startangle=140,
        wedgeprops={"edgecolor": DARK_BG, "linewidth": 2},
        pctdistance=0.75,
    )
    for t in autotexts:
        t.set_fontsize(9)
        t.set_color("white")
    # Donut hole
    centre_circle = plt.Circle((0, 0), 0.5, fc=DARK_BG)
    ax.add_patch(centre_circle)
    ax.set_title("Customer RFM Segmentation Distribution", fontsize=15, fontweight="bold", pad=20)
    ax.text(0, 0, f"{len(rfm):,}\nCustomers", ha="center", va="center",
            fontsize=12, color=TEXT_COLOR, fontweight="bold")
    fig.tight_layout()
    savefig("04_rfm_segments.png")


# ─────────────────────────────────────────────
# 5. Return Rate by Category
# ─────────────────────────────────────────────

def plot_return_rate(cat_stats: pd.DataFrame):
    cat = cat_stats.sort_values("return_rate_pct", ascending=False)
    colors = [ACCENT if r > cat_stats["return_rate_pct"].mean() * 1.2 else "#5c7cfa"
              for r in cat["return_rate_pct"]]
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(cat["category"], cat["return_rate_pct"], color=colors, edgecolor="none", width=0.6)
    mean_rate = cat_stats["return_rate_pct"].mean()
    ax.axhline(mean_rate, color="#f7b731", linewidth=1.5, linestyle="--", label=f"Avg: {mean_rate:.1f}%")
    for bar, val in zip(bars, cat["return_rate_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=9, color=TEXT_COLOR)
    ax.set_title("Return Rate by Category", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Category")
    ax.set_ylabel("Return Rate (%)")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.4)
    plt.xticks(rotation=15, ha="right")
    fig.tight_layout()
    savefig("05_return_rate.png")


# ─────────────────────────────────────────────
# 6. Profit vs Revenue (Scatter by Category)
# ─────────────────────────────────────────────

def plot_profit_vs_revenue(cat_stats: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 7))
    scatter_colors = sns.color_palette("husl", len(cat_stats))
    for i, (_, row) in enumerate(cat_stats.iterrows()):
        ax.scatter(row["revenue"] / 1e6, row["profit"] / 1e6,
                   s=row["orders"] / 5, color=scatter_colors[i],
                   alpha=0.85, edgecolors="white", linewidths=0.5, zorder=3)
        ax.annotate(row["category"], (row["revenue"] / 1e6, row["profit"] / 1e6),
                    textcoords="offset points", xytext=(8, 4), fontsize=8, color=TEXT_COLOR)
    ax.set_title("Profit vs Revenue by Category\n(Bubble size = Order Count)",
                 fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Total Revenue (Millions $)")
    ax.set_ylabel("Total Profit (Millions $)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    savefig("06_profit_vs_revenue.png")


# ─────────────────────────────────────────────
# 7. Cohort Retention Heatmap
# ─────────────────────────────────────────────

def plot_cohort_retention(cohort: pd.DataFrame):
    cohort_display = cohort.astype(float)
    cohort_str = cohort_display.index.astype(str).tolist()
    fig, ax = plt.subplots(figsize=(14, max(6, len(cohort_display) * 0.4)))
    mask = cohort_display == 0
    sns.heatmap(
        cohort_display, ax=ax, mask=mask,
        cmap="Blues", fmt=".0f", annot=True,
        linewidths=0.3, linecolor="#333",
        cbar_kws={"label": "Retention %", "shrink": 0.7},
        vmin=0, vmax=100,
    )
    ax.set_yticklabels(cohort_str, rotation=0, fontsize=8)
    ax.set_title("Customer Cohort Retention (%)", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Months Since First Purchase")
    ax.set_ylabel("Cohort Month")
    fig.tight_layout()
    savefig("07_cohort_retention.png")


# ─────────────────────────────────────────────
# 8. Anomaly Detection Timeline
# ─────────────────────────────────────────────

def plot_anomalies(daily: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(14, 5))
    normal = daily[daily["anomaly_type"] == "Normal"]
    spikes = daily[daily["anomaly_type"] == "Spike"]
    drops = daily[daily["anomaly_type"] == "Drop"]

    ax.plot(daily["date"], daily["ma_30"], color="#5c7cfa", linewidth=1.5, label="30-Day MA", zorder=2)
    ax.scatter(normal["date"], normal["revenue"], color="#aaa", s=8, alpha=0.3, label="Normal", zorder=1)
    ax.scatter(spikes["date"], spikes["revenue"], color="#f7b731", s=60, marker="^",
               label=f"Spikes ({len(spikes)})", zorder=3, edgecolors="white", linewidths=0.5)
    ax.scatter(drops["date"], drops["revenue"], color=ACCENT, s=60, marker="v",
               label=f"Drops ({len(drops)})", zorder=3, edgecolors="white", linewidths=0.5)

    ax.set_title("Revenue Anomaly Detection (Z-Score Method)", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Date")
    ax.set_ylabel("Daily Revenue ($)")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    savefig("08_anomaly_detection.png")


# ─────────────────────────────────────────────
# 9. Revenue Forecast (ARIMA)
# ─────────────────────────────────────────────

def plot_forecast(monthly: pd.DataFrame, forecast: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(14, 5))

    # Historical
    ax.plot(monthly["month_label"], monthly["revenue"] / 1e6,
            color="#5c7cfa", linewidth=2, marker="o", markersize=4, label="Historical Revenue")

    # Forecast
    x_forecast = list(range(len(monthly), len(monthly) + len(forecast)))
    x_historical = list(range(len(monthly)))
    # Make a continuous x-axis using labels
    all_labels = list(monthly["month_label"]) + list(forecast["month_label"])
    ax.plot(forecast["month_label"], forecast["forecast_revenue"] / 1e6,
            color="#f7b731", linewidth=2, linestyle="--", marker="D",
            markersize=5, label=f"Forecast ({forecast['method'].iloc[0]})")
    ax.fill_between(forecast["month_label"],
                    forecast["lower_ci"] / 1e6, forecast["upper_ci"] / 1e6,
                    alpha=0.2, color="#f7b731", label="80% CI")

    ax.set_title("6-Month Revenue Forecast", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (Millions $)")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    # Show only every 3rd x-label for clarity
    all_x = list(monthly["month_label"]) + list(forecast["month_label"])
    tick_positions = list(range(0, len(all_x), 3))
    ax.set_xticks([all_x[i] for i in tick_positions if i < len(all_x)])
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    savefig("09_revenue_forecast.png")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("VISUALIZATION LAYER — Generating Charts")
    print("=" * 60)

    df = pd.read_parquet(os.path.join(PROCESSED_DIR, "fact_final.parquet"))
    df["date"] = pd.to_datetime(df["date"])
    daily = pd.read_parquet(os.path.join(PROCESSED_DIR, "daily_revenue.parquet"))
    daily["date"] = pd.to_datetime(daily["date"])
    monthly = pd.read_parquet(os.path.join(PROCESSED_DIR, "monthly_revenue.parquet"))
    forecast = pd.read_parquet(os.path.join(PROCESSED_DIR, "forecast.parquet"))
    cohort = pd.read_parquet(os.path.join(PROCESSED_DIR, "cohort_retention.parquet"))
    cat_stats = pd.read_parquet(os.path.join(PROCESSED_DIR, "category_stats.parquet"))
    rfm = pd.read_parquet(os.path.join(PROCESSED_DIR, "rfm.parquet"))

    plot_revenue_trend(daily)
    plot_category_revenue(cat_stats)
    plot_region_heatmap(df)
    plot_rfm_segments(rfm)
    plot_return_rate(cat_stats)
    plot_profit_vs_revenue(cat_stats)
    plot_cohort_retention(cohort)
    plot_anomalies(daily)
    plot_forecast(monthly, forecast)

    print("\n✅ All charts saved to outputs/charts/")
    print("=" * 60)


if __name__ == "__main__":
    main()
