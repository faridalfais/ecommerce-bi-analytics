-- Customer Retention & Cohort Matrix Queries

-- Query 1: Cohort Analysis Matrix (Acquisition Month vs Month Index Retention)
WITH customer_cohort AS (
    SELECT
        customer_id,
        MIN(STRFTIME('%Y-%m', invoice_date)) AS cohort_month
    FROM fact_transactions
    WHERE is_cancelled = 0 AND customer_id IS NOT NULL
    GROUP BY customer_id
),
customer_activity AS (
    SELECT DISTINCT
        customer_id,
        STRFTIME('%Y-%m', invoice_date) AS activity_month
    FROM fact_transactions
    WHERE is_cancelled = 0 AND customer_id IS NOT NULL
),
cohort_size AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_id) AS initial_cohort_size
    FROM customer_cohort
    GROUP BY cohort_month
),
retention_matrix AS (
    SELECT
        c.cohort_month,
        a.activity_month,
        -- Month index difference
        (CAST(STRFTIME('%Y', a.activity_month || '-01') AS INT) - CAST(STRFTIME('%Y', c.cohort_month || '-01') AS INT)) * 12 +
        (CAST(STRFTIME('%m', a.activity_month || '-01') AS INT) - CAST(STRFTIME('%m', c.cohort_month || '-01') AS INT)) AS month_index,
        COUNT(DISTINCT a.customer_id) AS active_retained_customers
    FROM customer_activity a
    JOIN customer_cohort c ON a.customer_id = c.customer_id
    GROUP BY 1, 2, 3
)
SELECT
    r.cohort_month,
    cs.initial_cohort_size,
    r.month_index,
    r.active_retained_customers,
    ROUND((r.active_retained_customers * 100.0) / cs.initial_cohort_size, 2) AS retention_rate_pct
FROM retention_matrix r
JOIN cohort_size cs ON r.cohort_month = cs.cohort_month
ORDER BY r.cohort_month ASC, r.month_index ASC;

-- Query 2: Overall Customer Repeat Purchase Rate
WITH customer_order_counts AS (
    SELECT
        customer_id,
        COUNT(DISTINCT invoice_no) AS total_orders
    FROM fact_transactions
    WHERE is_cancelled = 0 AND customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT
    COUNT(customer_id) AS total_customers,
    SUM(CASE WHEN total_orders > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND((SUM(CASE WHEN total_orders > 1 THEN 1 ELSE 0 END) * 100.0) / COUNT(customer_id), 2) AS repeat_purchase_rate_pct
FROM customer_order_counts;
