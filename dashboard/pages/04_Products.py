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
from dashboard.components.charts import plot_top_products

st.set_page_config(page_title="Product Analytics", layout="wide")
inject_mobile_css()

lang = st.session_state.get("lang", "en")
data_store = load_all_pipeline_data()
df_clean = data_store["df_clean"]

st.title(get_text("nav_products", lang))
st.caption("Revenue and volume analysis at the SKU level. All prices in GBP (£).")
st.markdown("---")

if df_clean.empty:
    st.error("No transaction data available.")
    st.stop()

prod_summary = df_clean.groupby(['StockCode', 'Description']).agg(
    total_units_sold=('Quantity', 'sum'),
    total_orders=('Invoice', 'nunique'),
    total_revenue=('TotalLineAmount', 'sum'),
    avg_price=('Price', 'mean')
).reset_index()

prod_summary['total_revenue'] = prod_summary['total_revenue'].round(2)
prod_summary['avg_price'] = prod_summary['avg_price'].round(2)
prod_summary = prod_summary.sort_values(by='total_revenue', ascending=False)

# Responsive column layout — collapses to stacked on mobile via CSS
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
    mask = (
        prod_summary['Description'].str.contains(search_term, case=False, na=False) |
        prod_summary['StockCode'].str.contains(search_term, case=False, na=False)
    )
    filtered = prod_summary[mask]
    if filtered.empty:
        st.info(f"No products found matching '{search_term}'.")
    else:
        st.dataframe(filtered.head(50), use_container_width=True)
else:
    st.dataframe(prod_summary.head(50), use_container_width=True)
