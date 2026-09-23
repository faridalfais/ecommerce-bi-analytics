import os
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

from src.utils.logger import get_logger
from src.ingestion.loader import load_raw_data
from src.cleaning.cleaner import clean_transaction_data
from src.cleaning.data_quality import generate_data_quality_report
from src.analytics.db_engine import get_db_engine, init_database_schema, populate_database, run_sql_query
from src.analytics.metrics import compute_overall_kpis, generate_executive_insights
from src.segmentation.rfm import calculate_rfm, get_rfm_segment_summary
from src.ml.clustering import run_kmeans_segmentation
from src.ml.churn_model import train_churn_prediction_model
from src.anomaly.anomaly_detector import detect_revenue_anomalies
from src.forecasting.revenue_forecast import forecast_monthly_revenue
from src.external_data.economic_api import fetch_world_bank_data

logger = get_logger("pipeline_orchestrator")

def run_full_pipeline():
    """Execute complete reproducible E-Commerce BI Analytics pipeline."""
    start_time = datetime.now()
    logger.info("==========================================================")
    logger.info("  STARTING E-COMMERCE BI & CUSTOMER ANALYTICS PIPELINE")
    logger.info("==========================================================")
    
    # 1. Raw Ingestion
    logger.info("[Step 1/9] Ingesting UCI Raw Transaction Dataset...")
    raw_df = load_raw_data()
    
    # 2. Data Cleaning & Validation
    logger.info("[Step 2/9] Cleaning & Validating Transactions...")
    df_clean, quality_summary = clean_transaction_data(raw_df, save_processed=True)
    generate_data_quality_report(quality_summary)
    
    # 3. Database Schema & Seeding
    logger.info("[Step 3/9] Initializing Database & Loading Fact/Dimensions...")
    engine = get_db_engine()
    init_database_schema(engine)
    populate_database(df_clean, engine)
    
    # 4. SQL Analytics Queries Execution
    logger.info("[Step 4/9] Executing SQL Analytical Query Suite...")
    rev_sql = run_sql_query("revenue.sql", engine)
    cust_sql = run_sql_query("customer.sql", engine)
    prod_sql = run_sql_query("product.sql", engine)
    ret_sql = run_sql_query("retention.sql", engine)
    mkt_sql = run_sql_query("marketing.sql", engine)
    logger.info(f"SQL Execution finished successfully. Monthly revenue records: {len(rev_sql)}")
    
    # 5. RFM & K-Means Customer Segmentation
    logger.info("[Step 5/9] Calculating Customer RFM & K-Means Clustering...")
    rfm_df = calculate_rfm(df_clean)
    rfm_df, kmeans_summary = run_kmeans_segmentation(rfm_df)
    rfm_summary = get_rfm_segment_summary(rfm_df)
    
    # 6. ML Churn Prediction Model
    logger.info("[Step 6/9] Training Inactivity / Churn Prediction Models...")
    churn_results = train_churn_prediction_model(df_clean)
    
    # 7. Anomaly Detection
    logger.info("[Step 7/9] Running IsolationForest & Z-Score Anomaly Detector...")
    anomalies_df = detect_revenue_anomalies(df_clean)
    
    # 8. Revenue Time-Series Forecasting
    logger.info("[Step 8/9] Building Revenue Time-Series Forecast...")
    forecast_results = forecast_monthly_revenue(df_clean)
    
    # 9. External Economic Context & Executive Reports
    logger.info("[Step 9/9] Fetching World Bank Macro Data & Generating Executive Report...")
    try:
        macro_df = fetch_world_bank_data()
    except Exception as e:
        logger.warning(f"Could not fetch World Bank API: {e}")
        macro_df = pd.DataFrame()
        
    kpis = compute_overall_kpis(df_clean)
    insights = generate_executive_insights(kpis, rfm_summary, forecast_results)
    
    generate_executive_report_files(kpis, quality_summary, rfm_summary, churn_results, forecast_results, insights)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("==========================================================")
    logger.info(f"  PIPELINE EXECUTION COMPLETED SUCCESSFULLY IN {elapsed:.2f}s")
    logger.info("==========================================================")

