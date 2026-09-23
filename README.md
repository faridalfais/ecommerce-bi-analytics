# E-Commerce Business Intelligence & Customer Analytics Platform

> **Production-Grade Portfolio Case Study**  
> An end-to-end Business Intelligence, SQL analytics, Machine Learning, Forecasting, and Executive Analytics platform built on ~1 million transactions from the official **UCI Online Retail II** dataset (2009–2011) enriched with **World Bank macro-economic indicators**.

---

## 1. Business Problem & Executive Objective
Management at a UK-based non-store online retailer wanted to address critical operational and strategic business questions:
- **Revenue & Profitability Drivers**: What products, customer segments, and geographic markets generate the majority of net revenue?
- **Customer Retention & Churn**: Which customer groups represent high lifetime value vs those at risk of becoming inactive/churning?
- **Future Growth & Uncertainty**: What is the 12-month expected revenue forecast and confidence interval?
- **Macro-Economic Context**: How do UK consumer inflation (CPI) and national economic growth correlate with retailer sales trends?

---

## 2. System Architecture & Data Pipeline

```
┌─────────────────────────┐     ┌────────────────────────┐
│  UCI Archive (Zip)      │     │  World Bank API (GBR)  │
│  ~1.06M Raw Records     │     │  CPI & GDP Indicators  │
└────────────┬────────────┘     └───────────┬────────────┘
             │                              │
             ▼                              ▼
┌────────────────────────────────────────────────────────┐
│  Python Data Ingestion & Cleaning Pipeline             │
│  - Ingestion: src/ingestion/loader.py                  │
│  - Cleaning & Quality Audit: src/cleaning/cleaner.py    │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────┐
│  Database Layer (PostgreSQL / SQLite Engine)           │
│  - DDL Schema: database/schema.sql                      │
│  - Engine Wrapper: src/analytics/db_engine.py          │
│  - Fact Table: fact_transactions                       │
│  - Dimensions: dim_customer, dim_product, dim_date     │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────┐
│  SQL & Python Analytics Engine                         │
│  - SQL Query Library: database/queries/*.sql           │
│  - RFM & K-Means: src/segmentation/rfm.py              │
│  - Churn Modeling: src/ml/churn_model.py               │
│  - IsolationForest Anomaly: src/anomaly/anomaly.py     │
│  - Revenue Forecasting: src/forecasting/revenue.py     │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────┐
│  Executive Streamlit BI Dashboard (Multi-Page & i18n)  │
│  - Pages: Executive Overview, Finance, Customers, etc. │
│  - Bilingual UI Selector: English 🇬🇧 / Indonesian 🇮🇩   │
└────────────────────────────────────────────────────────┘
```

---

## 3. Data Sources & Attribution

