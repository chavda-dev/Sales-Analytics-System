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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

st.set_page_config(
    page_title="Sales Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
# THEME
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800&display=swap');

/* ── CSS variables ── */
:root {
    --bg:     #07111f;
    --card:   #0c1a2e;
    --card2:  #0f2040;
    --bdr:    #182d4a;
    --bdr2:   #234069;
    --blue:   #3b82f6;
    --indigo: #6366f1;
    --purple: #a855f7;
    --green:  #10b981;
    --red:    #ef4444;
    --amber:  #f59e0b;
    --cyan:   #06b6d4;
    --t1:     #f0f6ff;
    --t2:     #8ba3c7;
    --t3:     #3d5475;
}

/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; }
html, body { background: var(--bg) !important; }
* { font-family: 'Inter', system-ui, -apple-system, sans-serif !important; }

/* ── Erase Streamlit chrome ── */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
#MainMenu, footer { display: none !important; }

/* ── App shell ── */
.stApp,
[data-testid="stAppViewContainer"],
.main, section.main,
.main > div { background: var(--bg) !important; }

.block-container {
    padding: 0 2rem 3rem !important;
    max-width: 100% !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] section,
[data-testid="stSidebar"] .block-container {
    background: var(--card) !important;
}
[data-testid="stSidebar"] {
    border-right: 1px solid var(--bdr) !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span:not([data-baseweb]) {
    color: var(--t2) !important;
    font-size: 0.82rem !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child {
    background: #060f1c !important;
    border: 1px solid var(--bdr) !important;
    border-radius: 8px !important;
    color: var(--t1) !important;
}
[data-testid="stSidebar"] [data-testid="stDateInput"] input,
[data-testid="stSidebar"] input {
    background: #060f1c !important;
    border: 1px solid var(--bdr) !important;
    border-radius: 8px !important;
    color: var(--t1) !important;
}
[data-baseweb="popover"] { background: var(--card2) !important; border-color: var(--bdr2) !important; }

/* ── Columns / blocks ── */
[data-testid="stVerticalBlock"] > div,
[data-testid="column"] { background: transparent !important; }

/* ── KPI cards ── */
.kpi {
    background: var(--card);
    border: 1px solid var(--bdr);
    border-radius: 14px;
    padding: 20px 18px 16px;
    position: relative;
    overflow: hidden;
    height: 130px;
}
.kpi::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: var(--kc, var(--blue));
    border-radius: 14px 14px 0 0;
}
.kpi-ico {
    position: absolute;
    top: 14px; right: 16px;
    font-size: 1.2rem;
    opacity: 0.18;
}
.kpi-lbl {
    color: var(--t2);
    font-size: 0.64rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.6px;
    margin-bottom: 9px;
}
.kpi-val {
    color: var(--t1);
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: -1px;
    line-height: 1;
    margin-bottom: 9px;
}
.kpi-bdg {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 3px 7px;
    border-radius: 5px;
}
.kpi-bdg.pos { background: rgba(16,185,129,.14); color: #34d399; }
.kpi-bdg.neg { background: rgba(239,68,68,.14);  color: #f87171; }

/* ── Section header ── */
.shdr {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 2rem 0 0.85rem;
    padding-bottom: 0;
}
.shdr-bar {
    width: 3px; height: 17px;
    background: var(--blue);
    border-radius: 2px;
    flex-shrink: 0;
    box-shadow: 0 0 8px rgba(59,130,246,.5);
}
.shdr-txt { color: var(--t1); font-size: 0.9rem; font-weight: 700; }
.shdr-line { flex: 1; height: 1px; background: var(--bdr); margin-left: 6px; }
.shdr-badge {
    margin-left: auto;
    color: var(--t3);
    font-size: 0.68rem;
    font-weight: 500;
    white-space: nowrap;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--card) !important;
    border: 1px solid var(--bdr) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 3px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-radius: 7px !important;
    color: var(--t3) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 7px 14px !important;
    transition: color .15s !important;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(59,130,246,.1) !important;
    color: #93c5fd !important;
}
.stTabs [aria-selected="true"] {
    background: var(--blue) !important;
    color: #fff !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 12px rgba(59,130,246,.4) !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── DataFrames ── */
[data-testid="stDataFrame"] > div {
    background: var(--card) !important;
    border: 1px solid var(--bdr) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] th {
    background: var(--card2) !important;
    color: var(--t2) !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
[data-testid="stDataFrame"] td { color: var(--t1) !important; font-size: 0.83rem !important; }

/* ── Native st.metric ── */
[data-testid="stMetric"] {
    background: var(--card) !important;
    border: 1px solid var(--bdr) !important;
    border-radius: 10px !important;
    padding: 14px 16px !important;
}
[data-testid="stMetricLabel"] p { color: var(--t2) !important; font-size: 0.75rem !important; }
[data-testid="stMetricValue"]   { color: var(--t1) !important; }

/* ── Alerts / warnings ── */
[data-testid="stAlert"] {
    background: rgba(245,158,11,.08) !important;
    border: 1px solid rgba(245,158,11,.25) !important;
    border-radius: 10px !important;
    color: #fde68a !important;
}

/* ── Multiselect tags ── */
[data-baseweb="tag"] {
    background: rgba(59,130,246,.18) !important;
    border: 1px solid rgba(59,130,246,.3) !important;
    border-radius: 5px !important;
}
[data-baseweb="tag"] span { color: #93c5fd !important; font-size: 0.75rem !important; }

/* ── Insight cards ── */
.ins {
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 0.87rem;
    line-height: 1.65;
    border-left: 3px solid;
}
.ins.info { background: rgba(59,130,246,.07);  border-color: var(--blue);   color: #bfdbfe; }
.ins.pos  { background: rgba(16,185,129,.07);  border-color: var(--green);  color: #a7f3d0; }
.ins.warn { background: rgba(245,158,11,.07);  border-color: var(--amber);  color: #fde68a; }
.ins strong { font-weight: 700; }

/* ── Empty state ── */
.emp {
    text-align: center;
    padding: 2.5rem 1.5rem;
    background: var(--card);
    border: 1px dashed var(--bdr);
    border-radius: 12px;
    color: var(--t2);
    font-size: 0.88rem;
    margin: 4px 0;
}

/* ── Sidebar label ── */
.sb-lbl {
    display: block;
    color: var(--blue) !important;
    font-size: 0.59rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
    margin: 1.1rem 0 0.35rem !important;
}

/* ── Divider ── */
hr { border: none !important; border-top: 1px solid var(--bdr) !important; margin: 1.2rem 0 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(59,130,246,.3); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--blue); }

/* ── Select arrows ── */
[data-baseweb="select"] svg { fill: var(--t3) !important; }

/* ── General text ── */
h1, h2, h3 { color: var(--t1) !important; }
p, .stMarkdown p { color: var(--t2) !important; }

/* ═══════════════════════════════════════
   HEADER CLASSES (used for responsive)
═══════════════════════════════════════ */
.hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 22px 0 18px;
    border-bottom: 1px solid var(--bdr);
    margin-bottom: 6px;
    gap: 12px;
}
.hdr-left { display: flex; align-items: center; gap: 14px; flex: 1; min-width: 0; }
.hdr-logo {
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    width: 38px; height: 38px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.15rem; flex-shrink: 0;
}
.hdr-title-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.hdr-title { font-size: 1.2rem; font-weight: 800; color: #f0f6ff; letter-spacing: -.4px; white-space: nowrap; }
.hdr-live {
    background: rgba(59,130,246,.16); color: #60a5fa;
    font-size: 0.6rem; font-weight: 700; padding: 2px 7px;
    border-radius: 4px; letter-spacing: 1.2px; text-transform: uppercase;
    border: 1px solid rgba(59,130,246,.25); white-space: nowrap;
}
.hdr-sub { color: #3d5475; font-size: 0.74rem; margin-top: 3px; }
.hdr-chips { display: flex; gap: 8px; flex-shrink: 0; }
.hdr-chip {
    background: var(--card); border: 1px solid var(--bdr);
    border-radius: 9px; padding: 8px 16px; text-align: center;
}
.hdr-chip-lbl { color: #3d5475; font-size: 0.58rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; }
.hdr-chip-val { color: #8ba3c7; font-size: 0.78rem; font-weight: 600; }
.hdr-chip-val.accent { color: #60a5fa; }

/* ═══════════════════════════════════════
   RESPONSIVE BREAKPOINTS
═══════════════════════════════════════ */

/* ── Tablet  ≤ 1100px ── */
@media screen and (max-width: 1100px) {
    .block-container { padding: 0 1.2rem 2rem !important; }
    .kpi-val { font-size: 1.5rem !important; }
    .kpi { padding: 16px 14px 12px !important; }
    .hdr-title { font-size: 1.05rem !important; }
    .hdr-sub { font-size: 0.68rem !important; }
}

/* ── Mobile ≤ 768px ── */
@media screen and (max-width: 768px) {
    /* Spacing */
    .block-container { padding: 0 0.5rem 2rem !important; }

    /* Header */
    .hdr { padding: 14px 0 12px !important; }
    .hdr-chips { display: none !important; }
    .hdr-sub { display: none !important; }
    .hdr-logo { width: 32px !important; height: 32px !important; font-size: 1rem !important; border-radius: 8px !important; }
    .hdr-title { font-size: 0.95rem !important; }
    .hdr-left { gap: 10px !important; }

    /* Columns — wrap to 2 per row */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 8px !important;
    }
    [data-testid="column"] {
        min-width: calc(50% - 4px) !important;
        flex: 1 1 calc(50% - 4px) !important;
        width: calc(50% - 4px) !important;
    }

    /* KPI cards */
    .kpi { height: auto !important; padding: 14px 13px 11px !important; }
    .kpi-val { font-size: 1.3rem !important; letter-spacing: -0.5px !important; }
    .kpi-lbl { font-size: 0.6rem !important; margin-bottom: 6px !important; }
    .kpi-ico { display: none !important; }
    .kpi-bdg { font-size: 0.65rem !important; padding: 2px 6px !important; }

    /* Section headers */
    .shdr { margin: 1.3rem 0 0.6rem !important; }
    .shdr-txt { font-size: 0.82rem !important; }
    .shdr-badge { display: none !important; }

    /* Tabs — horizontal scroll */
    .stTabs [data-baseweb="tab-list"] {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
        -webkit-overflow-scrolling: touch !important;
        scrollbar-width: none !important;
        border-radius: 8px !important;
        padding: 3px !important;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none !important; }
    .stTabs [data-baseweb="tab"] {
        white-space: nowrap !important;
        font-size: 0.72rem !important;
        padding: 6px 10px !important;
    }

    /* Insight cards */
    .ins { font-size: 0.82rem !important; padding: 10px 12px !important; }

    /* Sidebar improvements on mobile */
    [data-testid="stSidebar"] .block-container { padding: 1rem 0.75rem !important; }

    /* Native metrics in 3-col row */
    [data-testid="stMetric"] { padding: 10px 12px !important; }
    [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
}

/* ── Small mobile ≤ 480px ── */
@media screen and (max-width: 480px) {
    /* Single column everything */
    [data-testid="column"] {
        min-width: 100% !important;
        flex: 1 1 100% !important;
        width: 100% !important;
    }
    .kpi-val { font-size: 1.45rem !important; }
    .block-container { padding: 0 0.3rem 1.5rem !important; }
    .hdr-live { display: none !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Plotly config ──────────────────────────────
PLOTLY_CFG = {"displayModeBar": False, "scrollZoom": False}
COLORS = ["#3b82f6", "#a855f7", "#10b981", "#f59e0b", "#ef4444",
          "#06b6d4", "#ec4899", "#14b8a6", "#f97316", "#6366f1"]

PLOTLY_DARK = dict(
    plot_bgcolor  = "#0c1a2e",
    paper_bgcolor = "#0c1a2e",
    font          = dict(color="#64748b", family="Inter, system-ui", size=11),
    xaxis         = dict(gridcolor="#182d4a", linecolor="#182d4a", zerolinecolor="#182d4a",
                         tickfont=dict(color="#3d5475", size=10)),
    yaxis         = dict(gridcolor="#182d4a", linecolor="#182d4a", zerolinecolor="#182d4a",
                         tickfont=dict(color="#3d5475", size=10)),
    hoverlabel    = dict(bgcolor="#0f2040", bordercolor="#234069",
                         font=dict(color="#f0f6ff", size=12)),
    margin        = dict(l=10, r=10, t=30, b=10),
)

LEGEND_H = dict(bgcolor="rgba(0,0,0,0)", borderwidth=0,
                font=dict(color="#8ba3c7", size=11), orientation="h", y=-0.18)


# ══════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def load_all_data():
    fact = pd.read_parquet(os.path.join(PROCESSED_DIR, "fact_final.parquet"))
    fact["date"] = pd.to_datetime(fact["date"])
    daily = pd.read_parquet(os.path.join(PROCESSED_DIR, "daily_revenue.parquet"))
    daily["date"] = pd.to_datetime(daily["date"])
    monthly  = pd.read_parquet(os.path.join(PROCESSED_DIR, "monthly_revenue.parquet"))
    forecast = pd.read_parquet(os.path.join(PROCESSED_DIR, "forecast.parquet"))
    cohort   = pd.read_parquet(os.path.join(PROCESSED_DIR, "cohort_retention.parquet"))
    cat_stats    = pd.read_parquet(os.path.join(PROCESSED_DIR, "category_stats.parquet"))
    region_stats = pd.read_parquet(os.path.join(PROCESSED_DIR, "region_stats.parquet"))
    rfm = pd.read_parquet(os.path.join(PROCESSED_DIR, "rfm.parquet"))
    return fact, daily, monthly, forecast, cohort, cat_stats, region_stats, rfm


def check_data_ready():
    required = ["fact_final.parquet", "daily_revenue.parquet", "monthly_revenue.parquet",
                "forecast.parquet", "cohort_retention.parquet", "category_stats.parquet",
                "region_stats.parquet", "rfm.parquet"]
    return [f for f in required if not os.path.exists(os.path.join(PROCESSED_DIR, f))]


@st.cache_resource
def run_pipeline_if_needed():
    """Auto-bootstrap pipeline on first launch."""
    if not check_data_ready():
        return "ready"
    import importlib.util
    def run_script(name):
        path = os.path.join(BASE_DIR, "scripts", name)
        spec = importlib.util.spec_from_file_location("mod", path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()
    for step in ["ingestion.py", "cleaning.py", "transformation.py", "db_loader.py", "analytics.py"]:
        run_script(step)
    return "ready"


# ══════════════════════════════════════════════════════════════════
# UI HELPERS
# ══════════════════════════════════════════════════════════════════

def kpi_card(label, value, delta=None, delta_good=True, color="#3b82f6", icon=""):
    badge = ""
    if delta:
        good  = (delta_good and not delta.startswith("-")) or (not delta_good and delta.startswith("-"))
        cls   = "pos" if good else "neg"
        arrow = "▲" if not delta.startswith("-") else "▼"
        badge = f'<div class="kpi-bdg {cls}">{arrow} {delta}</div>'
    ico_html = f'<div class="kpi-ico">{icon}</div>' if icon else ""
    st.markdown(
        f'<div class="kpi" style="--kc:{color}">'
        f'{ico_html}'
        f'<div class="kpi-lbl">{label}</div>'
        f'<div class="kpi-val">{value}</div>'
        f'{badge}</div>',
        unsafe_allow_html=True,
    )


def shdr(icon, title, badge=""):
    b = f'<span class="shdr-badge">{badge}</span>' if badge else ""
    st.markdown(
        f'<div class="shdr">'
        f'<div class="shdr-bar"></div>'
        f'<span class="shdr-txt">{icon}&nbsp; {title}</span>'
        f'{b}<div class="shdr-line"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def empty(msg="No data matches the selected filters."):
    st.markdown(
        f'<div class="emp">'
        f'<div style="font-size:1.6rem;margin-bottom:8px;opacity:.5;">🔍</div>'
        f'<div>{msg}</div></div>',
        unsafe_allow_html=True,
    )


def ins_card(text, kind="info"):
    st.markdown(f'<div class="ins {kind}">{text}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# KPI COMPUTATION
# ══════════════════════════════════════════════════════════════════

def compute_kpis(df):
    total_revenue = df["revenue"].sum()
    total_profit  = df["profit"].sum()
    total_orders  = df["order_id"].nunique()
    aov           = total_revenue / total_orders if total_orders else 0
    profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0
    return_rate   = df["return_flag"].mean() * 100
    monthly = df.groupby("month_label")["revenue"].sum().sort_index()
    mom_growth = 0.0
    if len(monthly) >= 2:
        last, prev = monthly.iloc[-1], monthly.iloc[-2]
        mom_growth = ((last - prev) / prev * 100) if prev else 0
    return dict(
        total_revenue=total_revenue, total_profit=total_profit,
        total_orders=total_orders, aov=aov,
        profit_margin=profit_margin, return_rate=return_rate,
        mom_growth=mom_growth,
    )


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():

    # ── Product header ───────────────────────────────────────────
    st.markdown("""
    <div class="hdr">
        <div class="hdr-left">
            <div class="hdr-logo">📊</div>
            <div>
                <div class="hdr-title-row">
                    <span class="hdr-title">Sales Analytics</span>
                    <span class="hdr-live">Live</span>
                </div>
                <div class="hdr-sub">
                    End-to-End Business Intelligence &nbsp;·&nbsp; 3 Years of Data &nbsp;·&nbsp; Real-Time Filters
                </div>
            </div>
        </div>
        <div class="hdr-chips">
            <div class="hdr-chip">
                <div class="hdr-chip-lbl">Platform</div>
                <div class="hdr-chip-val">Streamlit</div>
            </div>
            <div class="hdr-chip">
                <div class="hdr-chip-lbl">Version</div>
                <div class="hdr-chip-val accent">2.0</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Auto-bootstrap ───────────────────────────────────────────
    if check_data_ready():
        with st.spinner("Initializing data pipeline for the first time... (~60 seconds)"):
            run_pipeline_if_needed()
        st.rerun()

    with st.spinner("Loading data..."):
        fact, daily, monthly, forecast, cohort, cat_stats, region_stats, rfm = load_all_data()

    # ── Sidebar ──────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style="padding:0 0 14px;border-bottom:1px solid #182d4a;margin-bottom:4px;">
            <div style="color:#f0f6ff;font-size:0.88rem;font-weight:700;">Filters</div>
            <div style="color:#3d5475;font-size:0.7rem;margin-top:2px;">Adjust to slice the data</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<span class="sb-lbl">Date Range</span>', unsafe_allow_html=True)
        min_date, max_date = fact["date"].min().date(), fact["date"].max().date()
        date_range = st.date_input(
            "date", value=(min_date, max_date),
            min_value=min_date, max_value=max_date,
            label_visibility="collapsed",
        )

        st.markdown('<span class="sb-lbl">Geography</span>', unsafe_allow_html=True)
        all_regions = sorted(fact["region"].dropna().unique())
        sel_regions = st.multiselect("region", all_regions, default=all_regions,
                                     label_visibility="collapsed")

        st.markdown('<span class="sb-lbl">Category</span>', unsafe_allow_html=True)
        all_cats = sorted(fact["category"].dropna().unique())
        sel_cats = st.multiselect("category", all_cats, default=all_cats,
                                  label_visibility="collapsed")

        all_segs = sorted(fact["cust_segment"].dropna().unique()) if "cust_segment" in fact.columns else []
        if all_segs:
            st.markdown('<span class="sb-lbl">Customer Segment</span>', unsafe_allow_html=True)
            sel_segments = st.multiselect("segment", all_segs, default=all_segs,
                                          label_visibility="collapsed")
        else:
            sel_segments = []

        st.markdown('<div style="border-top:1px solid #182d4a;margin:16px 0 12px"></div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex;flex-direction:column;gap:7px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#3d5475;font-size:0.68rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Records</span>
                <span style="color:#60a5fa;font-size:0.78rem;font-weight:700;">{len(fact):,}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#3d5475;font-size:0.68rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;">From</span>
                <span style="color:#8ba3c7;font-size:0.75rem;">{min_date}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#3d5475;font-size:0.68rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;">To</span>
                <span style="color:#8ba3c7;font-size:0.75rem;">{max_date}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Apply filters ─────────────────────────────────────────────
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
        empty("No data matches your current filters. Try broadening the date range or selecting more options.")
        st.stop()

    kpis = compute_kpis(filt)

    # ── KPI row ───────────────────────────────────────────────────
    shdr("📈", "Key Performance Indicators",
         f"{len(filt):,} records · {kpis['total_orders']:,} orders")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Total Revenue", f"${kpis['total_revenue']/1e6:.2f}M",
                 f"{kpis['mom_growth']:+.1f}% MoM",
                 color="#3b82f6", icon="💰")
    with c2:
        kpi_card("Total Profit", f"${kpis['total_profit']/1e6:.2f}M",
                 color="#a855f7", icon="📈")
    with c3:
        kpi_card("Profit Margin", f"{kpis['profit_margin']:.1f}%",
                 color="#10b981", icon="🎯")
    with c4:
        kpi_card("Return Rate", f"{kpis['return_rate']:.1f}%",
                 f"{kpis['return_rate']:.1f}%", delta_good=False,
                 color="#ef4444", icon="🔄")
    with c5:
        kpi_card("Avg Order Value", f"${kpis['aov']:.0f}",
                 color="#f59e0b", icon="🛒")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────
    tabs = st.tabs(["📈  Overview", "👥  Customers", "📦  Products",
                    "⚠️  Anomalies & Forecast", "💡  Insights"])

    # ════════════════════════════════════
    # TAB 1 — Overview
    # ════════════════════════════════════
    with tabs[0]:
        col1, col2 = st.columns([3, 2])

        with col1:
            shdr("📉", "Revenue Trend")
            d_filt = daily.copy()
            if len(date_range) == 2:
                d_filt = d_filt[(d_filt["date"].dt.date >= date_range[0]) &
                                (d_filt["date"].dt.date <= date_range[1])]
            if d_filt.empty:
                empty("No daily revenue data for this date range.")
            else:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=d_filt["date"], y=d_filt["revenue"],
                    fill="tozeroy", fillcolor="rgba(59,130,246,0.06)",
                    line=dict(color="#3b82f6", width=1), name="Daily", opacity=0.8))
                fig.add_trace(go.Scatter(
                    x=d_filt["date"], y=d_filt["ma_7"],
                    line=dict(color="#f59e0b", width=1.5), name="7-Day MA"))
                fig.add_trace(go.Scatter(
                    x=d_filt["date"], y=d_filt["ma_30"],
                    line=dict(color="#a855f7", width=2), name="30-Day MA"))
                fig.update_layout(**PLOTLY_DARK, height=310)
                fig.update_layout(legend=LEGEND_H)
                st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CFG)

        with col2:
            shdr("🌍", "Revenue by Region")
            reg_df = (filt.groupby("region")["revenue"].sum()
                      .reset_index().sort_values("revenue", ascending=False))
            if reg_df.empty:
                empty()
            else:
                fig_pie = px.pie(reg_df, values="revenue", names="region",
                                 color_discrete_sequence=COLORS, hole=0.5)
                fig_pie.update_traces(textinfo="label+percent", textfont_size=10,
                                      textfont_color="#f0f6ff")
                fig_pie.update_layout(**PLOTLY_DARK, height=310)
                fig_pie.update_layout(legend=LEGEND_H)
                st.plotly_chart(fig_pie, use_container_width=True, config=PLOTLY_CFG)

        shdr("📦", "Category Performance")
        cat_df = (filt.groupby("category")
                  .agg(revenue=("revenue","sum"), profit=("profit","sum"))
                  .reset_index().sort_values("revenue", ascending=False))
        if cat_df.empty:
            empty()
        else:
            fig_cat = go.Figure()
            fig_cat.add_trace(go.Bar(x=cat_df["category"], y=cat_df["revenue"]/1e6,
                                     name="Revenue ($M)", marker_color="#3b82f6",
                                     marker_line_width=0))
            fig_cat.add_trace(go.Bar(x=cat_df["category"], y=cat_df["profit"]/1e6,
                                     name="Profit ($M)", marker_color="#10b981",
                                     marker_line_width=0))
            fig_cat.update_layout(**PLOTLY_DARK, height=320, barmode="group",
                                   xaxis_title="", yaxis_title="Amount ($M)")
            fig_cat.update_layout(legend=LEGEND_H)
            st.plotly_chart(fig_cat, use_container_width=True, config=PLOTLY_CFG)

        shdr("🗺️", "Region × Month Revenue Heatmap", "Last 18 months")
        if "region" in filt.columns:
            heat_data = (filt.pivot_table(index="month_label", columns="region",
                                          values="revenue", aggfunc="sum")
                         .fillna(0).iloc[-18:])
            if heat_data.empty:
                empty()
            else:
                fig_heat = px.imshow(heat_data/1e3, text_auto=".0f",
                                     color_continuous_scale="Blues",
                                     labels=dict(color="Revenue ($K)"))
                fig_heat.update_layout(**PLOTLY_DARK, height=440)
                st.plotly_chart(fig_heat, use_container_width=True, config=PLOTLY_CFG)

    # ════════════════════════════════════
    # TAB 2 — Customers
    # ════════════════════════════════════
    with tabs[1]:
        col1, col2 = st.columns(2)

        with col1:
            shdr("🎯", "RFM Customer Segments")
            rfm_counts = rfm["rfm_segment"].value_counts().reset_index()
            rfm_counts.columns = ["segment", "count"]
            if rfm_counts.empty:
                empty()
            else:
                fig_rfm = px.pie(rfm_counts, values="count", names="segment",
                                 color_discrete_sequence=COLORS, hole=0.45)
                fig_rfm.update_traces(textfont_color="#f0f6ff")
                fig_rfm.update_layout(**PLOTLY_DARK, height=360)
                fig_rfm.update_layout(legend=LEGEND_H)
                st.plotly_chart(fig_rfm, use_container_width=True, config=PLOTLY_CFG)

        with col2:
            shdr("💎", "CLV Segment Distribution")
            clv_seg = (filt.groupby("clv_segment")
                       .agg(customers=("customer_id","nunique"), revenue=("revenue","sum"))
                       .reset_index())
            if clv_seg.empty:
                empty()
            else:
                fig_clv = px.bar(
                    clv_seg, x="clv_segment", y="revenue", color="clv_segment",
                    text=clv_seg["customers"].apply(lambda x: f"{x:,} cust."),
                    color_discrete_sequence=["#ef4444","#f59e0b","#10b981"])
                fig_clv.update_traces(marker_line_width=0, textfont_size=10)
                fig_clv.update_layout(**PLOTLY_DARK, height=360, showlegend=False,
                                       xaxis_title="CLV Segment", yaxis_title="Revenue ($)")
                st.plotly_chart(fig_clv, use_container_width=True, config=PLOTLY_CFG)

        shdr("🔄", "Customer Cohort Retention (%)")
        cohort_vals = cohort.astype(float).head(18)
        cohort_vals.index = cohort_vals.index.astype(str)
        if cohort_vals.empty:
            empty()
        else:
            fig_coh = px.imshow(cohort_vals, text_auto=".0f",
                                color_continuous_scale="Blues",
                                labels=dict(color="Retention %"), zmin=0, zmax=100)
            fig_coh.update_layout(**PLOTLY_DARK, height=440)
            st.plotly_chart(fig_coh, use_container_width=True, config=PLOTLY_CFG)

        shdr("🏆", "Top Customers by Revenue")
        top_custs = (filt.groupby("customer_id")
                     .agg(revenue=("revenue","sum"), orders=("order_id","nunique"),
                          rfm_segment=("rfm_segment","first"),
                          clv_segment=("clv_segment","first"))
                     .reset_index().nlargest(15, "revenue"))
        if top_custs.empty:
            empty()
        else:
            top_custs["revenue"] = top_custs["revenue"].apply(lambda x: f"${x:,.0f}")
            st.dataframe(top_custs, use_container_width=True, hide_index=True)

    # ════════════════════════════════════
    # TAB 3 — Products
    # ════════════════════════════════════
    with tabs[2]:
        col1, col2 = st.columns(2)

        with col1:
            shdr("💹", "Profit vs Revenue by Category")
            cat_bubble = (filt.groupby("category")
                          .agg(revenue=("revenue","sum"), profit=("profit","sum"),
                               orders=("order_id","nunique"))
                          .reset_index())
            if cat_bubble.empty:
                empty()
            else:
                fig_bub = px.scatter(cat_bubble, x="revenue", y="profit",
                                     size="orders", color="category", text="category",
                                     color_discrete_sequence=COLORS, size_max=55)
                fig_bub.update_traces(textposition="top center", textfont_size=9,
                                      textfont_color="#8ba3c7")
                fig_bub.update_layout(**PLOTLY_DARK, height=400, showlegend=False,
                                       xaxis_title="Revenue ($)", yaxis_title="Profit ($)")
                st.plotly_chart(fig_bub, use_container_width=True, config=PLOTLY_CFG)

        with col2:
            shdr("🔁", "Return Rate by Category")
            cat_ret = (filt.groupby("category")
                       .agg(returns=("return_flag","sum"), total=("return_flag","count"))
                       .reset_index())
            cat_ret["return_rate"] = (cat_ret["returns"] / cat_ret["total"] * 100).round(2)
            cat_ret = cat_ret.sort_values("return_rate", ascending=True)
            if cat_ret.empty:
                empty()
            else:
                mean_rr = cat_ret["return_rate"].mean()
                colors  = ["#ef4444" if r > mean_rr else "#3b82f6" for r in cat_ret["return_rate"]]
                fig_rr = go.Figure(go.Bar(
                    x=cat_ret["return_rate"], y=cat_ret["category"],
                    orientation="h", marker_color=colors, marker_line_width=0,
                    text=cat_ret["return_rate"].apply(lambda x: f"{x:.1f}%"),
                    textposition="outside", textfont=dict(color="#8ba3c7", size=10)))
                fig_rr.add_vline(x=mean_rr, line_color="#f59e0b", line_dash="dash",
                                 annotation_text=f"Avg {mean_rr:.1f}%",
                                 annotation_font_color="#f59e0b", annotation_font_size=10)
                fig_rr.update_layout(**PLOTLY_DARK, height=400,
                                      xaxis_title="Return Rate (%)", yaxis_title="")
                st.plotly_chart(fig_rr, use_container_width=True, config=PLOTLY_CFG)

        shdr("🔬", "Top 20 Products by Revenue")
        drill_cat = st.selectbox("Filter by category:",
                                 ["All"] + sorted(filt["category"].dropna().unique()),
                                 label_visibility="collapsed")
        prod_view = filt if drill_cat == "All" else filt[filt["category"] == drill_cat]
        top_prods = (prod_view.groupby("product_id")
                     .agg(revenue=("revenue","sum"), profit=("profit","sum"),
                          units=("quantity","sum"), orders=("order_id","nunique"),
                          category=("category","first"),
                          return_rate=("return_flag","mean"))
                     .reset_index().nlargest(20, "revenue"))
        if top_prods.empty:
            empty("No products found for the selected category.")
        else:
            top_prods["revenue"]     = top_prods["revenue"].apply(lambda x: f"${x:,.0f}")
            top_prods["profit"]      = top_prods["profit"].apply(lambda x: f"${x:,.0f}")
            top_prods["return_rate"] = top_prods["return_rate"].apply(lambda x: f"{x*100:.1f}%")
            top_prods["units"]       = top_prods["units"].apply(lambda x: f"{x:,.0f}")
            st.dataframe(top_prods, use_container_width=True, hide_index=True)

    # ════════════════════════════════════
    # TAB 4 — Anomalies & Forecast
    # ════════════════════════════════════
    with tabs[3]:
        shdr("🔍", "Revenue Anomaly Detection", "Z-Score method")
        d_anom = daily.copy()
        if len(date_range) == 2:
            d_anom = d_anom[(d_anom["date"].dt.date >= date_range[0]) &
                            (d_anom["date"].dt.date <= date_range[1])]

        if d_anom.empty:
            empty("No anomaly data for the selected date range.")
        else:
            normal = d_anom[d_anom["anomaly_type"] == "Normal"]
            spikes = d_anom[d_anom["anomaly_type"] == "Spike"]
            drops  = d_anom[d_anom["anomaly_type"] == "Drop"]

            fig_anom = go.Figure()
            fig_anom.add_trace(go.Scatter(
                x=d_anom["date"], y=d_anom["ma_30"],
                line=dict(color="#3b82f6", width=2), name="30-Day MA"))
            fig_anom.add_trace(go.Scatter(
                x=normal["date"], y=normal["revenue"], mode="markers",
                marker=dict(color="#3d5475", size=3, opacity=0.5), name="Normal"))
            if not spikes.empty:
                fig_anom.add_trace(go.Scatter(
                    x=spikes["date"], y=spikes["revenue"], mode="markers",
                    marker=dict(color="#f59e0b", size=10, symbol="triangle-up",
                                line=dict(color="#fde68a", width=1)),
                    name=f"Spikes ({len(spikes)})"))
            if not drops.empty:
                fig_anom.add_trace(go.Scatter(
                    x=drops["date"], y=drops["revenue"], mode="markers",
                    marker=dict(color="#ef4444", size=10, symbol="triangle-down",
                                line=dict(color="#fca5a5", width=1)),
                    name=f"Drops ({len(drops)})"))
            fig_anom.update_layout(**PLOTLY_DARK, height=380,
                                   xaxis_title="Date", yaxis_title="Daily Revenue ($)")
            fig_anom.update_layout(legend=LEGEND_H)
            st.plotly_chart(fig_anom, use_container_width=True, config=PLOTLY_CFG)

            a1, a2, a3 = st.columns(3)
            a1.metric("Total Anomalies", int(d_anom["is_anomaly"].sum()))
            a2.metric("Revenue Spikes",  len(spikes))
            a3.metric("Revenue Drops",   len(drops))

        st.markdown("<hr>", unsafe_allow_html=True)

        shdr("📈", "6-Month ARIMA Revenue Forecast", forecast["method"].iloc[0])
        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(
            x=monthly["month_label"], y=monthly["revenue"]/1e6,
            line=dict(color="#3b82f6", width=2), mode="lines+markers",
            marker=dict(size=5, color="#3b82f6"),
            name="Historical Revenue ($M)"))
        fig_fc.add_trace(go.Scatter(
            x=forecast["month_label"], y=forecast["forecast_revenue"]/1e6,
            line=dict(color="#f59e0b", width=2, dash="dash"), mode="lines+markers",
            marker=dict(symbol="diamond", size=8, color="#f59e0b"),
            name="Forecast ($M)"))
        fig_fc.add_trace(go.Scatter(
            x=list(forecast["month_label"]) + list(reversed(forecast["month_label"])),
            y=list(forecast["upper_ci"]/1e6) + list(reversed(forecast["lower_ci"]/1e6)),
            fill="toself", fillcolor="rgba(245,158,11,0.1)",
            line=dict(color="rgba(0,0,0,0)"), name="80% CI"))
        fig_fc.update_layout(**PLOTLY_DARK, height=400,
                             xaxis_title="Month", yaxis_title="Revenue ($M)")
        fig_fc.update_layout(legend=LEGEND_H)
        fig_fc.update_xaxes(tickangle=30)
        st.plotly_chart(fig_fc, use_container_width=True, config=PLOTLY_CFG)

        next_months = forecast[["month_label","forecast_revenue","lower_ci","upper_ci"]].copy()
        next_months.columns = ["Month","Forecast ($)","Lower CI ($)","Upper CI ($)"]
        for col in ["Forecast ($)","Lower CI ($)","Upper CI ($)"]:
            next_months[col] = next_months[col].apply(lambda x: f"${x:,.0f}")
        st.dataframe(next_months, use_container_width=True, hide_index=True)

    # ════════════════════════════════════
    # TAB 5 — Insights
    # ════════════════════════════════════
    with tabs[4]:
        shdr("💡", "Auto-Generated Business Insights",
             f"Computed from {len(filt):,} records")
        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

        # recompute on filtered data
        cat_fs = (filt.groupby("category")
                  .agg(revenue=("revenue","sum"), profit=("profit","sum"),
                       orders=("order_id","nunique"),
                       returns=("return_flag","sum"), total_rows=("order_id","count"))
                  .reset_index())
        if not cat_fs.empty:
            cat_fs["return_rate_pct"]  = (cat_fs["returns"] / cat_fs["total_rows"] * 100).round(2)
            cat_fs["revenue_share_pct"]= (cat_fs["revenue"] / cat_fs["revenue"].sum() * 100).round(2)
            cat_fs["profit_margin_pct"]= (cat_fs["profit"]  / cat_fs["revenue"] * 100).round(2)
            cat_fs = cat_fs.sort_values("revenue", ascending=False)

        reg_fs = (filt.groupby("region")
                  .agg(revenue=("revenue","sum"), orders=("order_id","nunique"))
                  .reset_index())
        if not reg_fs.empty:
            reg_fs["revenue_share_pct"] = (reg_fs["revenue"] / reg_fs["revenue"].sum() * 100).round(2)
            reg_fs = reg_fs.sort_values("revenue", ascending=False)

        mfilt = filt.groupby("month_label")["revenue"].sum().reset_index().sort_values("month_label")
        mfilt["prev"]      = mfilt["revenue"].shift(1)
        mfilt["mom_growth"]= ((mfilt["revenue"]-mfilt["prev"])/mfilt["prev"]*100).round(2)

        insights = []

        if not reg_fs.empty:
            r = reg_fs.iloc[0]
            insights.append((
                f"🌍 <strong>{r['region']}</strong> is the top region — "
                f"<strong>{r['revenue_share_pct']:.1f}%</strong> of total revenue (${r['revenue']:,.0f}).",
                "pos"))

        if not cat_fs.empty:
            best = cat_fs.iloc[0]
            insights.append((
                f"⭐ <strong>{best['category']}</strong> leads all categories — "
                f"<strong>${best['revenue']:,.0f}</strong> revenue "
                f"(<strong>{best['revenue_share_pct']:.1f}%</strong> share), "
                f"<strong>{best['profit_margin_pct']:.1f}%</strong> margin.",
                "pos"))
            wr = cat_fs.loc[cat_fs["return_rate_pct"].idxmax()]
            insights.append((
                f"🔄 <strong>{wr['category']}</strong> has the highest return rate: "
                f"<strong>{wr['return_rate_pct']:.1f}%</strong> — quality review recommended.",
                "warn"))
            bm = cat_fs.loc[cat_fs["profit_margin_pct"].idxmax()]
            insights.append((
                f"💰 <strong>{bm['category']}</strong> delivers the best margin: "
                f"<strong>{bm['profit_margin_pct']:.1f}%</strong> — highest profitability per dollar.",
                "pos"))

        insights.append((
            f"📊 Overall profit margin <strong>{kpis['profit_margin']:.1f}%</strong> on "
            f"<strong>${kpis['total_revenue']/1e6:.2f}M</strong> revenue from "
            f"<strong>{kpis['total_orders']:,}</strong> orders.",
            "info"))
        insights.append((
            f"📦 Return rate <strong>{kpis['return_rate']:.1f}%</strong> — "
            f"{'⚠️ above industry average, needs attention' if kpis['return_rate'] > 15 else '✅ within acceptable range'}.",
            "warn" if kpis["return_rate"] > 15 else "info"))
        insights.append((
            f"🛒 Average Order Value <strong>${kpis['aov']:.2f}</strong> — "
            f"{'strong' if kpis['aov'] > 200 else 'moderate'} basket sizes.",
            "info"))

        mv = mfilt.dropna(subset=["mom_growth"])
        if not mv.empty:
            wm = mv.loc[mv["mom_growth"].idxmin()]
            bm2 = mv.loc[mv["mom_growth"].idxmax()]
            insights.append((
                f"📉 Worst MoM decline: <strong>{wm['mom_growth']:.1f}%</strong> in "
                f"<strong>{wm['month_label']}</strong> — possible seasonal effect.",
                "warn"))
            insights.append((
                f"📈 Best MoM growth: <strong>+{bm2['mom_growth']:.1f}%</strong> in "
                f"<strong>{bm2['month_label']}</strong> — standout performance month.",
                "pos"))

        mom_kind = "pos" if kpis["mom_growth"] >= 0 else "warn"
        insights.append((
            f"⚡ Current MoM trend: <strong>{kpis['mom_growth']:+.1f}%</strong> — "
            f"{'positive momentum' if kpis['mom_growth'] >= 0 else 'declining — investigate root cause'}.",
            mom_kind))

        if "clv_segment" in filt.columns:
            hv = filt[filt["clv_segment"] == "High Value"]
            if not hv.empty:
                hv_r = hv["revenue"].sum() / filt["revenue"].sum() * 100
                hv_c = hv["customer_id"].nunique() / filt["customer_id"].nunique() * 100
                insights.append((
                    f"🏆 <strong>High Value</strong> customers ({hv_c:.1f}% of base) generate "
                    f"<strong>{hv_r:.1f}%</strong> of revenue — classic Pareto pattern.",
                    "pos"))

        for text, kind in insights:
            ins_card(text, kind)

        st.markdown(
            f'<div style="color:#3d5475;font-size:0.75rem;margin-top:10px;">'
            f'{len(insights)} insights · {len(filt):,} records</div>',
            unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;color:#3d5475;font-size:0.72rem;padding:6px 0 16px;">
        Sales Analytics System &nbsp;·&nbsp; Python · Pandas · SQLite · Streamlit · Plotly
        &nbsp;·&nbsp; Ingestion → Cleaning → Transformation → Analytics → Viz
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
