# Sales Analytics System

<div align="center">

```
┌─────────────────────────────────────────────────────────┐
│          END-TO-END SALES ANALYTICS SYSTEM              │
│         Production-Grade Business Intelligence          │
└─────────────────────────────────────────────────────────┘
```

**Python · Pandas · NumPy · SQLite · Matplotlib · Seaborn · Plotly · Streamlit · Flask**

</div>

---

## Problem Statement

Most analytics systems show charts. This system simulates a **complete business intelligence pipeline** — from raw, messy data ingestion through advanced analytics to an interactive executive dashboard — the kind built by data engineering teams at scale.

It processes realistic synthetic data across 3 years, applies industry-standard data engineering practices, and surfaces actionable insights automatically.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    DATA LIFECYCLE PIPELINE                       │
│                                                                  │
│  [Raw CSV] → [Ingestion] → [Cleaning] → [Transformation]        │
│                                              │                   │
│                                         [SQLite DB]             │
│                                         (Star Schema)           │
│                                              │                   │
│                                       [Analytics Engine]        │
│                                    KPIs · RFM · Cohort          │
│                                  Anomaly · Forecast · STL       │
│                                              │                   │
│                              ┌───────────────┴──────────────┐   │
│                         [Streamlit]                    [Flask]  │
│                          Dashboard                      REST API │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow

| Stage | Script | Output |
|---|---|---|
| Ingestion | `scripts/ingestion.py` | `data/raw/*.csv` |
| Cleaning | `scripts/cleaning.py` | `data/processed/*_clean.parquet` |
| Transformation | `scripts/transformation.py` | `data/processed/fact_final.parquet` |
| Database | `scripts/db_loader.py` | `data/sales_analytics.db` |
| Analytics | `scripts/analytics.py` | `data/processed/*.parquet` |
| Visualization | `scripts/visualization.py` | `outputs/charts/*.png` |
| Dashboard | `app/dashboard.py` | Streamlit (port 8501) |
| API | `app/api.py` | Flask (port 5000) |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Core | Python 3.11+ |
| Data Processing | Pandas 2.x, NumPy |
| Data Generation | Faker |
| Database | SQLite + SQLAlchemy |
| Statistics / ML | SciPy, scikit-learn (IsolationForest) |
| Forecasting | statsmodels ARIMA |
| Static Charts | Matplotlib, Seaborn |
| Interactive Charts | Plotly Express / Graph Objects |
| Dashboard | Streamlit |
| REST API | Flask + Flask-CORS |

---

## Key Features

### 📥 Data Ingestion
- **10,000 orders**, 2,000 customers, 200 products across 3 years (2022–2024)
- Intentionally injected data quality issues: ~5% missing values, ~3% duplicates, outliers, mixed date formats (`YYYY-MM-DD`, `DD/MM/YYYY`, `MM-DD-YYYY`), inconsistent category casing

### 🧹 Data Cleaning
- Median/mode imputation for missing values
- `dateutil` robust multi-format date parsing
- IQR-based outlier capping (Winsorization — no data loss)
- Category normalization (strip + title-case)

### ⚙️ Feature Engineering
- `revenue = quantity × price`
- `profit = revenue − cost`
- `profit_margin = profit / revenue`
- Time dimensions: month, quarter, year, week, day_of_week
- **Customer Lifetime Value (CLV)** — cumulative profit per customer
- **RFM Scoring** — Recency, Frequency, Monetary scored 1–5 with 7 behavioural segments
- **Cohort Month** — first purchase month per customer

### 🗃️ Database (SQLite Star Schema)
- `fact_sales` · `dim_customers` · `dim_products` · `dim_time`
- Indexes on all FK columns and date
- 3 analytical views: `vw_revenue_by_region`, `vw_category_performance`, `vw_monthly_revenue`
- 10 pre-written analytical SQL queries (LAG, NTILE, OVER, CTEs)

### 📊 Advanced Analytics
- KPIs: Total Revenue, Profit Margin, AOV, Return Rate, MoM Growth
- **Cohort Retention Analysis** — retention matrix by first-purchase month
- **RFM Segmentation** — Champions, Loyal, At Risk, Lost, etc.
- **Moving Averages** — 7-day and 30-day rolling revenue
- **Anomaly Detection** — Z-score method (flagged spikes and drops)
- **ARIMA(2,1,2) Forecasting** — 6-month forward forecast with 80% CI (linear fallback)
- **Auto-generated insights** — 10+ dynamic narrative insights computed from data

### 📈 Visualizations (9 Charts)
1. Revenue trend + 7/30-day moving averages
2. Category-wise revenue (horizontal bar)
3. Region × Month heatmap
4. RFM segment donut chart
5. Return rate by category
6. Profit vs Revenue bubble chart
7. Customer cohort retention heatmap
8. Anomaly detection timeline
9. 6-month ARIMA forecast with confidence intervals

