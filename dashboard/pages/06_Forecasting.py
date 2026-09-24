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
from dashboard.components.charts import plot_forecast_chart

st.set_page_config(page_title="Revenue Forecasting", layout="wide")
inject_mobile_css()

lang = st.session_state.get("lang", "en")
data_store = load_all_pipeline_data()
forecast_results = data_store["forecast_results"]

st.title(get_text("nav_forecasting", lang))
st.caption(
    "Time-series models benchmarked: Naive Baseline, Holt-Winters Exponential Smoothing, SARIMA. "
    "Best model selected by lowest MAE on held-out test set."
)
st.markdown("---")

if forecast_results is None:
    st.error("Forecast results are unavailable. The forecasting pipeline may have encountered an error.")
    st.stop()

fig_forecast = plot_forecast_chart(forecast_results, title=get_text("chart_forecasting", lang))
st.plotly_chart(fig_forecast, use_container_width=True)

# Responsive columns — collapses to stacked on mobile via CSS
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Model Benchmarking — Accuracy Metrics")
    evals = forecast_results.get('evaluations', {})
    if evals:
        eval_rows = []
        for model_name, metrics in evals.items():
            eval_rows.append({
                "Model": model_name,
                "MAE (£)": f"£{metrics['MAE']:,.2f}",
                "RMSE (£)": f"£{metrics['RMSE']:,.2f}",
                "MAPE (%)": f"{metrics['MAPE']:.2f}%",
            })
        st.dataframe(pd.DataFrame(eval_rows), use_container_width=True)
        st.info(f"Selected model: **{forecast_results['best_model_name']}** (lowest MAE)")
    else:
        st.warning("Model evaluation metrics are unavailable.")

with col2:
    st.subheader("6-Month Forward Projections")
    fut_df = forecast_results.get('future_forecast')
    if fut_df is not None and not fut_df.empty:
        fut_display = fut_df.copy()
        fut_display['Date'] = fut_display['Date'].dt.strftime('%Y-%m')
        st.dataframe(fut_display, use_container_width=True)
        st.caption("Confidence intervals are model-derived. Projections assume conditions broadly similar to the training period.")
    else:
        st.warning("Forward projections are unavailable.")
