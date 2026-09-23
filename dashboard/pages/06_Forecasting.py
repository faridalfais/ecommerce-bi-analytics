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
from dashboard.components.charts import plot_forecast_chart

st.set_page_config(page_title="Revenue Forecasting", layout="wide")

lang = st.session_state.get("lang", "en")
data_store = load_all_pipeline_data()
forecast_results = data_store["forecast_results"]

st.title(get_text("nav_forecasting", lang))
st.caption(
    "Time-series models benchmarked: Naive Baseline, Holt-Winters Exponential Smoothing, SARIMA. "
    "Best model selected by lowest MAE on held-out test set."
)
st.markdown("---")

fig_forecast = plot_forecast_chart(forecast_results, title=get_text("chart_forecasting", lang))
st.plotly_chart(fig_forecast, use_container_width=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Model Benchmarking — Accuracy Metrics")
    evals = forecast_results['evaluations']
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

with col2:
    st.subheader("6-Month Forward Projections")
    fut_df = forecast_results['future_forecast'].copy()
    fut_df['Date'] = fut_df['Date'].dt.strftime('%Y-%m')
    st.dataframe(fut_df, use_container_width=True)
    st.caption("Confidence intervals are model-derived. Projections assume conditions broadly similar to the training period.")
