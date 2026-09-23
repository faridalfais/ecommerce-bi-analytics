import streamlit as st
import pandas as pd
from src.utils.i18n import get_text
from dashboard.app import load_all_pipeline_data
from dashboard.components.charts import plot_revenue_trend, plot_country_revenue

st.set_page_config(page_title="Finance & Revenue", layout="wide")

lang = st.session_state.get("lang", "en")
data_store = load_all_pipeline_data()
df_clean = data_store["df_clean"]
kpis = data_store["kpis"]

st.title(get_text("nav_finance", lang))
st.caption(f"Source: UCI Online Retail II — {kpis.get('max_transaction_date', 'N/A')}")
st.markdown("---")

st.caption(get_text("disclaimer_margin", lang))

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
monthly['AOV'] = (monthly['Revenue'] / monthly['Orders']).round(2)
monthly['Revenue'] = monthly['Revenue'].round(2)
monthly['MoM_Growth_Pct'] = (monthly['Revenue'].pct_change() * 100.0).round(2)

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
