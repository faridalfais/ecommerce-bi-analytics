import streamlit as st
import pandas as pd
from src.utils.i18n import get_text
from dashboard.app import load_all_pipeline_data
from dashboard.components.charts import plot_top_products

st.set_page_config(page_title="Product Analytics", layout="wide")

lang = st.session_state.get("lang", "en")
data_store = load_all_pipeline_data()
df_clean = data_store["df_clean"]

st.title(get_text("nav_products", lang))
st.caption("Revenue and volume analysis at the SKU level. All prices in GBP (£).")
st.markdown("---")

prod_summary = df_clean.groupby(['StockCode', 'Description']).agg(
    total_units_sold=('Quantity', 'sum'),
    total_orders=('Invoice', 'nunique'),
    total_revenue=('TotalLineAmount', 'sum'),
    avg_price=('Price', 'mean')
).reset_index()

prod_summary['total_revenue'] = prod_summary['total_revenue'].round(2)
prod_summary['avg_price'] = prod_summary['avg_price'].round(2)
prod_summary = prod_summary.sort_values(by='total_revenue', ascending=False)

col1, col2 = st.columns([3, 2])
with col1:
    fig_prod = plot_top_products(prod_summary, title=get_text("chart_top_products", lang))
    st.plotly_chart(fig_prod, use_container_width=True)

with col2:
    st.subheader("Top 10 Revenue-Generating SKUs")
    st.dataframe(
        prod_summary[['StockCode', 'Description', 'total_revenue', 'total_units_sold', 'avg_price']].head(10),
        use_container_width=True,
    )

st.markdown("---")
st.subheader("Product Catalog Search")
search_term = st.text_input("Filter by SKU or Description:", "")
if search_term:
    filtered = prod_summary[
        prod_summary['Description'].str.contains(search_term, case=False, na=False) |
        prod_summary['StockCode'].str.contains(search_term, case=False, na=False)
    ]
    st.dataframe(filtered.head(50), use_container_width=True)
else:
    st.dataframe(prod_summary.head(50), use_container_width=True)
