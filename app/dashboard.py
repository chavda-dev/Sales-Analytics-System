"""
dashboard.py — Interactive Streamlit Dashboard
5-tab business intelligence dashboard with sidebar filters,
KPI cards, Plotly interactive charts, and auto-generated insights.
"""

import os
import sys
import warnings
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")

# Add scripts to import path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

# ─── Page configuration ───────────────────────
st.set_page_config(
    page_title="Sales Analytics System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* ── App background ── */
    .stApp { background-color: #0e1117; }
    .main .block-container { padding-top: 1.5rem; max-width: 100%; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: #1a1f2e;
        border-right: 1px solid #2a2f3e;
    }
    .sidebar-label {
        color: #4f8ef7;
        font-size: 0.62rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2.5px;
        margin: 1.1rem 0 0.3rem 0;
        display: block;
    }

    /* ── KPI Cards ── */
    .kpi-card {
        background: #1a1f2e;
        border-radius: 12px;
        padding: 18px 16px 14px 16px;
        border-left: 4px solid #4f8ef7;
        box-shadow: 0 4px 24px rgba(0,0,0,0.35);
        min-height: 110px;
    }
    .kpi-label {
        color: #8892a4;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.8px;
        margin-bottom: 8px;
    }
    .kpi-value {
        color: #f0f4ff;
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 6px;
    }
    .kpi-delta {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 3px 9px;
        border-radius: 999px;
        display: inline-block;
    }
    .kpi-delta.positive { color: #22c55e; background: rgba(34,197,94,0.12); }
    .kpi-delta.negative { color: #ef4444; background: rgba(239,68,68,0.12); }

    /* ── Section headers ── */
    .sec-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 1.6rem 0 0.8rem 0;
    }
    .sec-header-icon { font-size: 1.1rem; }
    .sec-header-title {
        color: #f0f4ff;
        font-size: 1.0rem;
        font-weight: 600;
        white-space: nowrap;
    }
    .sec-header-line {
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, #4f8ef7 0%, rgba(79,142,247,0) 100%);
    }

    /* ── Insight cards ── */
    .ins-card {
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        font-size: 0.92rem;
        line-height: 1.65;
        border-left: 4px solid transparent;
    }
    .ins-card.info {
        background: rgba(79,142,247,0.07);
        border-left-color: #4f8ef7;
        color: #c5d5ee;
    }
    .ins-card.positive {
        background: rgba(34,197,94,0.07);
        border-left-color: #22c55e;
        color: #c0e8ce;
    }
    .ins-card.warning {
        background: rgba(251,146,60,0.07);
        border-left-color: #fb923c;
        color: #eeddc8;
    }

    /* ── Tabs (pill style) ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
        background: #1a1f2e;
        border-radius: 12px;
        padding: 5px 6px;
        border: 1px solid #2a2f3e;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #8892a4;
        font-size: 0.83rem;
        font-weight: 500;
        padding: 6px 14px;
        border: none;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(79,142,247,0.1);
        color: #c8d8f0;
    }
    .stTabs [aria-selected="true"] {
        background: #4f8ef7 !important;
        color: #ffffff !important;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }

    /* ── DataFrames ── */
    [data-testid="stDataFrame"] {
        border: 1px solid #2a2f3e;
        border-radius: 12px;
        overflow: hidden;
    }

    /* ── General ── */
    hr { border-color: #2a2f3e !important; }
    h1, h2, h3 { color: #f0f4ff !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #0e1117; }
    ::-webkit-scrollbar-thumb { background: #4f8ef7; border-radius: 4px; }

    /* ── Select / multiselect ── */
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background-color: #252b3b !important;
        border-color: #2a2f3e !important;
        border-radius: 8px !important;
    }

    /* ── Empty state ── */
    .empty-state {
        text-align: center;
        padding: 40px 20px;
        color: #8892a4;
        background: #1a1f2e;
        border-radius: 12px;
        border: 1px dashed #2a2f3e;
        margin: 8px 0;
    }
    .empty-state-icon { font-size: 2.2rem; margin-bottom: 10px; }
    .empty-state-text { font-size: 0.92rem; }
</style>
""", unsafe_allow_html=True)

# ─── Plotly dark theme ─────────────────────────
PLOTLY_DARK = {
    "plot_bgcolor": "#1a1f2e",
    "paper_bgcolor": "#1a1f2e",
    "font": {"color": "#e0e0e0", "family": "Inter, system-ui, sans-serif"},
    "xaxis": {"gridcolor": "#2a2f3e", "linecolor": "#2a2f3e", "zerolinecolor": "#2a2f3e"},
    "yaxis": {"gridcolor": "#2a2f3e", "linecolor": "#2a2f3e", "zerolinecolor": "#2a2f3e"},
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


@st.cache_resource
def run_pipeline_if_needed():
    """Auto-run the pipeline if processed files are missing.
    Enables zero-config cloud deployment - the app self-bootstraps on first launch.
    Takes ~60 seconds on first boot, then results are cached.
    """
    missing = check_data_ready()
    if not missing:
        return "ready"

    import importlib.util

    def run_script(script_name):
        path = os.path.join(BASE_DIR, "scripts", script_name)
        spec = importlib.util.spec_from_file_location("mod", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()

    for step in ["ingestion.py", "cleaning.py", "transformation.py",
                 "db_loader.py", "analytics.py"]:
        run_script(step)
    return "ready"


# ─────────────────────────────────────────────
# UI Helpers
# ─────────────────────────────────────────────

def kpi_card(label: str, value: str, delta: str = None, delta_good: bool = True):
    delta_html = ""
    if delta:
        is_good = (delta_good and not delta.startswith("-")) or (not delta_good and delta.startswith("-"))
        delta_class = "positive" if is_good else "negative"
        arrow = "▲" if not delta.startswith("-") else "▼"
        delta_html = f'<span class="kpi-delta {delta_class}">{arrow} {delta}</span>'
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def section_header(icon: str, title: str):
    st.markdown(f"""
    <div class="sec-header">
        <span class="sec-header-icon">{icon}</span>
        <span class="sec-header-title">{title}</span>
        <div class="sec-header-line"></div>
    </div>
    """, unsafe_allow_html=True)


def empty_state(message: str = "No data matches the selected filters."):
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <div class="empty-state-text">{message}</div>
    </div>
    """, unsafe_allow_html=True)


def insight_card(text: str, kind: str = "info"):
    """kind: 'info' | 'positive' | 'warning'"""
    st.markdown(f'<div class="ins-card {kind}">{text}</div>', unsafe_allow_html=True)


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
    # ─── Header ───────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 12px 0;">
        <h1 style="font-size:2.2rem; background:linear-gradient(90deg,#4f8ef7,#a78bfa);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;
            font-weight:800; margin:0; letter-spacing:-0.5px;">
            Sales Analytics System
        </h1>
        <p style="color:#8892a4; font-size:0.92rem; margin-top:6px; letter-spacing:0.3px;">
            End-to-End Business Intelligence &nbsp;·&nbsp; Real-Time Insights &nbsp;·&nbsp; 3 Years of Data
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Auto-bootstrap pipeline on first launch
    if check_data_ready():
        with st.spinner("Initializing data pipeline for the first time... (~60 seconds)"):
            run_pipeline_if_needed()
        st.rerun()

    with st.spinner("Loading analytics data..."):
        fact, daily, monthly, forecast, cohort, cat_stats, region_stats, rfm = load_all_data()

    # ─── Sidebar Filters ──────────────────────
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding-bottom:14px; border-bottom:1px solid #2a2f3e;">
            <span style="font-size:1.4rem;">📊</span>
            <div style="color:#f0f4ff; font-weight:600; font-size:0.95rem; margin-top:4px;">
                Dashboard Filters
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<span class="sidebar-label">Date Range</span>', unsafe_allow_html=True)
        min_date = fact["date"].min().date()
        max_date = fact["date"].max().date()
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            label_visibility="collapsed",
        )

        st.markdown('<span class="sidebar-label">Geography</span>', unsafe_allow_html=True)
        all_regions = sorted(fact["region"].dropna().unique())
        sel_regions = st.multiselect("Region", all_regions, default=all_regions,
                                     label_visibility="collapsed")

        st.markdown('<span class="sidebar-label">Category</span>', unsafe_allow_html=True)
        all_cats = sorted(fact["category"].dropna().unique())
        sel_cats = st.multiselect("Category", all_cats, default=all_cats,
                                  label_visibility="collapsed")

        all_segments = sorted(fact["cust_segment"].dropna().unique()) if "cust_segment" in fact.columns else []
        if all_segments:
            st.markdown('<span class="sidebar-label">Customer Segment</span>', unsafe_allow_html=True)
            sel_segments = st.multiselect("Segment", all_segments, default=all_segments,
                                          label_visibility="collapsed")
        else:
            sel_segments = []

        st.markdown('<div style="border-top:1px solid #2a2f3e; margin:14px 0 10px 0;"></div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div style="color:#8892a4; font-size:0.75rem; line-height:2;">
            <div>📅 <span style="color:#c8d8f0;">{min_date} → {max_date}</span></div>
            <div>📋 <span style="color:#c8d8f0;">{len(fact):,} total records</span></div>
        </div>
        """, unsafe_allow_html=True)

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
        empty_state("No data matches your current filter selections. "
                    "Try broadening the date range or selecting more categories.")
        st.stop()

    kpis = compute_kpis(filt)

    # ─── KPI Cards ────────────────────────────
    section_header("📈", "Key Performance Indicators")
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

    st.markdown("<div style='margin-bottom:0.5rem'></div>", unsafe_allow_html=True)

    # ─── Tabs ─────────────────────────────────
    tabs = st.tabs(["📈  Overview", "👥  Customers", "📦  Products",
                    "⚠️  Anomalies & Forecast", "💡  Insights"])

    # ══════════════════════════════════════════
    # TAB 1 — Overview
    # ══════════════════════════════════════════
    with tabs[0]:
        col1, col2 = st.columns([3, 2])

        with col1:
            section_header("📉", "Revenue Trend")
            d_filt = daily.copy()
            if len(date_range) == 2:
                d_filt = d_filt[(d_filt["date"].dt.date >= date_range[0]) &
                                (d_filt["date"].dt.date <= date_range[1])]
            if d_filt.empty:
                empty_state("No revenue data for the selected date range.")
            else:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=d_filt["date"], y=d_filt["revenue"],
                    fill="tozeroy", fillcolor="rgba(79,142,247,0.08)",
                    line=dict(color="#4f8ef7", width=0.8), name="Daily", opacity=0.7))
                fig.add_trace(go.Scatter(
                    x=d_filt["date"], y=d_filt["ma_7"],
                    line=dict(color="#f7b731", width=1.5), name="7-Day MA"))
                fig.add_trace(go.Scatter(
                    x=d_filt["date"], y=d_filt["ma_30"],
                    line=dict(color="#a78bfa", width=2.2), name="30-Day MA"))
                fig.update_layout(**PLOTLY_DARK, height=320,
                                  margin=dict(l=10, r=10, t=20, b=10),
                                  legend=dict(orientation="h", y=-0.15))
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            section_header("🌍", "Revenue by Region")
            reg_filt = (filt.groupby("region")["revenue"].sum()
                        .reset_index().sort_values("revenue", ascending=False))
            if reg_filt.empty:
                empty_state("No region data available.")
            else:
                fig_pie = px.pie(reg_filt, values="revenue", names="region",
                                 color_discrete_sequence=px.colors.qualitative.Vivid, hole=0.45)
                fig_pie.update_layout(**PLOTLY_DARK, height=320,
                                      margin=dict(l=10, r=10, t=20, b=10),
                                      showlegend=True, legend=dict(orientation="h", y=-0.1))
                fig_pie.update_traces(textinfo="label+percent", textfont_size=11)
                st.plotly_chart(fig_pie, use_container_width=True)

        section_header("📦", "Category Performance")
        cat_filt = filt.groupby("category").agg(
            revenue=("revenue", "sum"), profit=("profit", "sum")
        ).reset_index().sort_values("revenue", ascending=False)
        if cat_filt.empty:
            empty_state("No category data for the selected filters.")
        else:
            fig_cat = go.Figure()
            fig_cat.add_trace(go.Bar(x=cat_filt["category"], y=cat_filt["revenue"] / 1e6,
                                     name="Revenue ($M)", marker_color="#4f8ef7"))
            fig_cat.add_trace(go.Bar(x=cat_filt["category"], y=cat_filt["profit"] / 1e6,
                                     name="Profit ($M)", marker_color="#22c55e"))
            fig_cat.update_layout(**PLOTLY_DARK, height=350, barmode="group",
                                   margin=dict(l=10, r=10, t=20, b=10),
                                   legend=dict(orientation="h", y=-0.15),
                                   xaxis_title="Category", yaxis_title="Amount ($M)")
            st.plotly_chart(fig_cat, use_container_width=True)

        section_header("🗺️", "Region × Month Revenue Heatmap")
        if "region" in filt.columns:
            heat_data = filt.pivot_table(index="month_label", columns="region",
                                         values="revenue", aggfunc="sum").fillna(0)
            heat_data = heat_data.iloc[-18:]
            if heat_data.empty:
                empty_state("No heatmap data available.")
            else:
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
            section_header("🎯", "RFM Customer Segments")
            rfm_counts = rfm["rfm_segment"].value_counts().reset_index()
            rfm_counts.columns = ["segment", "count"]
            if rfm_counts.empty:
                empty_state("No RFM segment data available.")
            else:
                fig_rfm = px.pie(rfm_counts, values="count", names="segment",
                                 color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.4)
                fig_rfm.update_layout(**PLOTLY_DARK, height=380,
                                      margin=dict(l=5, r=5, t=20, b=5))
                st.plotly_chart(fig_rfm, use_container_width=True)

        with col2:
            section_header("💎", "CLV Segment Distribution")
            clv_seg = filt.groupby("clv_segment").agg(
                customers=("customer_id", "nunique"),
                revenue=("revenue", "sum"),
            ).reset_index()
            if clv_seg.empty:
                empty_state("No CLV segment data available.")
            else:
                fig_clv = px.bar(clv_seg, x="clv_segment", y="revenue", color="clv_segment",
                                 text=clv_seg["customers"].apply(lambda x: f"{x:,} customers"),
                                 color_discrete_sequence=["#ef4444", "#f7b731", "#22c55e"])
                fig_clv.update_layout(**PLOTLY_DARK, height=380, showlegend=False,
                                      margin=dict(l=5, r=5, t=20, b=5),
                                      xaxis_title="CLV Segment", yaxis_title="Revenue ($)")
                st.plotly_chart(fig_clv, use_container_width=True)

        section_header("🔄", "Customer Cohort Retention (%)")
        cohort_vals = cohort.astype(float).head(18)
        cohort_vals.index = cohort_vals.index.astype(str)
        if cohort_vals.empty:
            empty_state("No cohort data available.")
        else:
            fig_cohort2 = px.imshow(cohort_vals, text_auto=".0f",
                                    color_continuous_scale="Blues",
                                    labels=dict(color="Retention %"),
                                    zmin=0, zmax=100)
            fig_cohort2.update_layout(**PLOTLY_DARK, height=450,
                                      margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_cohort2, use_container_width=True)

        section_header("🏆", "Top Customers by Revenue")
        top_custs = filt.groupby("customer_id").agg(
            revenue=("revenue", "sum"),
            orders=("order_id", "nunique"),
            rfm_segment=("rfm_segment", "first"),
            clv_segment=("clv_segment", "first"),
        ).reset_index().nlargest(15, "revenue")
        if top_custs.empty:
            empty_state("No customer data for the selected filters.")
        else:
            top_custs["revenue"] = top_custs["revenue"].apply(lambda x: f"${x:,.0f}")
            st.dataframe(top_custs, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════
    # TAB 3 — Products
    # ══════════════════════════════════════════
    with tabs[2]:
        col1, col2 = st.columns(2)

        with col1:
            section_header("💹", "Profit vs Revenue by Category")
            cat_bubble = filt.groupby("category").agg(
                revenue=("revenue", "sum"),
                profit=("profit", "sum"),
                orders=("order_id", "nunique"),
            ).reset_index()
            if cat_bubble.empty:
                empty_state("No category data for the selected filters.")
            else:
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
            section_header("🔁", "Return Rate by Category")
            cat_ret = filt.groupby("category").agg(
                returns=("return_flag", "sum"),
                total=("return_flag", "count"),
            ).reset_index()
            cat_ret["return_rate"] = (cat_ret["returns"] / cat_ret["total"] * 100).round(2)
            cat_ret = cat_ret.sort_values("return_rate", ascending=True)
            if cat_ret.empty:
                empty_state("No return rate data available.")
            else:
                mean_rr = cat_ret["return_rate"].mean()
                colors = ["#ef4444" if r > mean_rr else "#4f8ef7" for r in cat_ret["return_rate"]]
                fig_rr = go.Figure(go.Bar(
                    x=cat_ret["return_rate"], y=cat_ret["category"],
                    orientation="h", marker_color=colors,
                    text=cat_ret["return_rate"].apply(lambda x: f"{x:.1f}%"),
                    textposition="outside"))
                fig_rr.add_vline(x=mean_rr, line_color="#f7b731", line_dash="dash",
                                 annotation_text=f"Avg: {mean_rr:.1f}%")
                fig_rr.update_layout(**PLOTLY_DARK, height=420,
                                     margin=dict(l=10, r=10, t=10, b=10),
                                     xaxis_title="Return Rate (%)", yaxis_title="")
                st.plotly_chart(fig_rr, use_container_width=True)

        section_header("🔬", "Top 20 Products by Revenue")
        drill_cat = st.selectbox("Drill down by category:",
                                 ["All"] + sorted(filt["category"].dropna().unique()))
        prod_view = filt if drill_cat == "All" else filt[filt["category"] == drill_cat]
        top_products = prod_view.groupby("product_id").agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            units=("quantity", "sum"),
            orders=("order_id", "nunique"),
            category=("category", "first"),
            return_rate=("return_flag", "mean"),
        ).reset_index().nlargest(20, "revenue")
        if top_products.empty:
            empty_state("No products found for the selected category.")
        else:
            top_products["revenue"] = top_products["revenue"].apply(lambda x: f"${x:,.0f}")
            top_products["profit"] = top_products["profit"].apply(lambda x: f"${x:,.0f}")
            top_products["return_rate"] = top_products["return_rate"].apply(lambda x: f"{x*100:.1f}%")
            top_products["units"] = top_products["units"].apply(lambda x: f"{x:,.0f}")
            st.dataframe(top_products, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════
    # TAB 4 — Anomalies & Forecast
    # ══════════════════════════════════════════
    with tabs[3]:
        section_header("🔍", "Revenue Anomaly Detection (Z-Score Method)")
        d_anom = daily.copy()
        if len(date_range) == 2:
            d_anom = d_anom[(d_anom["date"].dt.date >= date_range[0]) &
                            (d_anom["date"].dt.date <= date_range[1])]

        if d_anom.empty:
            empty_state("No anomaly data for the selected date range.")
        else:
            normal = d_anom[d_anom["anomaly_type"] == "Normal"]
            spikes = d_anom[d_anom["anomaly_type"] == "Spike"]
            drops = d_anom[d_anom["anomaly_type"] == "Drop"]

            fig_anom = go.Figure()
            fig_anom.add_trace(go.Scatter(
                x=d_anom["date"], y=d_anom["ma_30"],
                line=dict(color="#4f8ef7", width=2), name="30-Day MA", zorder=2))
            fig_anom.add_trace(go.Scatter(
                x=normal["date"], y=normal["revenue"],
                mode="markers", marker=dict(color="#8892a4", size=4, opacity=0.3),
                name="Normal Days"))
            if not spikes.empty:
                fig_anom.add_trace(go.Scatter(
                    x=spikes["date"], y=spikes["revenue"], mode="markers",
                    marker=dict(color="#f7b731", size=10, symbol="triangle-up"),
                    name=f"Spikes ({len(spikes)})"))
            if not drops.empty:
                fig_anom.add_trace(go.Scatter(
                    x=drops["date"], y=drops["revenue"], mode="markers",
                    marker=dict(color="#ef4444", size=10, symbol="triangle-down"),
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

        st.markdown("<hr>", unsafe_allow_html=True)

        section_header("📈", "6-Month ARIMA Revenue Forecast")
        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(
            x=monthly["month_label"], y=monthly["revenue"] / 1e6,
            line=dict(color="#4f8ef7", width=2),
            mode="lines+markers", marker=dict(size=5),
            name="Historical Revenue ($M)"))
        fig_fc.add_trace(go.Scatter(
            x=forecast["month_label"], y=forecast["forecast_revenue"] / 1e6,
            line=dict(color="#f7b731", width=2, dash="dash"),
            mode="lines+markers", marker=dict(symbol="diamond", size=8),
            name=f"Forecast ({forecast['method'].iloc[0]})"))
        fig_fc.add_trace(go.Scatter(
            x=list(forecast["month_label"]) + list(reversed(forecast["month_label"])),
            y=list(forecast["upper_ci"] / 1e6) + list(reversed(forecast["lower_ci"] / 1e6)),
            fill="toself", fillcolor="rgba(247,183,49,0.12)",
            line=dict(color="rgba(255,255,255,0)"), name="80% Confidence Interval"))
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
        section_header("💡", "Auto-Generated Business Insights")
        st.markdown(
            '<p style="color:#8892a4; font-size:0.85rem; margin-top:-8px; margin-bottom:16px;">'
            'Computed dynamically from the data — no hardcoded values.</p>',
            unsafe_allow_html=True)

        cat_filt_stats = filt.groupby("category").agg(
            revenue=("revenue", "sum"), profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            returns=("return_flag", "sum"), total_rows=("order_id", "count"),
        ).reset_index()
        if not cat_filt_stats.empty:
            cat_filt_stats["return_rate_pct"] = (
                cat_filt_stats["returns"] / cat_filt_stats["total_rows"] * 100).round(2)
            cat_filt_stats["revenue_share_pct"] = (
                cat_filt_stats["revenue"] / cat_filt_stats["revenue"].sum() * 100).round(2)
            cat_filt_stats["profit_margin_pct"] = (
                cat_filt_stats["profit"] / cat_filt_stats["revenue"] * 100).round(2)
            cat_filt_stats = cat_filt_stats.sort_values("revenue", ascending=False)

        reg_filt_stats = filt.groupby("region").agg(
            revenue=("revenue", "sum"), orders=("order_id", "nunique"),
        ).reset_index()
        if not reg_filt_stats.empty:
            reg_filt_stats["revenue_share_pct"] = (
                reg_filt_stats["revenue"] / reg_filt_stats["revenue"].sum() * 100).round(2)
            reg_filt_stats = reg_filt_stats.sort_values("revenue", ascending=False)

        monthly_filt = filt.groupby("month_label")["revenue"].sum().reset_index()
        monthly_filt = monthly_filt.sort_values("month_label")
        monthly_filt["prev"] = monthly_filt["revenue"].shift(1)
        monthly_filt["mom_growth"] = (
            (monthly_filt["revenue"] - monthly_filt["prev"]) / monthly_filt["prev"] * 100
        ).round(2)

        # Build typed insights: list of (html_text, kind)
        insights = []

        if not reg_filt_stats.empty:
            top_r = reg_filt_stats.iloc[0]
            insights.append((
                f"🌍 <strong>{top_r['region']}</strong> is the top-performing region, contributing "
                f"<strong>{top_r['revenue_share_pct']:.1f}%</strong> of total revenue "
                f"(${top_r['revenue']:,.0f}).",
                "positive"
            ))

        if not cat_filt_stats.empty:
            best = cat_filt_stats.iloc[0]
            insights.append((
                f"⭐ <strong>{best['category']}</strong> leads all categories with "
                f"<strong>${best['revenue']:,.0f}</strong> in revenue "
                f"(<strong>{best['revenue_share_pct']:.1f}%</strong> share) and a "
                f"<strong>{best['profit_margin_pct']:.1f}%</strong> profit margin.",
                "positive"
            ))
            worst_return = cat_filt_stats.loc[cat_filt_stats["return_rate_pct"].idxmax()]
            insights.append((
                f"🔄 <strong>{worst_return['category']}</strong> has the highest return rate at "
                f"<strong>{worst_return['return_rate_pct']:.1f}%</strong>, requiring quality "
                f"improvement focus.",
                "warning"
            ))
            best_margin = cat_filt_stats.loc[cat_filt_stats["profit_margin_pct"].idxmax()]
            insights.append((
                f"💰 <strong>{best_margin['category']}</strong> delivers the best profit margin of "
                f"<strong>{best_margin['profit_margin_pct']:.1f}%</strong> — highest profitability "
                f"per dollar sold.",
                "positive"
            ))

        insights.append((
            f"📊 Overall profit margin: <strong>{kpis['profit_margin']:.1f}%</strong> on "
            f"<strong>${kpis['total_revenue']/1e6:.2f}M</strong> total revenue from "
            f"<strong>{kpis['total_orders']:,}</strong> orders.",
            "info"
        ))
        insights.append((
            f"📦 Return rate stands at <strong>{kpis['return_rate']:.1f}%</strong> — "
            f"{'above industry average, needs attention' if kpis['return_rate'] > 15 else 'within acceptable range'}.",
            "warning" if kpis["return_rate"] > 15 else "info"
        ))
        insights.append((
            f"🛒 Average Order Value (AOV) is <strong>${kpis['aov']:.2f}</strong>, "
            f"reflecting {'strong' if kpis['aov'] > 200 else 'moderate'} basket sizes.",
            "info"
        ))

        monthly_valid = monthly_filt.dropna(subset=["mom_growth"])
        if not monthly_valid.empty:
            worst_m = monthly_valid.loc[monthly_valid["mom_growth"].idxmin()]
            best_m = monthly_valid.loc[monthly_valid["mom_growth"].idxmax()]
            insights.append((
                f"📉 Largest MoM revenue decline: <strong>{worst_m['mom_growth']:.1f}%</strong> in "
                f"<strong>{worst_m['month_label']}</strong> — potentially driven by seasonal effects.",
                "warning"
            ))
            insights.append((
                f"📈 Strongest MoM revenue growth: <strong>+{best_m['mom_growth']:.1f}%</strong> in "
                f"<strong>{best_m['month_label']}</strong> — a standout performance month.",
                "positive"
            ))

        mom_kind = "positive" if kpis["mom_growth"] >= 0 else "warning"
        insights.append((
            f"⚠️ Current MoM revenue trend: <strong>{kpis['mom_growth']:+.1f}%</strong> "
            f"vs previous month — "
            f"{'positive momentum' if kpis['mom_growth'] >= 0 else 'declining, investigate root cause'}.",
            mom_kind
        ))

        if "clv_segment" in filt.columns:
            high_val = filt[filt["clv_segment"] == "High Value"]
            if not high_val.empty:
                hv_rev_share = high_val["revenue"].sum() / filt["revenue"].sum() * 100
                hv_cust_share = high_val["customer_id"].nunique() / filt["customer_id"].nunique() * 100
                insights.append((
                    f"🏆 <strong>High Value</strong> customers ({hv_cust_share:.1f}% of base) generate "
                    f"<strong>{hv_rev_share:.1f}%</strong> of total revenue — classic Pareto pattern.",
                    "positive"
                ))

        for text, kind in insights:
            insight_card(text, kind)

        st.markdown(
            f'<p style="color:#8892a4; font-size:0.8rem; margin-top:12px;">'
            f'{len(insights)} insights generated from {len(filt):,} filtered records.</p>',
            unsafe_allow_html=True)

    # ─── Footer ───────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; color:#4a5568; font-size:0.78rem; padding:10px 0 20px 0;">
        Sales Analytics System &nbsp;·&nbsp; Built with Python, Pandas, SQLite, Streamlit &nbsp;·&nbsp;
        Data pipeline: Ingestion → Cleaning → Transformation → Analytics → Visualization
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
