-- =============================================================================
-- E-Commerce Customer Analytics — SQL Queries (Small Dataset: 50 customers)
-- Compatible with: PostgreSQL 14+ / SQLite 3.35+
-- =============================================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id   TEXT PRIMARY KEY,
    age           INTEGER,
    gender        TEXT,
    region        TEXT,
    signup_date   DATE,
    loyalty_tier  TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   TEXT PRIMARY KEY,
    customer_id      TEXT REFERENCES customers(customer_id),
    transaction_date DATE,
    category         TEXT,
    quantity         INTEGER,
    unit_price       NUMERIC(10,2),
    discount         NUMERIC(5,2),
    channel          TEXT,
    returned         INTEGER,
    total_amount     NUMERIC(10,2),
    net_amount       NUMERIC(10,2)
);

-- ============================================================================
-- QUERY 1: Monthly Revenue
-- ============================================================================
SELECT
    TO_CHAR(transaction_date, 'YYYY-MM')  AS month,
    COUNT(DISTINCT transaction_id)         AS num_transactions,
    COUNT(DISTINCT customer_id)            AS unique_buyers,
    ROUND(SUM(net_amount)::NUMERIC, 2)     AS net_revenue
FROM transactions WHERE returned = 0
GROUP BY 1 ORDER BY 1;

-- ============================================================================
-- QUERY 2: Revenue by Category
-- ============================================================================
SELECT
    category,
    COUNT(transaction_id)                  AS num_orders,
    ROUND(SUM(net_amount)::NUMERIC, 2)     AS total_revenue,
    ROUND(AVG(unit_price)::NUMERIC, 2)     AS avg_unit_price,
    ROUND(100.0 * SUM(net_amount) /
          SUM(SUM(net_amount)) OVER (), 1) AS revenue_share_pct
FROM transactions
GROUP BY 1 ORDER BY total_revenue DESC;

-- ============================================================================
-- QUERY 3: Repeat Customers
-- ============================================================================
WITH order_counts AS (
    SELECT customer_id, COUNT(transaction_id) AS num_orders
    FROM transactions GROUP BY 1
)
SELECT
    CASE
        WHEN num_orders = 1            THEN 'One-Time'
        WHEN num_orders BETWEEN 2 AND 5 THEN 'Repeat (2-5)'
        ELSE                                'Loyal (6+)'
    END                                    AS customer_type,
    COUNT(*)                               AS num_customers,
    ROUND(AVG(num_orders)::NUMERIC, 1)     AS avg_orders
FROM order_counts
GROUP BY 1 ORDER BY num_customers DESC;

-- ============================================================================
-- QUERY 4: Customer Lifetime Value
-- ============================================================================
WITH stats AS (
    SELECT
        customer_id,
        COUNT(transaction_id)                AS num_orders,
        ROUND(SUM(net_amount)::NUMERIC, 2)   AS total_spend,
        ROUND(AVG(net_amount)::NUMERIC, 2)   AS avg_order,
        GREATEST(MAX(transaction_date) - MIN(transaction_date), 1) AS tenure_days
    FROM transactions WHERE returned = 0
    GROUP BY 1
)
SELECT
    c.customer_id, c.loyalty_tier, c.region,
    s.num_orders, s.total_spend, s.avg_order,
    ROUND(s.avg_order * (s.num_orders::NUMERIC / (s.tenure_days/365.0)) * 3, 2) AS clv_3yr
FROM stats s JOIN customers c USING (customer_id)
ORDER BY clv_3yr DESC;

-- ============================================================================
-- QUERY 5: RFM Segments
-- ============================================================================
WITH snapshot AS (SELECT MAX(transaction_date) AS snap FROM transactions),
rfm_raw AS (
    SELECT customer_id,
        (SELECT snap FROM snapshot) - MAX(transaction_date) AS recency_days,
        COUNT(transaction_id)                               AS frequency,
        ROUND(SUM(net_amount)::NUMERIC, 2)                  AS monetary
    FROM transactions WHERE returned = 0
    GROUP BY 1
),
rfm_scored AS (
    SELECT *,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(4) OVER (ORDER BY frequency)          AS f_score,
        NTILE(4) OVER (ORDER BY monetary)            AS m_score
    FROM rfm_raw
)
SELECT
    CASE
        WHEN r_score+f_score+m_score >= 10 THEN 'Champions'
        WHEN r_score+f_score+m_score >= 7  THEN 'Loyal'
        WHEN r_score+f_score+m_score >= 5  THEN 'Potential'
        WHEN r_score+f_score+m_score >= 3  THEN 'At Risk'
        ELSE 'Lost'
    END AS segment,
    COUNT(*)                               AS num_customers,
    ROUND(AVG(recency_days)::NUMERIC, 0)   AS avg_recency,
    ROUND(AVG(frequency)::NUMERIC, 1)      AS avg_orders,
    ROUND(AVG(monetary)::NUMERIC, 2)       AS avg_spend
FROM rfm_scored
GROUP BY 1 ORDER BY avg_spend DESC;

-- ============================================================================
-- QUERY 6: Spending Tier Segmentation
-- ============================================================================
WITH totals AS (
    SELECT customer_id, ROUND(SUM(net_amount)::NUMERIC, 2) AS total_spend
    FROM transactions WHERE returned = 0 GROUP BY 1
),
tiered AS (
    SELECT *,
        CASE
            WHEN total_spend < 150                THEN '1_Budget (<$150)'
            WHEN total_spend BETWEEN 150 AND 499  THEN '2_Mid-Range ($150-$500)'
            WHEN total_spend BETWEEN 500 AND 1199 THEN '3_High-Value ($500-$1.2K)'
            ELSE                                      '4_Premium (>$1.2K)'
        END AS spend_tier
    FROM totals
)
SELECT
    spend_tier,
    COUNT(*)                               AS num_customers,
    ROUND(AVG(total_spend)::NUMERIC, 2)    AS avg_spend,
    ROUND(SUM(total_spend)::NUMERIC, 2)    AS tier_revenue,
    ROUND(100.0 * SUM(total_spend) /
          SUM(SUM(total_spend)) OVER (), 1) AS revenue_share_pct
FROM tiered GROUP BY 1 ORDER BY 1;

-- ============================================================================
-- QUERY 7: Churn Risk — No purchase in 90+ days
-- ============================================================================
WITH latest AS (SELECT MAX(transaction_date) AS snap FROM transactions),
last_buy AS (
    SELECT customer_id,
        MAX(transaction_date)                         AS last_txn,
        COUNT(transaction_id)                         AS total_orders,
        ROUND(SUM(net_amount)::NUMERIC, 2)            AS total_spend,
        (SELECT snap FROM latest) - MAX(transaction_date) AS days_since
    FROM transactions WHERE returned = 0 GROUP BY 1
)
SELECT lb.*, c.loyalty_tier, c.region
FROM last_buy lb JOIN customers c USING (customer_id)
WHERE days_since > 90
ORDER BY total_spend DESC;

-- ============================================================================
-- QUERY 8: Revenue by Region and Category (heatmap data)
-- ============================================================================
SELECT
    c.region, t.category,
    ROUND(SUM(t.net_amount)::NUMERIC, 2) AS revenue
FROM transactions t
JOIN customers c USING (customer_id)
WHERE t.returned = 0
GROUP BY 1, 2
ORDER BY 1, revenue DESC;
