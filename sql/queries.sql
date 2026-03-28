-- ============================================================
-- queries.sql — Analytical SQL Queries
-- Sales Analytics System
-- ============================================================

-- ─────────────────────────────────────────────
-- 1. Revenue by Region
-- ─────────────────────────────────────────────
-- Q1: Revenue, profit, and order count by region
SELECT
    fs.region,
    ROUND(SUM(fs.revenue), 2)                                AS total_revenue,
    ROUND(SUM(fs.profit), 2)                                 AS total_profit,
    COUNT(DISTINCT fs.order_id)                              AS total_orders,
    ROUND(SUM(fs.revenue) * 100.0 / SUM(SUM(fs.revenue))
          OVER (), 2)                                        AS revenue_share_pct,
    ROUND(AVG(fs.profit_margin), 2)                          AS avg_margin_pct
FROM fact_sales fs
GROUP BY fs.region
ORDER BY total_revenue DESC;

-- ─────────────────────────────────────────────
-- 2. Top-Selling Products (by Revenue)
-- ─────────────────────────────────────────────
SELECT
    dp.product_id,
    dp.product_name,
    dp.category,
    ROUND(SUM(fs.revenue), 2)   AS total_revenue,
    ROUND(SUM(fs.profit), 2)    AS total_profit,
    SUM(fs.quantity)            AS units_sold,
    ROUND(AVG(fs.price), 2)     AS avg_price
FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id
GROUP BY dp.product_id, dp.product_name, dp.category
ORDER BY total_revenue DESC
LIMIT 20;

-- ─────────────────────────────────────────────
-- 3. Monthly Revenue + Growth Rate (MoM %)
-- ─────────────────────────────────────────────
WITH monthly AS (
    SELECT
        dt.year,
        dt.month,
        dt.month_label,
        ROUND(SUM(fs.revenue), 2)  AS monthly_revenue,
        ROUND(SUM(fs.profit), 2)   AS monthly_profit
    FROM fact_sales fs
    JOIN dim_time dt ON fs.date_id = dt.date_id
    GROUP BY dt.year, dt.month, dt.month_label
    ORDER BY dt.year, dt.month
),
monthly_with_lag AS (
    SELECT
        *,
        LAG(monthly_revenue) OVER (ORDER BY year, month) AS prev_revenue
    FROM monthly
)
SELECT
    year, month, month_label,
    monthly_revenue,
    monthly_profit,
    prev_revenue,
    ROUND(
        CASE
            WHEN prev_revenue IS NULL OR prev_revenue = 0 THEN NULL
            ELSE (monthly_revenue - prev_revenue) * 100.0 / prev_revenue
        END, 2
    ) AS mom_growth_pct
FROM monthly_with_lag
ORDER BY year, month;

-- ─────────────────────────────────────────────
-- 4. Category-wise Profit Margin
-- ─────────────────────────────────────────────
SELECT
    dp.category,
    ROUND(SUM(fs.revenue), 2)                               AS total_revenue,
    ROUND(SUM(fs.profit), 2)                                AS total_profit,
    ROUND(SUM(fs.profit) * 100.0 / NULLIF(SUM(fs.revenue), 0), 2) AS profit_margin_pct,
    COUNT(DISTINCT fs.order_id)                             AS total_orders,
    ROUND(AVG(CAST(fs.return_flag AS REAL)) * 100.0, 2)    AS return_rate_pct
FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id
GROUP BY dp.category
HAVING SUM(fs.revenue) > 0
ORDER BY profit_margin_pct DESC;

-- ─────────────────────────────────────────────
-- 5. Customer Segmentation by CLV
-- ─────────────────────────────────────────────
SELECT
    clv_segment,
    COUNT(DISTINCT customer_id)                 AS customer_count,
    ROUND(SUM(revenue), 2)                      AS total_revenue,
    ROUND(SUM(revenue) * 100.0 / SUM(SUM(revenue)) OVER (), 2) AS revenue_share_pct,
    ROUND(AVG(clv), 2)                          AS avg_clv
FROM fact_sales
GROUP BY clv_segment
ORDER BY avg_clv DESC;

-- ─────────────────────────────────────────────
-- 6. Return Rate by Category
-- ─────────────────────────────────────────────
SELECT
    dp.category,
    COUNT(fs.order_id)                                       AS total_orders,
    SUM(fs.return_flag)                                      AS total_returns,
    ROUND(SUM(fs.return_flag) * 100.0 / COUNT(fs.order_id), 2) AS return_rate_pct
FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id
GROUP BY dp.category
ORDER BY return_rate_pct DESC;

-- ─────────────────────────────────────────────
-- 7. RFM Segment Distribution
-- ─────────────────────────────────────────────
SELECT
    rfm_segment,
    COUNT(DISTINCT customer_id)  AS customer_count,
    ROUND(SUM(revenue), 2)       AS total_revenue,
    ROUND(AVG(revenue), 2)       AS avg_revenue_per_order
FROM fact_sales
GROUP BY rfm_segment
ORDER BY total_revenue DESC;

-- ─────────────────────────────────────────────
-- 8. Quarterly Revenue Trend
-- ─────────────────────────────────────────────
SELECT
    dt.year,
    dt.quarter,
    ROUND(SUM(fs.revenue), 2)   AS quarterly_revenue,
    ROUND(SUM(fs.profit), 2)    AS quarterly_profit,
    COUNT(DISTINCT fs.customer_id) AS active_customers
FROM fact_sales fs
JOIN dim_time dt ON fs.date_id = dt.date_id
GROUP BY dt.year, dt.quarter
ORDER BY dt.year, dt.quarter;

-- ─────────────────────────────────────────────
-- 9. Top 10% Customers Revenue Contribution
-- ─────────────────────────────────────────────
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(revenue) AS cust_revenue,
        NTILE(10) OVER (ORDER BY SUM(revenue) DESC) AS decile
    FROM fact_sales
    GROUP BY customer_id
)
SELECT
    decile,
    COUNT(customer_id)              AS customer_count,
    ROUND(SUM(cust_revenue), 2)     AS segment_revenue,
    ROUND(SUM(cust_revenue) * 100.0 / SUM(SUM(cust_revenue)) OVER (), 2) AS revenue_share_pct
FROM customer_revenue
GROUP BY decile
ORDER BY decile;

-- ─────────────────────────────────────────────
-- 10. Region × Category Revenue Cross-Tab
-- ─────────────────────────────────────────────
SELECT
    fs.region,
    dp.category,
    ROUND(SUM(fs.revenue), 2)   AS revenue,
    ROUND(SUM(fs.profit), 2)    AS profit,
    COUNT(DISTINCT fs.order_id) AS orders
FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id
GROUP BY fs.region, dp.category
ORDER BY fs.region, revenue DESC;
