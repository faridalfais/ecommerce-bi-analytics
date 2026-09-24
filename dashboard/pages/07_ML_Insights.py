import sys
from pathlib import Path

# Ensure repository root is on sys.path for Streamlit Cloud deployment
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st
from src.utils.i18n import get_text
from dashboard.app import load_all_pipeline_data, load_clean_df_columns
from dashboard.components.kpi_card import inject_mobile_css
from dashboard.components.charts import plot_churn_risk
from src.anomaly.anomaly_detector import detect_revenue_anomalies

st.set_page_config(page_title="ML Insights & Risk Modeling", layout="wide")
inject_mobile_css()

lang = st.session_state.get("lang", "en")
data_store = load_all_pipeline_data()
churn_results = data_store["churn_results"]


@st.cache_data(ttl=None, show_spinner="Running anomaly detection...")
def _cached_anomaly_detection() -> pd.DataFrame:
    """
    MEM: Run IsolationForest anomaly detection once and cache the result.
    Without this, the model re-trains and the full daily aggregation re-runs
    on every page navigation — expensive and memory-wasteful.
    Only the columns needed for daily aggregation are loaded.
    """
    df = load_clean_df_columns(("InvoiceDate", "Invoice", "TotalLineAmount", "Quantity", "CustomerID"))
    if df.empty:
        return pd.DataFrame()
    return detect_revenue_anomalies(df)


st.title(get_text("nav_ml", lang))
st.caption(
    "Churn prediction via Random Forest classifier. "
    "Anomaly detection via IsolationForest with Z-score cross-validation."
)
st.markdown("---")

col1, col2 = st.columns([3, 2])

with col1:
    cust_preds = churn_results["customer_predictions"]
    fig_churn = plot_churn_risk(cust_preds, title=get_text("chart_churn_distribution", lang))
    st.plotly_chart(fig_churn, use_container_width=True)

with col2:
    st.subheader("Churn Classifier Performance")
    best_m = churn_results["best_model_name"]
    metrics_dict = churn_results["model_metrics"]

    st.info(f"Selected model: **{best_m}**")
    m_df = []
    for model_name, m_vals in metrics_dict.items():
        m_df.append({
            "Model": model_name,
            "Precision": m_vals["precision"],
            "Recall": m_vals["recall"],
            "F1-Score": m_vals["f1_score"],
            "ROC-AUC": m_vals["roc_auc"],
        })
    st.dataframe(pd.DataFrame(m_df), use_container_width=True)

    st.subheader("Feature Importances")
    f_imp = churn_results.get("feature_importances", {})
    if f_imp:
        fi_df = (
            pd.DataFrame(list(f_imp.items()), columns=["Feature", "Importance"])
            .sort_values(by="Importance", ascending=False)
        )
        st.dataframe(fi_df, use_container_width=True)

st.markdown("---")
st.subheader("Revenue Anomaly Detection")
st.caption("Daily revenue aggregates flagged by IsolationForest and/or |Z-score| > 2.5.")

anomalies_df = _cached_anomaly_detection()
if not anomalies_df.empty:
    anomaly_events = anomalies_df[anomalies_df['IsAnomaly'] == 1]
    st.caption(f"Anomalous days identified: **{len(anomaly_events)}**")
    st.dataframe(
        anomaly_events[['TransactionDate', 'DailyOrders', 'DailyRevenue', 'ZScore', 'AnomalyType']]
        .sort_values(by='DailyRevenue', ascending=False),
        use_container_width=True,
    )
else:
    st.warning("Anomaly detection data unavailable.")
