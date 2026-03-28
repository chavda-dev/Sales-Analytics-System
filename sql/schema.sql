-- ============================================================
-- schema.sql — Sales Analytics System Star Schema
-- SQLite-compatible DDL
-- ============================================================

-- ─────────────────────────────────────────────
-- Dimension Tables
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id     TEXT PRIMARY KEY,
    location        TEXT,
    region          TEXT,
    segment         TEXT,
    clv             REAL,
    rfm_segment     TEXT,
    clv_segment     TEXT
);

CREATE TABLE IF NOT EXISTS dim_products (
    product_id      TEXT PRIMARY KEY,
    product_name    TEXT,
    category        TEXT,
    cost_price      REAL,
    selling_price   REAL
);

CREATE TABLE IF NOT EXISTS dim_time (
    date_id         TEXT PRIMARY KEY,   -- YYYY-MM-DD string
    date            TEXT,
    year            INTEGER,
    month           INTEGER,
    quarter         INTEGER,
    week_of_year    INTEGER,
    day_of_week     TEXT,
    month_label     TEXT
);

-- ─────────────────────────────────────────────
-- Fact Table
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        TEXT NOT NULL,
    customer_id     TEXT,
    product_id      TEXT,
    date_id         TEXT,
    region          TEXT,
    status          TEXT,
    quantity        REAL,
    price           REAL,
    revenue         REAL,
    cost            REAL,
    profit          REAL,
    profit_margin   REAL,
    return_flag     INTEGER DEFAULT 0,
    return_reason   TEXT,
    rfm_segment     TEXT,
    clv_segment     TEXT,
    cohort_month    TEXT,
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
    FOREIGN KEY (product_id)  REFERENCES dim_products(product_id),
    FOREIGN KEY (date_id)     REFERENCES dim_time(date_id)
);

-- ─────────────────────────────────────────────
-- Indexes for Query Optimization
-- ─────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_fact_customer  ON fact_sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_product   ON fact_sales(product_id);
CREATE INDEX IF NOT EXISTS idx_fact_date      ON fact_sales(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_region    ON fact_sales(region);
CREATE INDEX IF NOT EXISTS idx_fact_category  ON fact_sales(product_id);  -- join to dim_products
CREATE INDEX IF NOT EXISTS idx_dim_cat        ON dim_products(category);
CREATE INDEX IF NOT EXISTS idx_dim_time_month ON dim_time(year, month);

-- ─────────────────────────────────────────────
-- Analytical Views
-- ─────────────────────────────────────────────

DROP VIEW IF EXISTS vw_revenue_by_region;
CREATE VIEW vw_revenue_by_region AS
SELECT
    fs.region,
    SUM(fs.revenue)        AS total_revenue,
    SUM(fs.profit)         AS total_profit,
    COUNT(DISTINCT fs.order_id) AS total_orders,
    ROUND(AVG(fs.profit_margin), 2) AS avg_margin_pct
FROM fact_sales fs
GROUP BY fs.region
ORDER BY total_revenue DESC;

DROP VIEW IF EXISTS vw_category_performance;
CREATE VIEW vw_category_performance AS
SELECT
    dp.category,
    SUM(fs.revenue)        AS total_revenue,
    SUM(fs.profit)         AS total_profit,
    COUNT(DISTINCT fs.order_id) AS total_orders,
    ROUND(AVG(fs.profit_margin), 2) AS avg_margin_pct,
    ROUND(AVG(CAST(fs.return_flag AS REAL)) * 100, 2) AS return_rate_pct
FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id
GROUP BY dp.category
ORDER BY total_revenue DESC;

DROP VIEW IF EXISTS vw_monthly_revenue;
CREATE VIEW vw_monthly_revenue AS
SELECT
    dt.year,
    dt.month,
    dt.month_label,
    SUM(fs.revenue)  AS monthly_revenue,
    SUM(fs.profit)   AS monthly_profit,
    COUNT(DISTINCT fs.customer_id) AS active_customers
FROM fact_sales fs
JOIN dim_time dt ON fs.date_id = dt.date_id
GROUP BY dt.year, dt.month, dt.month_label
ORDER BY dt.year, dt.month;
