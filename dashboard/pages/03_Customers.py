import streamlit as st
import pandas as pd
from src.utils.i18n import get_text
from dashboard.app import load_all_pipeline_data
from dashboard.components.charts import plot_rfm_segments

st.set_page_config(page_title="Customer Analytics & RFM", layout="wide")

lang = st.session_state.get("lang", "en")
data_store = load_all_pipeline_data()
rfm_df = data_store["rfm_df"]
rfm_summary = data_store["rfm_summary"]

st.title(get_text("nav_customers", lang))
st.caption("Customer segmentation using Recency, Frequency, and Monetary (RFM) scoring.")
st.markdown("---")

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
