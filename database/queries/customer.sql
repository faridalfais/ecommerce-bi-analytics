-- Customer Analytics & Segmentation Queries

-- Query 1: Customer First Purchase Cohort Assignment & Overall Summary
SELECT
    c.customer_id,
    c.country,
    c.first_purchase_date,
    c.last_purchase_date,
    c.total_orders,
    c.total_spend,
    ROUND(c.total_spend / NULLIF(c.total_orders, 0), 2) AS avg_order_value
FROM dim_customer c
ORDER BY c.total_spend DESC;

-- Query 2: New vs Returning Customers by Month
WITH customer_first_orders AS (
    SELECT
        customer_id,
        MIN(STRFTIME('%Y-%m', invoice_date)) AS cohort_month
    FROM fact_transactions
    WHERE is_cancelled = 0 AND customer_id IS NOT NULL
    GROUP BY 1
),
monthly_customer_activity AS (
    SELECT DISTINCT
        STRFTIME('%Y-%m', invoice_date) AS active_month,
        customer_id
    FROM fact_transactions
    WHERE is_cancelled = 0 AND customer_id IS NOT NULL
)
SELECT
    m.active_month,
    COUNT(DISTINCT m.customer_id) AS total_active_customers,
    COUNT(DISTINCT CASE WHEN c.cohort_month = m.active_month THEN m.customer_id END) AS new_customers,
    COUNT(DISTINCT CASE WHEN c.cohort_month < m.active_month THEN m.customer_id END) AS returning_customers
FROM monthly_customer_activity m
JOIN customer_first_orders c ON m.customer_id = c.customer_id
GROUP BY 1
ORDER BY 1 ASC;
