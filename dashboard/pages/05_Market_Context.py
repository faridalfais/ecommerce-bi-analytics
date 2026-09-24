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
from dashboard.components.charts import plot_macro_trend
from src.statistics.stats_analysis import analyze_macro_correlations

st.set_page_config(page_title="Market Context & Macro Economy", layout="wide")
inject_mobile_css()

lang = st.session_state.get("lang", "en")
data_store = load_all_pipeline_data()
macro_df = data_store["macro_df"]

# MEM: Use pre-aggregated monthly_revenue from data_store — was previously
# re-aggregated from df_clean on every page load.
monthly = data_store["monthly_revenue"]

st.title(get_text("nav_market", lang))
st.caption("UK macro-economic context (2009–2011) overlaid with company transaction history.")
st.markdown("---")

st.caption("Source: World Bank Open Data API — United Kingdom series (GBR), 2009–2011.")

if macro_df is not None and not macro_df.empty:
    # Responsive columns — collapses to stacked on mobile via CSS
    col1, col2 = st.columns([3, 2])
    with col1:
        fig_macro = plot_macro_trend(macro_df, title=get_text("chart_macro_context", lang))
        st.plotly_chart(fig_macro, use_container_width=True)

    with col2:
        st.subheader("UK Macro Indicators")
        # Show only relevant columns and handle missing ones gracefully
        available_cols = [c for c in ['year', 'indicator_code', 'indicator_name', 'value'] if c in macro_df.columns]
        st.dataframe(
            macro_df[available_cols],
            use_container_width=True,
        )

    # Correlation analysis — requires both datasets
    if not monthly.empty:
        try:
            stats_res = analyze_macro_correlations(monthly, macro_df)
        except Exception as e:
            stats_res = {}
            st.warning(f"Statistical correlation analysis could not be computed: {e}")

        st.markdown("---")
        st.subheader("Statistical Correlation — Macro Indicators vs Retail Sales")
        st.caption(
            "Note: Annual macro sample (n=3) is insufficient for inferential statistics. "
            "Correlation values here are contextual, not causal."
        )

        corr_dict = stats_res.get('correlations', {})
        if corr_dict:
            corr_rows = []
            for code, info in corr_dict.items():
                corr_rows.append({
                    "Indicator": info['indicator_name'],
                    "Pearson r": info['pearson_r'],
                    "Pearson p-value": info['pearson_pvalue'],
                    "Spearman r": info['spearman_r'],
                })
            st.dataframe(pd.DataFrame(corr_rows), use_container_width=True)
        else:
            st.info("Annual macro sample size (2009–2011) provides contextual alignment only.")
else:
    st.warning("World Bank API data unavailable. Displaying transaction data without macro overlay.")
    st.info(
        "The application uses embedded authentic UK macro data (2009–2011) as a fallback. "
        "If this warning appears, check your internet connection or API availability."
    )
