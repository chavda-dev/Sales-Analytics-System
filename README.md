<div align="center">

<h1>📊 Sales Analytics System</h1>

<p><strong>Production-Grade End-to-End Business Intelligence Pipeline</strong></p>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Flask](https://img.shields.io/badge/Flask-REST_API-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite-Star_Schema-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)

<br/>

### 🚀 [**VIEW LIVE DASHBOARD →**](https://sales-analytics-system969.streamlit.app/)

<br/>

*Raw messy data → cleaned pipeline → star schema DB → ML analytics → live interactive dashboard*

</div>

---

## 🎯 What This Project Does

Most analytics projects show a couple of charts. This system simulates a **complete business intelligence pipeline** — the kind built by data engineering teams at scale.

It ingests **10,000 orders** across 3 years with intentionally injected data quality issues, cleans and transforms the data, loads it into a star-schema SQLite database, runs advanced analytics including ARIMA forecasting and RFM segmentation, and surfaces everything through an interactive Streamlit dashboard and a Flask REST API.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LIFECYCLE PIPELINE                     │
│                                                                 │
│   Raw CSV  ──►  Ingestion  ──►  Cleaning  ──►  Transformation  │
│                                                    │            │
│                                              SQLite DB          │
│                                           (Star Schema)         │
│                                                    │            │
│                                          Analytics Engine       │
│                                    KPIs · RFM · Cohort          │
│                                  Anomaly · Forecast · STL       │
│                                                    │            │
│                              ┌─────────────────────┴──────┐    │
│                         Streamlit                      Flask    │
│                         Dashboard                    REST API   │
└─────────────────────────────────────────────────────────────────┘
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
| Dashboard | `app/dashboard.py` | Streamlit → [live demo](https://sales-analytics-system969.streamlit.app/) |
| API | `app/api.py` | Flask (port 5000) |

---

## ⚙️ Tech Stack

<div align="center">

| Layer | Technology |
|---|---|
| **Core** | Python 3.11+ |
| **Data Processing** | Pandas 2.x, NumPy |
| **Data Generation** | Faker |
| **Database** | SQLite + SQLAlchemy |
| **Statistics / ML** | SciPy, scikit-learn (IsolationForest) |
| **Forecasting** | statsmodels ARIMA(2,1,2) |
| **Static Charts** | Matplotlib, Seaborn |
| **Interactive Charts** | Plotly Express / Graph Objects |
| **Dashboard** | Streamlit |
| **REST API** | Flask + Flask-CORS |

</div>

---

## ✨ Key Features

<details>
<summary><b>📥 Data Ingestion & Quality Simulation</b></summary>
<br>

- **10,000 orders**, 2,000 customers, 200 products across 3 years (2022–2024)
- Intentionally injected data quality issues to simulate real-world messiness:
  - ~5% missing values
  - ~3% duplicate rows
  - Outliers and price spikes
  - Mixed date formats (`YYYY-MM-DD`, `DD/MM/YYYY`, `MM-DD-YYYY`)
  - Inconsistent category casing

</details>

<details>
<summary><b>🧹 Data Cleaning Pipeline</b></summary>
<br>

- Median/mode imputation for missing values
- `dateutil` robust multi-format date parsing
- IQR-based outlier capping (Winsorization — zero data loss)
- Category normalization (strip + title-case)

</details>

<details>
<summary><b>⚙️ Feature Engineering</b></summary>
<br>

- `revenue = quantity × price` · `profit = revenue − cost` · `profit_margin = profit / revenue`
- Time dimensions: month, quarter, year, week, day_of_week
- **Customer Lifetime Value (CLV)** — cumulative profit per customer
- **RFM Scoring** — Recency, Frequency, Monetary scored 1–5 with 7 behavioural segments
- **Cohort Month** — first purchase month per customer

</details>

<details>
<summary><b>🗃️ SQLite Star Schema Database</b></summary>
<br>

- Tables: `fact_sales` · `dim_customers` · `dim_products` · `dim_time`
- Indexes on all FK columns and date fields
- 3 analytical views: `vw_revenue_by_region`, `vw_category_performance`, `vw_monthly_revenue`
- 10 pre-written analytical SQL queries using `LAG`, `NTILE`, `OVER`, CTEs

</details>

<details>
<summary><b>📊 Advanced Analytics Engine</b></summary>
<br>

- **KPIs**: Total Revenue, Profit Margin, AOV, Return Rate, MoM Growth
- **Cohort Retention Analysis** — retention matrix by first-purchase month
- **RFM Segmentation** — Champions, Loyal, At Risk, Lost, and more
- **Moving Averages** — 7-day and 30-day rolling revenue
- **Anomaly Detection** — Z-score method flagging spikes and drops
- **ARIMA(2,1,2) Forecasting** — 6-month forward forecast with 80% confidence interval
- **Auto-generated narrative insights** — 10+ dynamic strings computed from live data

</details>

<details>
<summary><b>🖥️ Streamlit Dashboard — <a href="https://sales-analytics-system969.streamlit.app/">Live Demo</a></b></summary>
<br>

- **5 interactive tabs**: Overview · Customers · Products · Anomalies & Forecast · Insights
- **Sidebar filters**: Date range, Region, Category, Customer Segment
- **KPI cards** with MoM delta indicators
- **Plotly charts** — fully interactive (hover, zoom, pan)
- **Drill-down**: Filter products by category
- **Auto-generated insights tab** — zero hardcoded strings

</details>

<details>
<summary><b>🔌 Flask REST API</b></summary>
<br>

| Endpoint | Description |
|---|---|
| `GET /api/health` | Service health check |
| `GET /api/kpis` | All KPI metrics |
| `GET /api/insights` | Dynamic narrative insight strings |
| `GET /api/revenue?region=X&category=Y&year=Z` | Filtered revenue data |
| `GET /api/forecast` | ARIMA forecast data |
| `GET /api/categories` | Category performance |
| `GET /api/rfm` | RFM segmentation data |

</details>

---

## 💡 Sample Auto-Generated Insights

> 🌍 Region **'North'** contributes **23.4%** of total revenue ($2,847,392)
>
> 🔄 **'Electronics'** has the highest return rate at **18.2%**, warranting quality review
>
> 📉 Largest revenue drop: **-14.7%** in **2023-02** vs the prior month
>
> 🏆 Top **12.1%** of customers (High Value) generate **61.3%** of revenue
>
> ⚠️ **47** revenue anomalies detected: 24 spikes and 23 drops over the analysis period

*All values are computed dynamically from actual data — nothing is hardcoded.*

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Full Pipeline (Recommended)
```bash
python run_pipeline.py
```
Runs all 6 stages in sequence — takes ~30–60 seconds.

### 3. Launch the Dashboard
```bash
streamlit run app/dashboard.py
# → http://localhost:8501
```
Or use the **[live hosted version](https://sales-analytics-system969.streamlit.app/)**.

### 4. Launch the REST API
```bash
python app/api.py
# → http://localhost:5000

# Test endpoints:
curl http://localhost:5000/api/health
curl http://localhost:5000/api/kpis
curl "http://localhost:5000/api/revenue?region=North&year=2023"
```

### 5. Run Stages Individually
```bash
python scripts/ingestion.py       # Generate raw CSVs
python scripts/cleaning.py        # Clean & normalize
python scripts/transformation.py  # Feature engineering
python scripts/db_loader.py       # Load SQLite DB
python scripts/analytics.py       # Compute all analytics
python scripts/visualization.py   # Generate 9 charts
```

### 6. Query the Database Directly
```bash
sqlite3 data/sales_analytics.db
.tables
SELECT * FROM vw_revenue_by_region;
SELECT * FROM vw_category_performance;
```

---

## 📁 Project Structure

```
Sales-Analytics-System/
├── data/
│   ├── raw/                    # Raw CSV files (orders, products, customers, returns)
│   ├── processed/              # Cleaned Parquet files
│   │   ├── fact_final.parquet
│   │   ├── rfm.parquet
│   │   ├── daily_revenue.parquet
│   │   ├── monthly_revenue.parquet
│   │   ├── forecast.parquet
│   │   ├── cohort_retention.parquet
│   │   ├── category_stats.parquet
│   │   └── region_stats.parquet
│   └── sales_analytics.db      # SQLite star schema database
├── scripts/
│   ├── ingestion.py            # Data generation & quality injection
│   ├── cleaning.py             # Cleaning & normalization
│   ├── transformation.py       # Feature engineering
│   ├── db_loader.py            # SQLite loader
│   ├── analytics.py            # KPIs, RFM, cohort, anomaly, forecast
│   └── visualization.py        # 9 static charts
├── sql/
│   ├── schema.sql              # DDL + indexes + analytical views
│   └── queries.sql             # 10 analytical SQL queries
├── app/
│   ├── dashboard.py            # Streamlit dashboard (5 tabs)
│   └── api.py                  # Flask REST API (7 endpoints)
├── outputs/
│   └── charts/                 # Generated PNG charts
├── run_pipeline.py             # One-click full pipeline runner
└── requirements.txt
```

---

## 🧪 Data Quality Issues Handled

| Issue | Simulation | Resolution |
|---|---|---|
| Missing values (~5%) | Random NaN injection | Median/mode imputation |
| Duplicate rows (~3%) | Row duplication | `drop_duplicates()` |
| Outliers | Z-score > 3 spikes | IQR Winsorization |
| Mixed date formats | 4 format variants | `dateutil.parser` |
| Inconsistent categories | Random case variants | Strip + title-case |

---

## 🗃️ SQL Queries Included

1. Revenue by region — `SUM() OVER ()` window function
2. Top 20 products by revenue — `JOIN + GROUP BY`
3. Monthly MoM growth rate — `LAG()` CTE
4. Category profit margin — `HAVING` clause
5. Customer CLV segmentation — `CASE WHEN`
6. Return rate by category
7. RFM segment distribution
8. Quarterly revenue trend
9. Top 10% customers by revenue — `NTILE(10)`
10. Region × Category cross-tab

---

<div align="center">

*Built as a production-grade portfolio project demonstrating end-to-end data engineering, analytics, and BI development.*

**[🚀 Live Dashboard](https://sales-analytics-system969.streamlit.app/) · [👤 View Portfolio](https://github.com/chavda-dev)**

</div>
