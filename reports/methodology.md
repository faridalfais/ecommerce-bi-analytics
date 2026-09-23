# E-Commerce Analytics Methodology & Data Lineage Document

## Data Lineage Architecture
```
Raw UCI Archive Zip (online+retail+ii.zip)
  │
  ▼
Python pandas Ingestion (loader.py)
  │
  ▼
Data Cleaning & Quality Audit (cleaner.py)
  │
  ▼
SQLite / PostgreSQL Fact & Dimensions (db_engine.py / schema.sql)
  │
  ▼
SQL Analytics Queries (database/queries/*.sql)
  │
  ▼
Python ML, Segmentation & Forecasting (rfm.py, churn_model.py, revenue_forecast.py)
  │
  ▼
Bilingual Interactive Streamlit Dashboard (dashboard/app.py)
```

## Calculation & Formula Specifications

### 1. Revenue
$$\text{Total Line Revenue} = \text{Quantity} \times \text{Unit Price}$$
Calculated strictly on non-cancelled invoices (`IsCancelled == False`, `Quantity > 0`, `Price > 0`).

### 2. Average Order Value (AOV)
$$\text{AOV} = \frac{\sum \text{Total Line Amount}}{\text{Count of Unique Invoices}}$$

### 3. Repeat Purchase Rate
$$\text{Repeat Purchase Rate} = \frac{\text{Count of Customers with Orders} > 1}{\text{Total Active Registered Customers}} \times 100$$

### 4. RFM Segmentation Scoring
- **Recency (R)**: Days elapsed between latest purchase and cutoff reference date (Quantile Score 1-5).
- **Frequency (F)**: Distinct invoice count per customer (Quantile Score 1-5).
- **Monetary (M)**: Total spend sum per customer (Quantile Score 1-5).

### 5. Forecasting Time-Series Models
- **Holt-Winters Exponential Smoothing**: Trend-adjusted additive smoothing.
- **SARIMA**: Seasonal Autoregressive Integrated Moving Average $(1, 1, 1)$.
- Evaluated via temporal train/test split using **MAE** (Mean Absolute Error) and **MAPE** (Mean Absolute Percentage Error).
