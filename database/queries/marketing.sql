-- Geographic Market & Country Breakdown Queries

-- Query 1: Country Sales Revenue, Volume, Orders, and Revenue Share
WITH country_metrics AS (
    SELECT
        country,
        COUNT(DISTINCT invoice_no) AS total_orders,
        COUNT(DISTINCT customer_id) AS total_customers,
        SUM(quantity) AS total_units_sold,
        ROUND(SUM(total_line_amount), 2) AS total_revenue
    FROM fact_transactions
    WHERE is_cancelled = 0 AND total_line_amount > 0
    GROUP BY country
)
SELECT
    country,
    total_orders,
    total_customers,
    total_units_sold,
    total_revenue,
    ROUND((total_revenue * 100.0) / (SELECT SUM(total_revenue) FROM country_metrics), 2) AS revenue_share_pct
FROM country_metrics
ORDER BY total_revenue DESC;

-- Query 2: Domestic (UK) vs International Revenue Summary
SELECT
    CASE WHEN country = 'United Kingdom' THEN 'Domestic (UK)' ELSE 'International' END AS market_segment,
    COUNT(DISTINCT invoice_no) AS total_orders,
    COUNT(DISTINCT customer_id) AS total_customers,
    ROUND(SUM(total_line_amount), 2) AS total_revenue,
    ROUND((SUM(total_line_amount) * 100.0) / (SELECT SUM(total_line_amount) FROM fact_transactions WHERE is_cancelled = 0), 2) AS revenue_share_pct
FROM fact_transactions
WHERE is_cancelled = 0 AND total_line_amount > 0
GROUP BY 1
ORDER BY total_revenue DESC;
