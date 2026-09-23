-- E-Commerce BI Analytics Normalized Schema
-- Compatible with PostgreSQL and SQLite

DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_country;

-- Fact Table: Sales Transactions
CREATE TABLE fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no VARCHAR(20) NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL,
    invoice_date TIMESTAMP NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    total_line_amount NUMERIC(12, 2) NOT NULL,
    customer_id VARCHAR(20),
    country VARCHAR(100) NOT NULL,
    is_cancelled BOOLEAN DEFAULT FALSE
);

-- Dimension: Customers
CREATE TABLE dim_customer (
    customer_id VARCHAR(20) PRIMARY KEY,
    country VARCHAR(100),
    first_purchase_date TIMESTAMP,
    last_purchase_date TIMESTAMP,
    total_orders INTEGER,
    total_spend NUMERIC(12, 2)
);

-- Dimension: Products
CREATE TABLE dim_product (
    stock_code VARCHAR(20) PRIMARY KEY,
    description TEXT,
    latest_unit_price NUMERIC(10, 2),
    total_units_sold INTEGER,
    total_revenue NUMERIC(12, 2)
);

-- Dimension: Calendar Date
CREATE TABLE dim_date (
    date_key DATE PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    day INTEGER NOT NULL,
    day_name VARCHAR(15) NOT NULL,
    quarter INTEGER NOT NULL
);

-- Dimension: Country
CREATE TABLE dim_country (
    country_name VARCHAR(100) PRIMARY KEY,
    is_domestic BOOLEAN DEFAULT FALSE
);

-- Indexes for Query Performance
CREATE INDEX idx_fact_invoice_date ON fact_transactions(invoice_date);
CREATE INDEX idx_fact_customer_id ON fact_transactions(customer_id);
CREATE INDEX idx_fact_stock_code ON fact_transactions(stock_code);
CREATE INDEX idx_fact_country ON fact_transactions(country);