### Primary Transaction Dataset
- **Source**: UCI Machine Learning Repository — Online Retail II
- **URL**: [https://archive.ics.uci.edu/dataset/502/online+retail+ii](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
- **Timeframe**: December 1, 2009 – December 9, 2011
- **Record Count**: 1,067,371 raw invoice lines
- **Description**: Contains real transaction records for a UK-based registered online retailer primarily selling unique all-occasion giftware.

### External Macro-Economic Dataset
- **Source**: World Bank Open Data API
- **URL**: [http://api.worldbank.org/v2/country/GBR/indicator/](http://api.worldbank.org/v2/country/GBR/indicator/)
- **Retrieved**: Live via `src/external_data/economic_api.py`
- **Indicators**:
  - `FP.CPI.TOTL.ZG`: Inflation, consumer prices (annual %)
  - `NY.GDP.MKTP.KD.ZG`: GDP growth (annual %)
  - `NE.CON.PRVT.CD`: Household final consumption expenditure (US$)

---

## 4. Key Performance Indicator (KPI) Definitions

| Metric Name | Mathematical Definition | Business Relevance |
| :--- | :--- | :--- |
| **Total Revenue** | $\sum (\text{Quantity} \times \text{Unit Price})$ for non-cancelled sales | Top-line financial measure of net gross sales volume. |
| **Average Order Value (AOV)** | $\frac{\text{Total Revenue}}{\text{Count of Unique Invoices}}$ | Evaluates purchasing basket size per transaction. |
| **Average Revenue Per User (ARPU)** | $\frac{\text{Total Revenue}}{\text{Count of Registered Active Customers}}$ | Evaluates revenue intensity per registered buyer. |
| **Repeat Purchase Rate** | $\frac{\text{Customers with Orders} > 1}{\text{Total Active Customers}} \times 100\%$ | Quantifies customer retention and repeat loyalty. |
| **MoM Growth Rate** | $\frac{\text{Revenue}_t - \text{Revenue}_{t-1}}{\text{Revenue}_{t-1}} \times 100\%$ | Tracks monthly growth velocity. |

> **Financial Integrity Note**: Per strict analytical guidelines, unit costs (COGS) are not present in the raw source dataset. Revenue is reported cleanly as baseline truth without fabricating cost or ROI figures.

---

## 5. Machine Learning & Forecasting Methodology

### Customer RFM & K-Means Clustering
- **Feature Processing**: Log-transformation ($\ln(1+x)$) on Recency, Frequency, Monetary metrics to correct skewness, followed by `StandardScaler`.
- **Optimal Cluster Selection**: Evaluated using Silhouette scores across $K \in [2, 6]$.
- **Segment Profiles**: Classifies buyers into Champions, Loyal Customers, Potential Loyalists, At Risk, and Hibernating / Lost.

### Inactivity / Churn Prediction Model
- **Target Label**: Customers who made zero purchases in the 90-day follow-up window post cutoff date.
- **Model Comparison**: Benchmarked Logistic Regression (Baseline), Random Forest, and Gradient Boosting.
- **Metrics Evaluated**: Precision, Recall, F1-Score, ROC-AUC, and Confusion Matrix.

### Time-Series Revenue Forecasting
- **Monthly Resampling**: 24-month historical monthly revenue series.
- **Models Benchmarked**: Naive Baseline, Holt-Winters Exponential Smoothing, and SARIMA $(1, 1, 1)$.
- **Evaluation**: Temporal train/test split evaluated using Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Mean Absolute Percentage Error (MAPE).
- **Projections**: Outputs 6-12 month future forecasts with 80% and 95% confidence intervals.

---

## 6. How to Run Locally

### Prerequisites
- Python 3.10+
- Virtual environment (recommended)

### Installation & Execution

```bash
# 1. Clone repository & enter project directory
cd ecommerce-bi-analytics

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create active environment configuration
cp .env.example .env

# 4. Run full end-to-end automated pipeline
python run_pipeline.py

# 5. Launch interactive bilingual BI dashboard
streamlit run dashboard/app.py

# 6. Run automated test suite
pytest tests/ -v
```

---

## 7. How to Add Your Own Dataset

The platform includes a standardized data-import and validation system allowing you to plug in your own transaction data without altering core analytics code.

### Step-by-Step Workflow:

1. **Place your dataset in `data/raw/custom/`**:
   Drop your `.csv`, `.parquet`, or `.xlsx` file into `data/raw/custom/` (e.g. `data/raw/custom/sales_2024.csv`).

2. **Define column mapping (if required)**:
   If your headers differ from standard names, create `data/raw/custom/column_mapping.json`:
   ```json
   {
     "order_id": "Invoice",
     "transaction_time": "InvoiceDate",
     "item_sku": "StockCode",
     "item_title": "Description",
     "units_ordered": "Quantity",
     "item_price": "Price",
     "user_id": "CustomerID",
     "market_country": "Country"
   }
   ```
   *Note: Common aliases like `transaction_id`, `order_date`, `product_id`, `unit_price`, and `customer_id` are automatically recognized even without a config file.*

3. **Run validation & pipeline**:
   ```bash
   python run_pipeline.py
   ```

4. **Review the Data Quality Audit Report**:
   Inspect `data/processed/data_quality_report.md` for duplicate counts, cancellations, and record hygiene statistics.

5. **Launch the Dashboard**:
   ```bash
   streamlit run dashboard/app.py
   ```

---

## 8. Project Structure

```
ecommerce-bi-analytics/
├── data/                       # Ingested, processed & external datasets
│   ├── raw/
│   │   ├── ecommerce/          # Default UCI Online Retail II dataset
│   │   └── custom/             # Drop-in folder for custom datasets
│   ├── processed/              # Cleaned Parquet tables & quality reports
│   └── external/               # World Bank API macro-economic data
├── database/                   # DDL schema, seeds, and SQL queries
│   └── queries/                # revenue.sql, customer.sql, product.sql, retention.sql, marketing.sql
├── src/                        # Modular Python source modules
│   ├── ingestion/              # loader.py & config.py
│   ├── cleaning/               # cleaner.py, validator.py & data_quality.py
│   ├── analytics/              # db_engine.py & metrics.py
│   ├── segmentation/           # rfm.py
│   ├── ml/                     # clustering.py & churn_model.py
│   ├── anomaly/                # anomaly_detector.py
│   ├── forecasting/            # revenue_forecast.py
│   ├── external_data/          # economic_api.py
│   └── utils/                  # logger.py & i18n.py
├── dashboard/                  # Streamlit Multi-page application
│   ├── app.py                  # Main dashboard shell
│   ├── pages/                  # 7 Multi-page views
│   ├── components/             # KPI cards, Plotly charts, Insights box
│   └── locales/                # en.json & id.json
├── reports/                    # Generated Markdown executive summaries
├── notebooks/                  # Step-by-step exploratory Jupyter notebooks
├── tests/                      # Pytest test suite
├── .env.example
├── requirements.txt
├── README.md
└── run_pipeline.py             # Reproducible pipeline orchestrator
```

---

## 9. Limitations & Future Improvements
1. **COGS / Margin Data**: Raw dataset does not contain unit cost of goods. Integrating supplier cost feeds will enable true Net Margin analysis.
2. **Real-time Streaming**: Future architecture could ingest live transaction webhooks into Kafka / PostgreSQL for real-time operational monitoring.

