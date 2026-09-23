-- Revenue & Financial Performance Queries

-- Query 1: Monthly Revenue, Orders, Active Customers, AOV, and MoM Growth
WITH monthly_metrics AS (
    SELECT
        STRFTIME('%Y-%m', invoice_date) AS year_month,
        COUNT(DISTINCT invoice_no) AS total_orders,
        COUNT(DISTINCT customer_id) AS active_customers,
        SUM(quantity) AS total_units_sold,
        ROUND(SUM(total_line_amount), 2) AS monthly_revenue,
        ROUND(SUM(total_line_amount) / NULLIF(COUNT(DISTINCT invoice_no), 0), 2) AS average_order_value
    FROM fact_transactions
    WHERE is_cancelled = 0 AND total_line_amount > 0
    GROUP BY 1
)
SELECT
    year_month,
    total_orders,
    active_customers,
    total_units_sold,
    monthly_revenue,
    average_order_value,
    LAG(monthly_revenue) OVER (ORDER BY year_month) AS prev_month_revenue,
    ROUND(
        ((monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY year_month)) / NULLIF(LAG(monthly_revenue) OVER (ORDER BY year_month), 0)) * 100.0,
        2
    ) AS mom_growth_pct
FROM monthly_metrics
ORDER BY year_month ASC;

-- Query 2: Daily Revenue Trends
SELECT
    DATE(invoice_date) AS transaction_date,
    COUNT(DISTINCT invoice_no) AS daily_orders,
    ROUND(SUM(total_line_amount), 2) AS daily_revenue
FROM fact_transactions
WHERE is_cancelled = 0 AND total_line_amount > 0
GROUP BY 1
ORDER BY 1 ASC;
