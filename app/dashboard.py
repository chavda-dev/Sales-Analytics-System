"""
dashboard.py — Interactive Streamlit Dashboard
5-tab business intelligence dashboard with sidebar filters,
KPI cards, Plotly interactive charts, and auto-generated insights.
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

warnings.filterwarnings("ignore")

# Add scripts to import path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

# ─── Theme configuration ──────────────────────
st.set_page_config(
    page_title="Sales Analytics System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main { background-color: #0f0f1a; }
    
    .stApp { background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%); }
    
    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1e1e3f 0%, #16213e 100%);
        border: 1px solid #2a2a5a;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        transition: transform 0.2s ease;
    }
    .kpi-card:hover { transform: translateY(-3px); }
    .kpi-label { color: #8888cc; font-size: 0.78rem; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
    .kpi-value { color: #ffffff; font-size: 1.9rem; font-weight: 700; }
    .kpi-delta { font-size: 0.85rem; margin-top: 4px; }
    .kpi-delta.positive { color: #20bf6b; }
    .kpi-delta.negative { color: #e94560; }
    
    /* Insight cards */
    .insight-card {
        background: linear-gradient(135deg, #1e2a4a 0%, #162030 100%);
        border-left: 4px solid #5c7cfa;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
        font-size: 0.95rem;
        color: #ddeeff;
        box-shadow: 0 2px 12px rgba(0,0,0,0.2);
    }
    
    /* Sidebar */
    .css-1d391kg { background: #12122a; }
    
    /* Headings */
    h1, h2, h3 { color: #ffffff !important; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background: #1a1a2e; border-radius: 10px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 8px; color: #8888cc; }
    .stTabs [aria-selected="true"] { background: #5c7cfa !important; color: white !important; }
    
    /* Metric delta */
    [data-testid="stMetricDelta"] { font-size: 0.85rem; }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #1a1a2e; }
    ::-webkit-scrollbar-thumb { background: #5c7cfa; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

PLOTLY_DARK = {
    "plot_bgcolor": "#1e1e3f",
    "paper_bgcolor": "#16213e",
    "font": {"color": "#eaeaea"},
}


# ─────────────────────────────────────────────
# Data Loading
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_all_data():
    fact = pd.read_parquet(os.path.join(PROCESSED_DIR, "fact_final.parquet"))
    fact["date"] = pd.to_datetime(fact["date"])
    daily = pd.read_parquet(os.path.join(PROCESSED_DIR, "daily_revenue.parquet"))
    daily["date"] = pd.to_datetime(daily["date"])
    monthly = pd.read_parquet(os.path.join(PROCESSED_DIR, "monthly_revenue.parquet"))
    forecast = pd.read_parquet(os.path.join(PROCESSED_DIR, "forecast.parquet"))
    cohort = pd.read_parquet(os.path.join(PROCESSED_DIR, "cohort_retention.parquet"))
    cat_stats = pd.read_parquet(os.path.join(PROCESSED_DIR, "category_stats.parquet"))
    region_stats = pd.read_parquet(os.path.join(PROCESSED_DIR, "region_stats.parquet"))
    rfm = pd.read_parquet(os.path.join(PROCESSED_DIR, "rfm.parquet"))
    return fact, daily, monthly, forecast, cohort, cat_stats, region_stats, rfm


def check_data_ready():
    required = ["fact_final.parquet", "daily_revenue.parquet", "monthly_revenue.parquet",
                "forecast.parquet", "cohort_retention.parquet", "category_stats.parquet",
                "region_stats.parquet", "rfm.parquet"]
    missing = [f for f in required if not os.path.exists(os.path.join(PROCESSED_DIR, f))]
    return missing


# ─────────────────────────────────────────────
# KPI Card Helper
# ─────────────────────────────────────────────

def kpi_card(label: str, value: str, delta: str = None, delta_good: bool = True):
    delta_class = ""
    delta_html = ""
    if delta:
        is_good = (delta_good and not delta.startswith("-")) or (not delta_good and delta.startswith("-"))
        delta_class = "positive" if is_good else "negative"
        arrow = "▲" if not delta.startswith("-") else "▼"
        delta_html = f'<div class="kpi-delta {delta_class}">{arrow} {delta}</div>'
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# KPI Computation (filtered)
# ─────────────────────────────────────────────

def compute_kpis(df: pd.DataFrame) -> dict:
    total_revenue = df["revenue"].sum()
    total_profit = df["profit"].sum()
    total_orders = df["order_id"].nunique()
    aov = total_revenue / total_orders if total_orders else 0
    profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0
    return_rate = df["return_flag"].mean() * 100
    monthly = df.groupby("month_label")["revenue"].sum().sort_index()
    mom_growth = 0.0
    if len(monthly) >= 2:
        last, prev = monthly.iloc[-1], monthly.iloc[-2]
        mom_growth = ((last - prev) / prev * 100) if prev else 0
    return {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "total_orders": total_orders,
        "aov": aov,
        "profit_margin": profit_margin,
        "return_rate": return_rate,
        "mom_growth": mom_growth,
    }


# ─────────────────────────────────────────────
# Main Dashboard
# ─────────────────────────────────────────────

def main():
    # Header
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <h1 style="font-size: 2.4rem; background: linear-gradient(90deg, #5c7cfa, #e94560);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;">
            📊 Sales Analytics System
        </h1>
        <p style="color: #8888cc; font-size: 1rem; margin-top: -10px;">
            End-to-End Business Intelligence · Real-Time Insights · 3 Years of Data
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Data readiness check
    missing = check_data_ready()
    if missing:
        st.error(f"❌ Missing data files: {', '.join(missing)}")
        st.info("Run the pipeline first:\n```bash\npython scripts/ingestion.py\npython scripts/cleaning.py\npython scripts/transformation.py\npython scripts/db_loader.py\npython scripts/analytics.py\n```")
        st.stop()

    fact, daily, monthly, forecast, cohort, cat_stats, region_stats, rfm = load_all_data()

    # ─── Sidebar Filters ─────────────────────
    with st.sidebar:
        st.markdown("## 🎛️ Filters")
        st.markdown("---")

        min_date = fact["date"].min().date()
        max_date = fact["date"].max().date()
        date_range = st.date_input(
            "📅 Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        all_regions = sorted(fact["region"].dropna().unique())
        sel_regions = st.multiselect("🌍 Region", all_regions, default=all_regions)

        all_cats = sorted(fact["category"].dropna().unique())
        sel_cats = st.multiselect("📦 Category", all_cats, default=all_cats)

        all_segments = sorted(fact["cust_segment"].dropna().unique()) if "cust_segment" in fact.columns else []
        if all_segments:
            sel_segments = st.multiselect("👥 Customer Segment", all_segments, default=all_segments)
        else:
            sel_segments = []

        st.markdown("---")
        st.markdown(f"**Data Range:** {min_date} → {max_date}")
        st.markdown(f"**Total Records:** {len(fact):,}")

    # Apply filters
    filt = fact.copy()
    if len(date_range) == 2:
        filt = filt[(filt["date"].dt.date >= date_range[0]) & (filt["date"].dt.date <= date_range[1])]
    if sel_regions:
        filt = filt[filt["region"].isin(sel_regions)]
    if sel_cats:
        filt = filt[filt["category"].isin(sel_cats)]
    if sel_segments and "cust_segment" in filt.columns:
        filt = filt[filt["cust_segment"].isin(sel_segments)]

    if filt.empty:
        st.warning("⚠️ No data matches the selected filters. Please adjust your selections.")
        st.stop()

    kpis = compute_kpis(filt)

    # ─── KPI Cards ───────────────────────────
    st.markdown("### 📈 Key Performance Indicators")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Total Revenue", f"${kpis['total_revenue']/1e6:.2f}M",
                 f"{kpis['mom_growth']:+.1f}% MoM")
    with c2:
        kpi_card("Total Profit", f"${kpis['total_profit']/1e6:.2f}M")
    with c3:
        kpi_card("Profit Margin", f"{kpis['profit_margin']:.1f}%")
    with c4:
        kpi_card("Return Rate", f"{kpis['return_rate']:.1f}%",
                 f"{kpis['return_rate']:.1f}%", delta_good=False)
    with c5:
        kpi_card("Avg Order Value", f"${kpis['aov']:.0f}")

    st.markdown("---")

    # ─── Tabs ────────────────────────────────
    tabs = st.tabs(["📈 Overview", "👥 Customers", "📦 Products", "⚠️ Anomalies & Forecast", "💡 Insights"])

    # ══════════════════════════════════════════
    # TAB 1 — Overview
    # ══════════════════════════════════════════
    with tabs[0]:
        col1, col2 = st.columns([3, 2])

        with col1:
            st.subheader("Revenue Trend")
            # Filter daily to date range
            d_filt = daily.copy()
            if len(date_range) == 2:
                d_filt = d_filt[(d_filt["date"].dt.date >= date_range[0]) & (d_filt["date"].dt.date <= date_range[1])]
            if not d_filt.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=d_filt["date"], y=d_filt["revenue"],
                                         fill="tozeroy", fillcolor="rgba(92,124,250,0.1)",
                                         line=dict(color="#aaa", width=0.5), name="Daily", opacity=0.6))
                fig.add_trace(go.Scatter(x=d_filt["date"], y=d_filt["ma_7"],
                                         line=dict(color="#f7b731", width=1.5), name="7-Day MA"))
                fig.add_trace(go.Scatter(x=d_filt["date"], y=d_filt["ma_30"],
                                         line=dict(color="#e94560", width=2.2), name="30-Day MA"))
                fig.update_layout(**PLOTLY_DARK, height=320, margin=dict(l=10, r=10, t=20, b=10),
                                   legend=dict(orientation="h", y=-0.15))
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Revenue by Region")
            reg_filt = filt.groupby("region")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
            fig_pie = px.pie(reg_filt, values="revenue", names="region",
                             color_discrete_sequence=px.colors.qualitative.Vivid, hole=0.45)
            fig_pie.update_layout(**PLOTLY_DARK, height=320, margin=dict(l=10, r=10, t=20, b=10),
                                   showlegend=True, legend=dict(orientation="h", y=-0.1))
            fig_pie.update_traces(textinfo="label+percent", textfont_size=11)
            st.plotly_chart(fig_pie, use_container_width=True)

        # Category Bar
        st.subheader("Category Performance")
        cat_filt = filt.groupby("category").agg(
            revenue=("revenue", "sum"), profit=("profit", "sum")
        ).reset_index().sort_values("revenue", ascending=False)
        fig_cat = go.Figure()
        fig_cat.add_trace(go.Bar(x=cat_filt["category"], y=cat_filt["revenue"] / 1e6,
                                  name="Revenue ($M)", marker_color="#5c7cfa"))
        fig_cat.add_trace(go.Bar(x=cat_filt["category"], y=cat_filt["profit"] / 1e6,
                                  name="Profit ($M)", marker_color="#20bf6b"))
        fig_cat.update_layout(**PLOTLY_DARK, height=350, barmode="group",
                               margin=dict(l=10, r=10, t=20, b=10),
                               legend=dict(orientation="h", y=-0.15),
                               xaxis_title="Category", yaxis_title="Amount ($M)")
        st.plotly_chart(fig_cat, use_container_width=True)

        # Region × Month Heatmap
        st.subheader("Region × Month Revenue Heatmap")
        if "region" in filt.columns:
            heat_data = filt.pivot_table(index="month_label", columns="region",
                                          values="revenue", aggfunc="sum").fillna(0)
            heat_data = heat_data.iloc[-18:]
            fig_heat = px.imshow(heat_data / 1e3, text_auto=".0f",
                                  color_continuous_scale="Blues",
                                  labels=dict(color="Revenue ($K)"))
            fig_heat.update_layout(**PLOTLY_DARK, height=450,
                                    margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_heat, use_container_width=True)

    # ══════════════════════════════════════════
    # TAB 2 — Customers
    # ══════════════════════════════════════════
    with tabs[1]:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("RFM Customer Segments")
            rfm_counts = rfm["rfm_segment"].value_counts().reset_index()
            rfm_counts.columns = ["segment", "count"]
            fig_rfm = px.pie(rfm_counts, values="count", names="segment",
                              color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
            fig_rfm.update_layout(**PLOTLY_DARK, height=380, margin=dict(l=5, r=5, t=20, b=5))
            st.plotly_chart(fig_rfm, use_container_width=True)

        with col2:
            st.subheader("CLV Segment Distribution")
            clv_seg = filt.groupby("clv_segment").agg(
                customers=("customer_id", "nunique"),
                revenue=("revenue", "sum"),
            ).reset_index()
            fig_clv = px.bar(clv_seg, x="clv_segment", y="revenue", color="clv_segment",
                              text=clv_seg["customers"].apply(lambda x: f"{x:,} customers"),
                              color_discrete_sequence=["#e94560", "#f7b731", "#20bf6b"])
            fig_clv.update_layout(**PLOTLY_DARK, height=380, showlegend=False,
                                   margin=dict(l=5, r=5, t=20, b=5),
                                   xaxis_title="CLV Segment", yaxis_title="Revenue ($)")
            st.plotly_chart(fig_clv, use_container_width=True)

        st.subheader("Customer Cohort Retention (%)")
        cohort_display = cohort.astype(float).reset_index()
        cohort_display["cohort"] = cohort_display["cohort"].astype(str)
        cohort_melt = cohort_display.melt(id_vars="cohort", var_name="months_since",
                                           value_name="retention")
        fig_cohort = px.density_heatmap(cohort_melt, x="months_since", y="cohort",
                                          z="retention", histfunc="avg",
                                          color_continuous_scale="Blues")
        if not cohort_display.empty:
            cohort_vals = cohort.astype(float)
            fig_cohort2 = px.imshow(cohort_vals.head(18), text_auto=".0f",
                                     color_continuous_scale="Blues",
                                     labels=dict(color="Retention %"),
                                     zmin=0, zmax=100)
            fig_cohort2.update_layout(**PLOTLY_DARK, height=450,
                                       margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_cohort2, use_container_width=True)

        # Customer table
        st.subheader("Top Customers by Revenue")
        top_custs = filt.groupby("customer_id").agg(
            revenue=("revenue", "sum"),
            orders=("order_id", "nunique"),
            rfm_segment=("rfm_segment", "first"),
            clv_segment=("clv_segment", "first"),
        ).reset_index().nlargest(15, "revenue")
        top_custs["revenue"] = top_custs["revenue"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(top_custs, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════
    # TAB 3 — Products
    # ══════════════════════════════════════════
    with tabs[2]:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Profit vs Revenue by Category")
            cat_bubble = filt.groupby("category").agg(
                revenue=("revenue", "sum"),
                profit=("profit", "sum"),
                orders=("order_id", "nunique"),
            ).reset_index()
            fig_bubble = px.scatter(cat_bubble, x="revenue", y="profit",
                                     size="orders", color="category",
                                     text="category",
                                     color_discrete_sequence=px.colors.qualitative.Vivid,
                                     size_max=50)
            fig_bubble.update_traces(textposition="top center", textfont_size=9)
            fig_bubble.update_layout(**PLOTLY_DARK, height=420,
                                      margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
                                      xaxis_title="Revenue ($)", yaxis_title="Profit ($)")
            st.plotly_chart(fig_bubble, use_container_width=True)

        with col2:
            st.subheader("Return Rate by Category")
            cat_ret = filt.groupby("category").agg(
                returns=("return_flag", "sum"),
                total=("return_flag", "count"),
            ).reset_index()
            cat_ret["return_rate"] = (cat_ret["returns"] / cat_ret["total"] * 100).round(2)
            cat_ret = cat_ret.sort_values("return_rate", ascending=True)
            mean_rr = cat_ret["return_rate"].mean()
            colors = ["#e94560" if r > mean_rr else "#5c7cfa" for r in cat_ret["return_rate"]]
            fig_rr = go.Figure(go.Bar(x=cat_ret["return_rate"], y=cat_ret["category"],
                                       orientation="h", marker_color=colors,
                                       text=cat_ret["return_rate"].apply(lambda x: f"{x:.1f}%"),
                                       textposition="outside"))
            fig_rr.add_vline(x=mean_rr, line_color="#f7b731", line_dash="dash",
                              annotation_text=f"Avg: {mean_rr:.1f}%")
            fig_rr.update_layout(**PLOTLY_DARK, height=420,
                                  margin=dict(l=10, r=10, t=10, b=10),
                                  xaxis_title="Return Rate (%)", yaxis_title="")
            st.plotly_chart(fig_rr, use_container_width=True)

        # Top 20 products drill-down
        st.subheader("Top 20 Products by Revenue")
        drill_cat = st.selectbox("Drill down by category:", ["All"] + sorted(filt["category"].dropna().unique()))
        prod_view = filt if drill_cat == "All" else filt[filt["category"] == drill_cat]
        top_products = prod_view.groupby("product_id").agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            units=("quantity", "sum"),
            orders=("order_id", "nunique"),
            category=("category", "first"),
            return_rate=("return_flag", "mean"),
        ).reset_index().nlargest(20, "revenue")
        top_products["revenue"] = top_products["revenue"].apply(lambda x: f"${x:,.0f}")
        top_products["profit"] = top_products["profit"].apply(lambda x: f"${x:,.0f}")
        top_products["return_rate"] = top_products["return_rate"].apply(lambda x: f"{x*100:.1f}%")
        top_products["units"] = top_products["units"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(top_products, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════
    # TAB 4 — Anomalies & Forecast
    # ══════════════════════════════════════════
    with tabs[3]:
        # Anomaly Detection
        st.subheader("🔍 Revenue Anomaly Detection (Z-Score Method)")
        d_anom = daily.copy()
        if len(date_range) == 2:
            d_anom = d_anom[(d_anom["date"].dt.date >= date_range[0]) & (d_anom["date"].dt.date <= date_range[1])]

        if not d_anom.empty:
            normal = d_anom[d_anom["anomaly_type"] == "Normal"]
            spikes = d_anom[d_anom["anomaly_type"] == "Spike"]
            drops = d_anom[d_anom["anomaly_type"] == "Drop"]

            fig_anom = go.Figure()
            fig_anom.add_trace(go.Scatter(x=d_anom["date"], y=d_anom["ma_30"],
                                           line=dict(color="#5c7cfa", width=2),
                                           name="30-Day MA", zorder=2))
            fig_anom.add_trace(go.Scatter(x=normal["date"], y=normal["revenue"],
                                           mode="markers", marker=dict(color="#aaa", size=4, opacity=0.3),
                                           name="Normal Days"))
            if not spikes.empty:
                fig_anom.add_trace(go.Scatter(x=spikes["date"], y=spikes["revenue"],
                                               mode="markers",
                                               marker=dict(color="#f7b731", size=10, symbol="triangle-up"),
                                               name=f"Spikes ({len(spikes)})"))
            if not drops.empty:
                fig_anom.add_trace(go.Scatter(x=drops["date"], y=drops["revenue"],
                                               mode="markers",
                                               marker=dict(color="#e94560", size=10, symbol="triangle-down"),
                                               name=f"Drops ({len(drops)})"))

            fig_anom.update_layout(**PLOTLY_DARK, height=400,
                                    margin=dict(l=10, r=10, t=10, b=10),
                                    xaxis_title="Date", yaxis_title="Daily Revenue ($)",
                                    legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig_anom, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Anomalies", int(d_anom["is_anomaly"].sum()))
            col2.metric("Revenue Spikes", len(spikes))
            col3.metric("Revenue Drops", len(drops))

        st.markdown("---")

        # Forecast
        st.subheader("📈 6-Month ARIMA Revenue Forecast")
        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(x=monthly["month_label"], y=monthly["revenue"] / 1e6,
                                     line=dict(color="#5c7cfa", width=2),
                                     mode="lines+markers", marker=dict(size=5),
                                     name="Historical Revenue ($M)"))
        fig_fc.add_trace(go.Scatter(x=forecast["month_label"],
                                     y=forecast["forecast_revenue"] / 1e6,
                                     line=dict(color="#f7b731", width=2, dash="dash"),
                                     mode="lines+markers", marker=dict(symbol="diamond", size=8),
                                     name=f"Forecast ({forecast['method'].iloc[0]})"))
        fig_fc.add_trace(go.Scatter(
            x=list(forecast["month_label"]) + list(reversed(forecast["month_label"])),
            y=list(forecast["upper_ci"] / 1e6) + list(reversed(forecast["lower_ci"] / 1e6)),
            fill="toself", fillcolor="rgba(247,183,49,0.15)",
            line=dict(color="rgba(255,255,255,0)"), name="80% Confidence Interval"
        ))
        fig_fc.update_layout(**PLOTLY_DARK, height=420,
                              margin=dict(l=10, r=10, t=10, b=10),
                              xaxis_title="Month", yaxis_title="Revenue ($M)",
                              legend=dict(orientation="h", y=-0.15))
        fig_fc.update_xaxes(tickangle=30)
        st.plotly_chart(fig_fc, use_container_width=True)

        next_months = forecast[["month_label", "forecast_revenue", "lower_ci", "upper_ci"]].copy()
        next_months.columns = ["Month", "Forecast ($)", "Lower CI ($)", "Upper CI ($)"]
        for col in ["Forecast ($)", "Lower CI ($)", "Upper CI ($)"]:
            next_months[col] = next_months[col].apply(lambda x: f"${x:,.0f}")
        st.dataframe(next_months, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════
    # TAB 5 — Insights
    # ══════════════════════════════════════════
    with tabs[4]:
        st.subheader("💡 Auto-Generated Business Insights")
        st.markdown("*Computed dynamically from the data — no hardcoded values.*")
        st.markdown("")

        # Re-compute for filtered data
        cat_filt_stats = filt.groupby("category").agg(
            revenue=("revenue", "sum"), profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            returns=("return_flag", "sum"), total_rows=("order_id", "count"),
        ).reset_index()
        if not cat_filt_stats.empty:
            cat_filt_stats["return_rate_pct"] = (cat_filt_stats["returns"] / cat_filt_stats["total_rows"] * 100).round(2)
            cat_filt_stats["revenue_share_pct"] = (cat_filt_stats["revenue"] / cat_filt_stats["revenue"].sum() * 100).round(2)
            cat_filt_stats["profit_margin_pct"] = (cat_filt_stats["profit"] / cat_filt_stats["revenue"] * 100).round(2)
            cat_filt_stats = cat_filt_stats.sort_values("revenue", ascending=False)

        reg_filt_stats = filt.groupby("region").agg(
            revenue=("revenue", "sum"), orders=("order_id", "nunique"),
        ).reset_index()
        if not reg_filt_stats.empty:
            reg_filt_stats["revenue_share_pct"] = (reg_filt_stats["revenue"] / reg_filt_stats["revenue"].sum() * 100).round(2)
            reg_filt_stats = reg_filt_stats.sort_values("revenue", ascending=False)

        monthly_filt = filt.groupby("month_label")["revenue"].sum().reset_index()
        monthly_filt = monthly_filt.sort_values("month_label")
        monthly_filt["prev"] = monthly_filt["revenue"].shift(1)
        monthly_filt["mom_growth"] = ((monthly_filt["revenue"] - monthly_filt["prev"]) / monthly_filt["prev"] * 100).round(2)

        insights = []

        if not reg_filt_stats.empty:
            top_r = reg_filt_stats.iloc[0]
            insights.append(f"🌍 **{top_r['region']}** is the top-performing region, contributing "
                            f"**{top_r['revenue_share_pct']:.1f}%** of total revenue (${top_r['revenue']:,.0f}).")

        if not cat_filt_stats.empty:
            best = cat_filt_stats.iloc[0]
            insights.append(f"⭐ **{best['category']}** leads all categories with **${best['revenue']:,.0f}** "
                            f"in revenue (**{best['revenue_share_pct']:.1f}%** share) and a "
                            f"**{best['profit_margin_pct']:.1f}%** profit margin.")
            worst_return = cat_filt_stats.loc[cat_filt_stats["return_rate_pct"].idxmax()]
            insights.append(f"🔄 **{worst_return['category']}** has the highest return rate at "
                            f"**{worst_return['return_rate_pct']:.1f}%**, requiring quality improvement focus.")
            best_margin = cat_filt_stats.loc[cat_filt_stats["profit_margin_pct"].idxmax()]
            insights.append(f"💰 **{best_margin['category']}** delivers the best profit margin of "
                            f"**{best_margin['profit_margin_pct']:.1f}%** — highest profitability per dollar sold.")

        insights.append(f"📊 Overall profit margin: **{kpis['profit_margin']:.1f}%** on "
                        f"**${kpis['total_revenue']/1e6:.2f}M** total revenue from "
                        f"**{kpis['total_orders']:,}** orders.")
        insights.append(f"📦 Return rate stands at **{kpis['return_rate']:.1f}%** — "
                        f"{'above industry average, needs attention' if kpis['return_rate'] > 15 else 'within acceptable range'}.")
        insights.append(f"🛒 Average Order Value (AOV) is **${kpis['aov']:.2f}**, "
                        f"reflecting {'strong' if kpis['aov'] > 200 else 'moderate'} basket sizes.")

        monthly_valid = monthly_filt.dropna(subset=["mom_growth"])
        if not monthly_valid.empty:
            worst_m = monthly_valid.loc[monthly_valid["mom_growth"].idxmin()]
            best_m = monthly_valid.loc[monthly_valid["mom_growth"].idxmax()]
            insights.append(f"📉 Largest MoM revenue decline: **{worst_m['mom_growth']:.1f}%** in "
                            f"**{worst_m['month_label']}** — potentially driven by seasonal effects.")
            insights.append(f"📈 Strongest MoM revenue growth: **+{best_m['mom_growth']:.1f}%** in "
                            f"**{best_m['month_label']}** — a standout performance month.")

        insights.append(f"⚠️ Current MoM revenue trend: **{kpis['mom_growth']:+.1f}%** "
                        f"vs previous month — {'positive momentum' if kpis['mom_growth'] >= 0 else 'declining, investigate root cause'}.")

        # CLV insights
        if "clv_segment" in filt.columns:
            high_val = filt[filt["clv_segment"] == "High Value"]
            if not high_val.empty:
                hv_rev_share = high_val["revenue"].sum() / filt["revenue"].sum() * 100
                hv_cust_share = high_val["customer_id"].nunique() / filt["customer_id"].nunique() * 100
                insights.append(f"🏆 **High Value** customers ({hv_cust_share:.1f}% of base) generate "
                                f"**{hv_rev_share:.1f}%** of total revenue — classic Pareto pattern.")

        for ins in insights:
            st.markdown(f'<div class="insight-card">{ins}</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"*{len(insights)} insights generated from {len(filt):,} filtered records.*")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#555; font-size:0.8rem; padding:10px;">
        Sales Analytics System · Built with Python, Pandas, SQLite, Streamlit · 
        Data pipeline: Ingestion → Cleaning → Transformation → Analytics → Visualization
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
