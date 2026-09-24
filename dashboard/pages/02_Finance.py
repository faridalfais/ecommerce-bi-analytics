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
from dashboard.components.charts import plot_revenue_trend, plot_country_revenue

st.set_page_config(page_title="Finance & Revenue", layout="wide")
inject_mobile_css()

lang = st.session_state.get("lang", "en")
data_store = load_all_pipeline_data()
df_clean = data_store["df_clean"]
kpis = data_store["kpis"]

st.title(get_text("nav_finance", lang))
st.caption(f"Source: UCI Online Retail II — {kpis.get('max_transaction_date', 'N/A')}")
st.markdown("---")

st.caption(get_text("disclaimer_margin", lang))

if df_clean.empty:
    st.error("No transaction data available. Please check the data pipeline.")
    st.stop()

# Monthly aggregation — rename InvoiceDate to Date immediately for consistency
df_clean = df_clean.copy()
df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'])
monthly = df_clean.set_index('InvoiceDate').resample('ME').agg(
    Revenue=('TotalLineAmount', 'sum'),
    Orders=('Invoice', 'nunique'),
    ActiveCustomers=('CustomerID', 'nunique'),
    UnitsSold=('Quantity', 'sum')
).reset_index()

# Rename 'InvoiceDate' -> 'Date' so plot_revenue_trend finds it
monthly.rename(columns={'InvoiceDate': 'Date'}, inplace=True)
monthly['AOV'] = (monthly['Revenue'] / monthly['Orders'].replace(0, float('nan'))).round(2)
monthly['Revenue'] = monthly['Revenue'].round(2)
monthly['MoM_Growth_Pct'] = (monthly['Revenue'].pct_change() * 100.0).round(2)

# Charts — responsive columns (collapse to stacked on mobile via CSS)
c1, c2 = st.columns([3, 2])
with c1:
    fig_rev = plot_revenue_trend(monthly, title=get_text("chart_revenue_trend", lang))
    st.plotly_chart(fig_rev, use_container_width=True)

with c2:
    country_df = df_clean.groupby('Country')['TotalLineAmount'].sum().reset_index()
    country_df.columns = ['country', 'total_revenue']
    country_df = country_df.sort_values('total_revenue', ascending=False)
    country_df['total_revenue'] = country_df['total_revenue'].round(2)
    fig_country = plot_country_revenue(country_df, title=get_text("chart_country_share", lang))
    st.plotly_chart(fig_country, use_container_width=True)

st.markdown("---")
st.subheader("Monthly Performance")
display = monthly.copy()
display['Date'] = display['Date'].dt.strftime('%Y-%m')
st.dataframe(display.sort_values(by='Date', ascending=False), use_container_width=True)
