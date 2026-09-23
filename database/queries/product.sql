-- Product Performance & Pareto Analytics Queries

-- Query 1: Top 20 Products by Sales Revenue & Volume
SELECT
    stock_code,
    description,
    SUM(quantity) AS total_units_sold,
    COUNT(DISTINCT invoice_no) AS total_orders,
    ROUND(SUM(total_line_amount), 2) AS total_revenue,
    ROUND(AVG(unit_price), 2) AS avg_unit_price
FROM fact_transactions
WHERE is_cancelled = 0 AND total_line_amount > 0
GROUP BY stock_code, description
ORDER BY total_revenue DESC
LIMIT 20;

-- Query 2: Product Cumulative Revenue Pareto Contribution
WITH product_revenue AS (
    SELECT
        stock_code,
        MAX(description) AS description,
        SUM(total_line_amount) AS revenue
    FROM fact_transactions
    WHERE is_cancelled = 0 AND total_line_amount > 0
    GROUP BY stock_code
),
ranked_products AS (
    SELECT
        stock_code,
        description,
        revenue,
        SUM(revenue) OVER (ORDER BY revenue DESC) AS cumulative_revenue,
        SUM(revenue) OVER () AS total_company_revenue
    FROM product_revenue
)
SELECT
    stock_code,
    description,
    ROUND(revenue, 2) AS revenue,
    ROUND(cumulative_revenue, 2) AS cumulative_revenue,
    ROUND((cumulative_revenue / total_company_revenue) * 100.0, 2) AS cumulative_revenue_pct
FROM ranked_products
ORDER BY revenue DESC;