### 🖥️ Streamlit Dashboard
- **5 interactive tabs**: Overview · Customers · Products · Anomalies & Forecast · Insights
- **Sidebar filters**: Date range, Region, Category, Customer Segment
- **KPI cards** with MoM delta indicators
- **Plotly charts** — fully interactive (hover, zoom, pan)
- **Drill-down**: Filter products by category
- **Auto-generated insights tab** — no hardcoded strings

### 🔌 Flask REST API (Bonus)
- `GET /api/health` — service check
- `GET /api/kpis` — all KPI metrics
- `GET /api/insights` — dynamic insight strings
- `GET /api/revenue?region=X&category=Y&year=Z` — filtered revenue
- `GET /api/forecast` — ARIMA forecast data
- `GET /api/categories` — category performance
- `GET /api/rfm` — RFM segmentation data

---

## Sample Auto-Generated Insights

> 🌍 Region **'North'** contributes **23.4%** of total revenue ($2,847,392).
>
> 🔄 **'Electronics'** has the highest return rate at **18.2%**, warranting quality review.
>
> 📉 Largest revenue drop: **-14.7%** in **2023-02** vs the prior month.
>
> 🏆 Top **12.1%** of customers (High Value) generate **61.3%** of revenue.
>
> ⚠️ **47** revenue anomalies detected: 24 spikes and 23 drops over the analysis period.

*(Values are computed dynamically — they reflect your actual data.)*

---

## Project Structure

```
Sales-Analytics-System/
├── data/
│   ├── raw/                   # Raw CSV files
│   │   ├── orders.csv
│   │   ├── products.csv
│   │   ├── customers.csv
│   │   └── returns.csv
│   ├── processed/             # Clean Parquet files & DB
│   │   ├── fact_final.parquet
│   │   ├── rfm.parquet
│   │   ├── daily_revenue.parquet
│   │   ├── monthly_revenue.parquet
│   │   ├── forecast.parquet
│   │   ├── cohort_retention.parquet
│   │   ├── category_stats.parquet
│   │   └── region_stats.parquet
│   └── sales_analytics.db     # SQLite database
├── scripts/
│   ├── ingestion.py           # Data generation & injection
│   ├── cleaning.py            # Cleaning & normalization
│   ├── transformation.py      # Feature engineering
│   ├── db_loader.py           # SQLite loader
│   ├── analytics.py           # KPIs, RFM, cohort, anomaly, forecast
│   └── visualization.py       # 9 static charts
├── sql/
│   ├── schema.sql             # DDL + indexes + views
│   └── queries.sql            # 10 analytical queries
├── app/
│   ├── dashboard.py           # Streamlit dashboard
│   └── api.py                 # Flask REST API
├── outputs/
│   └── charts/                # Generated PNG charts
├── run_pipeline.py            # One-click pipeline runner
├── requirements.txt
└── README.md
```

---

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Full Pipeline (Recommended)
```bash
python run_pipeline.py
```
This runs all 6 stages in sequence (~30–60 seconds).

### 3. Run Stages Individually
```bash
python scripts/ingestion.py       # Generate raw CSVs
python scripts/cleaning.py        # Clean & normalize
python scripts/transformation.py  # Feature engineering
python scripts/db_loader.py       # Load SQLite DB
python scripts/analytics.py       # Compute all analytics
python scripts/visualization.py   # Generate 9 charts
```

### 4. Launch the Dashboard
```bash
streamlit run app/dashboard.py
```
Opens at → **http://localhost:8501**

### 5. Launch the API (Bonus)
```bash
python app/api.py
```
API available at → **http://localhost:5000**

```bash
# Test the API
curl http://localhost:5000/api/health
curl http://localhost:5000/api/kpis
curl http://localhost:5000/api/revenue?region=North&year=2023
```

### 6. Query the Database Directly
```bash
# Using SQLite CLI
sqlite3 data/sales_analytics.db
.tables
SELECT * FROM vw_revenue_by_region;
SELECT * FROM vw_category_performance;
```

---

## Data Quality Issues Simulated

| Issue | Mechanism | Resolution |
|---|---|---|
| Missing values (~5%) | Random NaN injection | Median/mode imputation |
| Duplicate rows (~3%) | Row duplication | `drop_duplicates()` |
| Outliers | Z-score > 3 spikes | IQR Winsorization |
| Mixed date formats | 4 format variants | `dateutil.parser` |
| Inconsistent categories | Random case variants | Strip + title-case |

---

## SQL Queries Included

1. Revenue by region with window function `SUM() OVER ()`
2. Top 20 products by revenue (JOIN + GROUP BY)
3. Monthly MoM growth rate using `LAG()` CTE
4. Category profit margin with `HAVING`
5. Customer CLV segmentation (CASE WHEN)
6. Return rate by category
7. RFM segment distribution
8. Quarterly revenue trend
9. Top 10% customers by revenue `NTILE(10)`
10. Region × Category cross-tab

---

*Built as a production-grade portfolio project demonstrating end-to-end data engineering, analytics, and BI development.*
