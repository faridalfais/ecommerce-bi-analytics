import streamlit as st
import pandas as pd
from src.utils.i18n import get_text
from dashboard.app import load_all_pipeline_data
from dashboard.components.charts import plot_churn_risk
from src.anomaly.anomaly_detector import detect_revenue_anomalies

st.set_page_config(page_title="ML Insights & Risk Modeling", layout="wide")

lang = st.session_state.get("lang", "en")
data_store = load_all_pipeline_data()
churn_results = data_store["churn_results"]
df_clean = data_store["df_clean"]

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

anomalies_df = detect_revenue_anomalies(df_clean)
anomaly_events = anomalies_df[anomalies_df['IsAnomaly'] == 1].copy()

st.caption(f"Anomalous days identified: **{len(anomaly_events)}**")
st.dataframe(
    anomaly_events[['TransactionDate', 'DailyOrders', 'DailyRevenue', 'ZScore', 'AnomalyType']]
    .sort_values(by='DailyRevenue', ascending=False),
    use_container_width=True,
)
