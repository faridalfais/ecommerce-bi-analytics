import sys
from pathlib import Path

# Ensure repository root is on sys.path for Streamlit Cloud deployment
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from src.utils.i18n import get_text
from dashboard.app import load_all_pipeline_data
from dashboard.components.kpi_card import inject_mobile_css
from dashboard.components.charts import plot_rfm_segments

st.set_page_config(page_title="Customer Analytics & RFM", layout="wide")
inject_mobile_css()

lang = st.session_state.get("lang", "en")
data_store = load_all_pipeline_data()
rfm_df = data_store["rfm_df"]
rfm_summary = data_store["rfm_summary"]

st.title(get_text("nav_customers", lang))
st.caption("Customer segmentation using Recency, Frequency, and Monetary (RFM) scoring.")
st.markdown("---")

if rfm_df is None or rfm_df.empty:
    st.warning(
        "Customer RFM data is unavailable. This typically means the dataset "
        "has no CustomerID column or all CustomerID values are missing."
    )
    st.stop()

# Responsive column layout — collapses to stacked on mobile via CSS
col1, col2 = st.columns([3, 2])
with col1:
    fig_rfm = plot_rfm_segments(rfm_summary, title=get_text("chart_rfm_segments", lang))
    st.plotly_chart(fig_rfm, use_container_width=True)

with col2:
    st.subheader("Segment Financial Profiles")
    st.dataframe(
        rfm_summary[['Segment', 'CustomerCount', 'AvgRecencyDays', 'AvgFrequency', 'TotalRevenue', 'RevenueSharePct']],
        use_container_width=True,
    )

st.markdown("---")
st.subheader("Individual Customer RFM Roster")
st.caption("Showing first 100 customers. All monetary values in GBP (£).")
st.dataframe(
    rfm_df[['CustomerID', 'Country', 'Recency', 'Frequency', 'Monetary', 'AvgOrderValue', 'RFM_Cell', 'Segment']].head(100),
    use_container_width=True,
)
