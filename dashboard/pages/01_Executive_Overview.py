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
from dashboard.components.kpi_card import render_kpi_card
from dashboard.components.charts import plot_revenue_trend, plot_rfm_segments
from dashboard.components.insights_card import render_insights_card

st.set_page_config(page_title="Executive Overview — BI Analytics", layout="wide")

lang = st.session_state.get("lang", "en")
data_store = load_all_pipeline_data()
kpis = data_store["kpis"]
df_clean = data_store["df_clean"]

st.title(get_text("nav_executive", lang))
st.caption(
    f"Dataset: UCI Online Retail II / Ingested Data  ·  "
    f"Period: 2009-12-01 – {kpis.get('max_transaction_date', 'N/A')}  ·  "
    f"Transactions: {len(df_clean):,}"
)
st.markdown("---")

# Responsive KPI Rows (2 rows of 3 columns)
r1_c1, r1_c2, r1_c3 = st.columns(3)
with r1_c1:
    render_kpi_card(get_text("kpi_total_revenue", lang), f"£{kpis['total_revenue']:,.2f}")
with r1_c2:
    render_kpi_card(get_text("kpi_total_orders", lang), f"{kpis['total_orders']:,}")
with r1_c3:
    render_kpi_card(get_text("kpi_active_customers", lang), f"{kpis['active_customers']:,}")

r2_c1, r2_c2, r2_c3 = st.columns(3)
with r2_c1:
    render_kpi_card(get_text("kpi_aov", lang), f"£{kpis['average_order_value']:.2f}")
with r2_c2:
    render_kpi_card(get_text("kpi_repeat_rate", lang), f"{kpis['repeat_purchase_rate_pct']}%")
with r2_c3:
    mom = kpis['latest_mom_growth_pct']
    render_kpi_card(
        get_text("kpi_mom_growth", lang),
        f"{mom:+}%",
        delta=f"{mom}%",
        delta_color="normal" if mom >= 0 else "inverse",
    )

st.markdown("---")

# Charts Row
col1, col2 = st.columns([3, 2])
with col1:
    monthly = (
        df_clean
        .set_index('InvoiceDate')
        .resample('ME')['TotalLineAmount']
        .sum()
        .reset_index()
    )
    monthly.columns = ['Date', 'Revenue']
    fig_rev = plot_revenue_trend(monthly, title=get_text("chart_revenue_trend", lang))
    st.plotly_chart(fig_rev, use_container_width=True)

with col2:
    fig_rfm = plot_rfm_segments(data_store['rfm_summary'], title=get_text("chart_rfm_segments", lang))
    st.plotly_chart(fig_rfm, use_container_width=True)

st.markdown("---")

# Data & Methodology Section
with st.expander("Data & Methodology", expanded=False):
    st.markdown("""
**Dataset:** E-Commerce Wholesale Transaction Records (UCI Online Retail II or Custom Ingestion).  
Contains invoice-level sales spanning online retail operations.

**What is available:**
- Invoice-level transactions: quantity, unit price, customer ID, country, product description.
- Derived metric: `TotalLineAmount = Quantity × UnitPrice` (gross revenue per line item).

**What is NOT available and therefore NOT reported:**
- Cost of Goods Sold (COGS)
- Gross profit or net profit
- Marketing spend or ROAS
- Return on Investment (ROI)

Any metric labelled "Revenue" in this dashboard refers to **gross sales volume only**.

**Pipeline stages:** Ingestion → Cleaning & Validation → SQL Analytics → RFM Segmentation → Churn Prediction (Random Forest) → Anomaly Detection (IsolationForest) → Time-Series Forecasting (Holt-Winters / SARIMA) → Executive Reporting.
    """)

# Insights
render_insights_card(data_store['insights'], lang=lang)