def generate_executive_report_files(kpis, quality_summary, rfm_summary, churn_results, forecast_results, insights):
    """Generate Markdown Reports in reports/ directory."""
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Executive Summary Report
    exec_path = reports_dir / "executive_summary.md"
    ins_en = insights.get("en", {})
    
    exec_content = f"""# E-Commerce Executive Business Intelligence Summary Report

## 1. Top-Level Key Performance Indicators (KPIs)
- **Total Cumulative Revenue**: £{kpis['total_revenue']:,.2f}
- **Total Completed Orders**: {kpis['total_orders']:,}
- **Total Units Sold**: {kpis['total_units_sold']:,}
- **Registered Active Customers**: {kpis['active_customers']:,}
- **Average Order Value (AOV)**: £{kpis['average_order_value']:.2f}
- **Average Revenue Per Customer (ARPU)**: £{kpis['average_revenue_per_user']:.2f}
- **Customer Repeat Purchase Rate**: {kpis['repeat_purchase_rate_pct']}%
- **Latest MoM Revenue Growth**: {kpis['latest_mom_growth_pct']}%
- **Domestic (UK) Revenue Concentration**: {kpis['uk_revenue_share_pct']}%

---

## 2. Automated Executive Decision Narrative

### WHAT HAPPENED?
{ins_en.get('what_happened', '')}

### WHY?
{ins_en.get('why', '')}

### BUSINESS IMPACT
{ins_en.get('business_impact', '')}

### WHAT SHOULD MANAGEMENT WATCH?
{ins_en.get('what_should_management_watch', '')}

---

## 3. Customer RFM Segmentation & Revenue Contribution
| Segment Name | Customer Count | Avg Recency (Days) | Avg Frequency | Total Revenue (£) | Revenue Share (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for _, row in rfm_summary.iterrows():
        exec_content += f"| {row['Segment']} | {row['CustomerCount']:,} | {row['AvgRecencyDays']} | {row['AvgFrequency']} | £{row['TotalRevenue']:,.2f} | {row['RevenueSharePct']}% |\n"

    exec_content += f"""
---

## 4. Machine Learning & Predictive Analytics Overview
- **Customer Inactivity Churn Predictor**: Best Model = **{churn_results['best_model_name']}** (F1-Score = {churn_results['model_metrics'][churn_results['best_model_name']]['f1_score']})
- **Revenue Time-Series Forecasting**: Best Model = **{forecast_results['best_model_name']}** (MAE = £{forecast_results['evaluations'][forecast_results['best_model_name']]['MAE']:,.2f})

---
*Report generated automatically by E-Commerce BI Analytics Pipeline on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.*
"""
    with open(exec_path, "w", encoding="utf-8") as f:
        f.write(exec_content)
        
    # 2. Methodology & Data Lineage Report
    method_path = reports_dir / "methodology.md"
    method_content = f"""# E-Commerce Analytics Methodology & Data Lineage Document

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
$$\\text{{Total Line Revenue}} = \\text{{Quantity}} \\times \\text{{Unit Price}}$$
Calculated strictly on non-cancelled invoices (`IsCancelled == False`, `Quantity > 0`, `Price > 0`).

### 2. Average Order Value (AOV)
$$\\text{{AOV}} = \\frac{{\\sum \\text{{Total Line Amount}}}}{{\\text{{Count of Unique Invoices}}}}$$

### 3. Repeat Purchase Rate
$$\\text{{Repeat Purchase Rate}} = \\frac{{\\text{{Count of Customers with Orders}} > 1}}{{\\text{{Total Active Registered Customers}}}} \\times 100$$

### 4. RFM Segmentation Scoring
- **Recency (R)**: Days elapsed between latest purchase and cutoff reference date (Quantile Score 1-5).
- **Frequency (F)**: Distinct invoice count per customer (Quantile Score 1-5).
- **Monetary (M)**: Total spend sum per customer (Quantile Score 1-5).

### 5. Forecasting Time-Series Models
- **Holt-Winters Exponential Smoothing**: Trend-adjusted additive smoothing.
- **SARIMA**: Seasonal Autoregressive Integrated Moving Average $(1, 1, 1)$.
- Evaluated via temporal train/test split using **MAE** (Mean Absolute Error) and **MAPE** (Mean Absolute Percentage Error).
"""
    with open(method_path, "w", encoding="utf-8") as f:
        f.write(method_content)
        
    logger.info(f"Executive Markdown Reports generated at {exec_path} and {method_path}")

if __name__ == "__main__":
    run_full_pipeline()
