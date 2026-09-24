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
from src.utils.logger import get_logger
from src.ingestion.loader import load_raw_data
from src.cleaning.cleaner import clean_transaction_data
from src.analytics.metrics import compute_overall_kpis, generate_executive_insights
from src.segmentation.rfm import calculate_rfm, get_rfm_segment_summary
from src.ml.churn_model import train_churn_prediction_model
from src.forecasting.revenue_forecast import forecast_monthly_revenue
from src.external_data.economic_api import fetch_world_bank_data

logger = get_logger("dashboard")

# Resolved paths — always absolute so they work regardless of CWD
_PROCESSED_DIR = ROOT_DIR / "data" / "processed"
_PROCESSED_PARQUET = _PROCESSED_DIR / "cleaned_transactions.parquet"


def _run_full_pipeline() -> dict:
    """Execute the full data ingestion, cleaning, and analytics pipeline."""
    logger.info("Running full data pipeline (download → clean → analyse)...")
    raw_df = load_raw_data()
    df_clean, quality_summary = clean_transaction_data(raw_df, save_processed=True)
    return _compute_analytics(df_clean, quality_summary)


def _load_from_processed_parquet() -> dict:
    """Load pre-cleaned data from persisted parquet and run analytics only."""
    logger.info(f"Loading pre-cleaned data from {_PROCESSED_PARQUET}...")
    df_clean = pd.read_parquet(_PROCESSED_PARQUET)
    # Provide a minimal quality_summary when loading from cache
    quality_summary = {
        "raw_record_count": len(df_clean),
        "cleaned_usable_record_count": len(df_clean),
        "total_cleaned_revenue": float(df_clean["TotalLineAmount"].sum()),
        "unique_customers_count": int(df_clean["CustomerID"].dropna().nunique()),
        "unique_products_count": int(df_clean["StockCode"].nunique()) if "StockCode" in df_clean.columns else 0,
        "source": "processed_parquet_cache",
    }
    return _compute_analytics(df_clean, quality_summary)


def _compute_analytics(df_clean: pd.DataFrame, quality_summary: dict) -> dict:
    """Run all analytics on a cleaned DataFrame."""
    logger.info(f"Computing analytics on {len(df_clean):,} clean records...")
    kpis = compute_overall_kpis(df_clean)
    rfm_df = calculate_rfm(df_clean)
    rfm_summary = get_rfm_segment_summary(rfm_df)
    churn_results = train_churn_prediction_model(df_clean)
    forecast_results = forecast_monthly_revenue(df_clean)
    insights = generate_executive_insights(kpis, rfm_summary, forecast_results)

    try:
        macro_df = fetch_world_bank_data()
    except Exception as e:
        logger.warning(f"World Bank API unavailable, using fallback: {e}")
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


# Data Caching — ttl=None means cache persists until Streamlit server restarts.
# On first run: runs full pipeline (downloads + cleans ~1M rows if no processed parquet).
# On subsequent runs within the same deployment: serves from Streamlit cache (instant).
# Fast path: if cleaned_transactions.parquet already exists from a prior run, load it
# directly (avoids re-downloading and re-cleaning the 1M-row dataset).
@st.cache_data(ttl=None, show_spinner="Loading analytics data...")
def load_all_pipeline_data(use_processed_cache: bool = True) -> dict:
    """
    Load and compute all BI analytics data.

    Fast path: if data/processed/cleaned_transactions.parquet exists, loads from
    that pre-cleaned file and skips the download + cleaning pipeline. This is the
    normal case on Streamlit Cloud after the first successful deployment run.

    Full pipeline: runs when no processed parquet exists (first-time startup, fresh
    Cloud deployment, or after a custom dataset swap).
    """
    if use_processed_cache and _PROCESSED_PARQUET.exists() and _PROCESSED_PARQUET.stat().st_size > 0:
        try:
            return _load_from_processed_parquet()
        except Exception as e:
            logger.warning(f"Failed to load from processed cache ({e}). Falling back to full pipeline.")

    return _run_full_pipeline()


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

# Top Summary Metrics — use 1 column on narrow screens by detecting column count
# st.columns(3) still works on mobile but Streamlit collapses them when viewport < ~600px.
# Using use_container_width=True everywhere ensures charts stay within viewport.
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Revenue", f"£{kpis['total_revenue']:,.2f}")
with col2:
    st.metric("Total Orders", f"{kpis['total_orders']:,}")
with col3:
    st.metric("Active Customers", f"{kpis['active_customers']:,}")
