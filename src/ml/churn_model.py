import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from src.utils.logger import get_logger

logger = get_logger("churn_model")

def train_churn_prediction_model(df_clean: pd.DataFrame, inactivity_threshold_days: int = 90) -> dict:
    """
    Build customer inactivity / churn prediction classification models.
    
    Data-driven Churn Definition:
    Cutoff Date = Max transaction date minus observation window (e.g. 90 days).
    Customers whose last purchase occurred > 90 days prior to the cutoff date are labeled as Churned (1).
    """
    logger.info("Building Customer Inactivity / Churn Prediction Pipeline...")
    valid_df = df_clean.dropna(subset=['CustomerID']).copy()
    valid_df['InvoiceDate'] = pd.to_datetime(valid_df['InvoiceDate'])
    
    max_date = valid_df['InvoiceDate'].max()
    cutoff_date = max_date - pd.Timedelta(days=inactivity_threshold_days)
    
    # Historical observation data up to cutoff_date
    obs_df = valid_df[valid_df['InvoiceDate'] <= cutoff_date].copy()
    
    if len(obs_df) == 0:
        logger.warning("Cutoff date results in empty observation window. Adjusting cutoff...")
        cutoff_date = max_date - pd.Timedelta(days=60)
        obs_df = valid_df[valid_df['InvoiceDate'] <= cutoff_date].copy()
        
    # Build Customer Feature Vectors from observation window
    cust_features = obs_df.groupby('CustomerID').agg(
        Recency=('InvoiceDate', lambda x: (cutoff_date - x.max()).days),
        Frequency=('Invoice', 'nunique'),
        Monetary=('TotalLineAmount', 'sum'),
        FirstPurchase=('InvoiceDate', 'min'),
        LastPurchase=('InvoiceDate', 'max'),
        UniqueProducts=('StockCode', 'nunique'),
        Country=('Country', 'last')
    ).reset_index()
    
    cust_features['Monetary'] = cust_features['Monetary'].round(2)
    cust_features['AvgOrderValue'] = (cust_features['Monetary'] / cust_features['Frequency']).round(2)
    cust_features['LifespanDays'] = (cust_features['LastPurchase'] - cust_features['FirstPurchase']).dt.days
    cust_features['PurchaseVelocity'] = (cust_features['Frequency'] / (cust_features['LifespanDays'] + 1)).round(4)
    cust_features['IsDomestic'] = (cust_features['Country'] == 'United Kingdom').astype(int)
    
    # Ground Truth Churn Label: Did customer make ANY purchase after cutoff_date?
    future_purchasers = valid_df[valid_df['InvoiceDate'] > cutoff_date]['CustomerID'].unique()
    cust_features['IsChurned'] = (~cust_features['CustomerID'].isin(future_purchasers)).astype(int)
    
    logger.info(f"Feature matrix built for {len(cust_features)} customers. Churn rate: {cust_features['IsChurned'].mean()*100:.2f}%")
    
    # Select Numeric Feature Matrix X and Target y
    feature_cols = ['Recency', 'Frequency', 'Monetary', 'AvgOrderValue', 'UniqueProducts', 'LifespanDays', 'PurchaseVelocity', 'IsDomestic']
    X = cust_features[feature_cols].fillna(0)
    y = cust_features['IsChurned']
    
    # Stratified Train-Test Split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    models = {
        "Logistic Regression": LogisticRegression(random_state=42, max_iter=1000),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42, max_depth=8),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5)
    }
    
    results = {}
    best_model_name = "Gradient Boosting"
    best_f1 = -1
    best_model_obj = None
    
    for name, model in models.items():
        if name == "Logistic Regression":
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            y_prob = model.predict_proba(X_test_scaled)[:, 1]
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)[:, 1]
            
        p = precision_score(y_test, y_pred, zero_division=0)
        r = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc = roc_auc_score(y_test, y_prob)
        cm = confusion_matrix(y_test, y_pred).tolist()
        
        results[name] = {
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1_score": round(float(f1), 4),
            "roc_auc": round(float(auc), 4),
            "confusion_matrix": cm
        }
        
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model_obj = model
            
    # Feature Importances from best tree model
    feature_importances = {}
    if hasattr(best_model_obj, "feature_importances_"):
        importances = best_model_obj.feature_importances_
        for col, imp in zip(feature_cols, importances):
            feature_importances[col] = round(float(imp), 4)
            
    logger.info(f"Model comparison complete. Best Model: {best_model_name} (F1: {best_f1:.4f})")
    
    # Predict churn risk score on entire dataset
    cust_features['ChurnRiskScore'] = (best_model_obj.predict_proba(X)[:, 1] * 100).round(1)
    
    return {
        "best_model_name": best_model_name,
        "model_metrics": results,
        "feature_importances": feature_importances,
        "customer_predictions": cust_features[['CustomerID', 'Recency', 'Frequency', 'Monetary', 'IsChurned', 'ChurnRiskScore']].sort_values(by='ChurnRiskScore', ascending=False)
    }
