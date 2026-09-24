import sys
from pathlib import Path

# Ensure repository root is on sys.path for Streamlit Cloud deployment
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st
from src.utils.i18n import get_text
from dashboard.app import load_all_pipeline_data
from dashboard.components.kpi_card import inject_mobile_css
from dashboard.components.charts import plot_revenue_trend, plot_country_revenue

st.set_page_config(page_title="Finance & Revenue", layout="wide")
inject_mobile_css()

lang = st.session_state.get("lang", "en")
data_store = load_all_pipeline_data()
kpis = data_store["kpis"]

# MEM: Use pre-aggregated monthly and country DataFrames from data_store.
# These are tiny (~24 rows and ~40 rows respectively) and were computed once
# during the pipeline run — no need to load df_clean here.
monthly_base = data_store["monthly_revenue"].copy()   # ~24 rows, safe to copy
country_df = data_store["country_revenue"]

st.title(get_text("nav_finance", lang))
st.caption(f"Source: UCI Online Retail II — {kpis.get('max_transaction_date', 'N/A')}")
st.markdown("---")

st.caption(get_text("disclaimer_margin", lang))

if monthly_base.empty:
    st.error("No transaction data available. Please check the data pipeline.")
    st.stop()

# Enrich the monthly summary with derived metrics for the table display
monthly_base["Date"] = pd.to_datetime(monthly_base["Date"])
# Reconstruct aggregated monthly metrics from forecast_results if available
# (orders/customers are in forecast_results historical series only as revenue)
# Here we derive the additional columns from the monthly revenue series alone.
monthly_base = monthly_base.rename(columns={"Revenue": "Revenue"})  # ensure name
monthly_base["MoM_Growth_Pct"] = (monthly_base["Revenue"].pct_change() * 100.0).round(2)
monthly_base["Revenue"] = monthly_base["Revenue"].round(2)

# Charts — responsive columns (collapse to stacked on mobile via CSS)
c1, c2 = st.columns([3, 2])
with c1:
    fig_rev = plot_revenue_trend(monthly_base, title=get_text("chart_revenue_trend", lang))
    st.plotly_chart(fig_rev, use_container_width=True)

with c2:
    fig_country = plot_country_revenue(country_df, title=get_text("chart_country_share", lang))
    st.plotly_chart(fig_country, use_container_width=True)

st.markdown("---")
st.subheader("Monthly Performance")
display = monthly_base.copy()
display["Date"] = display["Date"].dt.strftime("%Y-%m")
st.dataframe(display.sort_values(by="Date", ascending=False), use_container_width=True)
