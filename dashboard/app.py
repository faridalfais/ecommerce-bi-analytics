import sys
from pathlib import Path

# Ensure repository root is on sys.path for Streamlit Cloud deployment
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import gc
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

# Columns used only for analytics (not needed per-page as raw rows)
_ANALYTICS_COLS = [
    "Invoice", "InvoiceDate", "StockCode", "Description",
    "Quantity", "Price", "TotalLineAmount", "CustomerID", "Country",
    "IsCancelled",
]


def _run_full_pipeline() -> tuple[pd.DataFrame, dict]:
    """Execute the full data ingestion, cleaning, and analytics pipeline.
    Returns (df_clean, quality_summary) — caller must handle df_clean lifetime."""
    logger.info("Running full data pipeline (download → clean → analyse)...")
    raw_df = load_raw_data()
    df_clean, quality_summary = clean_transaction_data(raw_df, save_processed=True)
    del raw_df
    gc.collect()
    return df_clean, quality_summary


def _load_clean_df() -> tuple[pd.DataFrame, dict]:
    """Load pre-cleaned data from persisted parquet and build quality_summary."""
    logger.info(f"Loading pre-cleaned data from {_PROCESSED_PARQUET}...")
    # MEM: load only the columns the analytics pipeline actually touches
    df_clean = pd.read_parquet(_PROCESSED_PARQUET, columns=_ANALYTICS_COLS)
    quality_summary = {
        "raw_record_count": len(df_clean),
        "cleaned_usable_record_count": len(df_clean),
        "total_cleaned_revenue": float(df_clean["TotalLineAmount"].sum()),
        "unique_customers_count": int(df_clean["CustomerID"].dropna().nunique()),
        "unique_products_count": int(df_clean["StockCode"].nunique()) if "StockCode" in df_clean.columns else 0,
        "source": "processed_parquet_cache",
    }
    return df_clean, quality_summary


def _compute_analytics(df_clean: pd.DataFrame, quality_summary: dict) -> dict:
    """
    Run all analytics on a cleaned DataFrame.
    MEM: df_clean is NOT stored in the returned dict — callers that need raw
    row-level data should use load_clean_df_columns() separately.
    """
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

    # Pre-aggregate monthly revenue here so pages don't need df_clean for it
    df_clean["InvoiceDate"] = pd.to_datetime(df_clean["InvoiceDate"])
    monthly_revenue = (
        df_clean.set_index("InvoiceDate")
        .resample("ME")["TotalLineAmount"]
        .sum()
        .reset_index()
        .rename(columns={"InvoiceDate": "Date", "TotalLineAmount": "Revenue"})
    )

    # MEM: country aggregation — small result, doesn't need df_clean later
    country_revenue = (
        df_clean.groupby("Country")["TotalLineAmount"]
        .sum()
        .reset_index()
        .rename(columns={"TotalLineAmount": "total_revenue"})
        .sort_values("total_revenue", ascending=False)
        .assign(total_revenue=lambda d: d["total_revenue"].round(2))
    )

    # MEM: product aggregation — small result, doesn't need df_clean later
    prod_summary = (
        df_clean.groupby(["StockCode", "Description"])
        .agg(
            total_units_sold=("Quantity", "sum"),
            total_orders=("Invoice", "nunique"),
            total_revenue=("TotalLineAmount", "sum"),
            avg_price=("Price", "mean"),
        )
        .reset_index()
        .assign(
            total_revenue=lambda d: d["total_revenue"].round(2),
            avg_price=lambda d: d["avg_price"].round(2),
        )
        .sort_values("total_revenue", ascending=False)
    )

    record_count = len(df_clean)

    # MEM: explicitly release df_clean — analytics are complete; don't store it
    del df_clean
    gc.collect()

    return {
        # No df_clean here — pages load only the columns they need on demand
        "record_count": record_count,
        "quality_summary": quality_summary,
        "kpis": kpis,
        "rfm_df": rfm_df,
        "rfm_summary": rfm_summary,
        "churn_results": churn_results,
        "forecast_results": forecast_results,
        "insights": insights,
        "macro_df": macro_df,
        "monthly_revenue": monthly_revenue,
        "country_revenue": country_revenue,
        "prod_summary": prod_summary,
    }


# ---------------------------------------------------------------------------
# Public cached loaders
# ---------------------------------------------------------------------------

@st.cache_data(ttl=None, show_spinner="Loading analytics data...")
def load_all_pipeline_data(use_processed_cache: bool = True) -> dict:
    """
    Load and compute all BI analytics data.

    MEM CHANGE: This function no longer stores df_clean in the returned dict.
    Pre-aggregated views (monthly_revenue, country_revenue, prod_summary) are
    stored instead so dashboard pages don't need the full 1M-row DataFrame.

    Fast path: if data/processed/cleaned_transactions.parquet exists, loads from
    that pre-cleaned file and skips the download + cleaning pipeline.

    Full pipeline: runs when no processed parquet exists (first-time startup).
    """
    if use_processed_cache and _PROCESSED_PARQUET.exists() and _PROCESSED_PARQUET.stat().st_size > 0:
        try:
            df_clean, quality_summary = _load_clean_df()
            return _compute_analytics(df_clean, quality_summary)
        except Exception as e:
            logger.warning(f"Failed to load from processed cache ({e}). Falling back to full pipeline.")

    df_clean, quality_summary = _run_full_pipeline()
    return _compute_analytics(df_clean, quality_summary)


@st.cache_data(ttl=None, show_spinner=False)
def load_clean_df_columns(columns: tuple[str, ...]) -> pd.DataFrame:
    """
    Load only the requested columns from the processed parquet.

    MEM: Pages call this with exactly the columns they need rather than
    unpacking the full df_clean from the shared data store. This avoids
    keeping a full 1M-row copy per page in memory.

    Parameters
    ----------
    columns : tuple[str, ...]
        Tuple of column names to load (tuple is hashable for cache key).
    """
    if _PROCESSED_PARQUET.exists() and _PROCESSED_PARQUET.stat().st_size > 0:
        return pd.read_parquet(_PROCESSED_PARQUET, columns=list(columns))
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Language State Management
# ---------------------------------------------------------------------------
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
    f"Total transactions: {data_store['record_count']:,}"
)
st.markdown("---")

st.info(
    "Use the left sidebar navigation to explore: "
    "Executive Overview, Finance, Customers, Products, Market Context, Forecasting, and ML Insights."
)

# Top Summary Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Revenue", f"£{kpis['total_revenue']:,.2f}")
with col2:
    st.metric("Total Orders", f"{kpis['total_orders']:,}")
with col3:
    st.metric("Active Customers", f"{kpis['active_customers']:,}")
