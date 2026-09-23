import sys
from pathlib import Path

# Ensure repository root is on sys.path for Streamlit Cloud deployment
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd

# Page Configuration — Clean, neutral, professional BI styling
st.set_page_config(
    page_title="E-Commerce BI & Customer Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.utils.i18n import get_text
from src.ingestion.loader import load_raw_data
from src.cleaning.cleaner import clean_transaction_data
from src.analytics.metrics import compute_overall_kpis, generate_executive_insights
from src.segmentation.rfm import calculate_rfm, get_rfm_segment_summary
from src.ml.churn_model import train_churn_prediction_model
from src.forecasting.revenue_forecast import forecast_monthly_revenue
from src.external_data.economic_api import fetch_world_bank_data

# Data Caching
@st.cache_data(ttl=3600)
def load_all_pipeline_data():
    raw_df = load_raw_data()
    df_clean, quality_summary = clean_transaction_data(raw_df, save_processed=True)
    kpis = compute_overall_kpis(df_clean)
    rfm_df = calculate_rfm(df_clean)
    rfm_summary = get_rfm_segment_summary(rfm_df)
    churn_results = train_churn_prediction_model(df_clean)
    forecast_results = forecast_monthly_revenue(df_clean)
    insights = generate_executive_insights(kpis, rfm_summary, forecast_results)

    try:
        macro_df = fetch_world_bank_data()
    except Exception:
        macro_df = pd.DataFrame()

    return {
        "df_clean": df_clean,
        "quality_summary": quality_summary,
        "kpis": kpis,
        "rfm_df": rfm_df,
        "rfm_summary": rfm_summary,
        "churn_results": churn_results,
        "forecast_results": forecast_results,
        "insights": insights,
        "macro_df": macro_df,
    }

# Language State Management
if "lang" not in st.session_state:
    st.session_state["lang"] = "en"

# Sidebar
st.sidebar.title("E-Commerce BI")
lang_choice = st.sidebar.selectbox(
    "Language / Bahasa",
    options=["English", "Bahasa Indonesia"],
    index=0 if st.session_state["lang"] == "en" else 1,
)
st.session_state["lang"] = "en" if "English" in lang_choice else "id"
lang = st.session_state["lang"]

st.sidebar.markdown("---")
st.sidebar.caption("Portfolio Case Study — Analytical BI Platform")
st.sidebar.caption("Data: UCI Online Retail II / Custom Ingestion")

# Home Overview Section
data_store = load_all_pipeline_data()
kpis = data_store["kpis"]

st.title("E-Commerce Business Intelligence & Customer Analytics")
st.markdown(
    "Analysis of transactions, customers, products, and business trends using historical data."
)
st.caption(
    f"Dataset period: 2009-12-01 – {kpis.get('max_transaction_date', 'N/A')}  ·  "
    f"Total transactions: {len(data_store['df_clean']):,}"
)
st.markdown("---")

st.info(
    "Use the left sidebar navigation to explore: "
    "Executive Overview, Finance, Customers, Products, Market Context, Forecasting, and ML Insights."
)

# Top Summary Metrics (Responsive 3-column layout)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Revenue", f"£{kpis['total_revenue']:,.2f}")
with col2:
    st.metric("Total Orders", f"{kpis['total_orders']:,}")
with col3:
    st.metric("Active Customers", f"{kpis['active_customers']:,}")
