import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from src.utils.logger import get_logger

logger = get_logger("anomaly")

def detect_revenue_anomalies(df_clean: pd.DataFrame, contamination: float = 0.05) -> pd.DataFrame:
    """
    Detect statistical and machine learning anomalies in daily transaction trends.
    Uses IsolationForest and Rolling Z-Score methods.
    """
    logger.info("Running Anomaly Detection pipeline on daily metrics...")
    
    # Aggregate daily metrics
    daily = df_clean.groupby(df_clean['InvoiceDate'].dt.date).agg(
        DailyOrders=('Invoice', 'nunique'),
        DailyRevenue=('TotalLineAmount', 'sum'),
        DailyUnits=('Quantity', 'sum'),
        ActiveCustomers=('CustomerID', 'nunique')
    ).reset_index()
    
    daily.rename(columns={'InvoiceDate': 'TransactionDate'}, inplace=True)
    daily['TransactionDate'] = pd.to_datetime(daily['TransactionDate'])
    daily = daily.sort_values(by='TransactionDate').reset_index(drop=True)
    
    # 1. Isolation Forest Model
    features = ['DailyOrders', 'DailyRevenue', 'DailyUnits', 'ActiveCustomers']
    iso_forest = IsolationForest(contamination=contamination, random_state=42)
    daily['IsoForestAnomaly'] = (iso_forest.fit_predict(daily[features]) == -1).astype(int)
    daily['IsoForestScore'] = iso_forest.decision_function(daily[features])
    
    # 2. Rolling Z-Score Method on Daily Revenue
    rolling_mean = daily['DailyRevenue'].rolling(window=7, min_periods=3).mean()
    rolling_std = daily['DailyRevenue'].rolling(window=7, min_periods=3).std().replace(0, 1)
    daily['ZScore'] = ((daily['DailyRevenue'] - rolling_mean) / rolling_std).fillna(0).round(2)
    daily['ZScoreAnomaly'] = (np.abs(daily['ZScore']) > 2.5).astype(int)
    
    # Combined Anomaly Indicator
    daily['IsAnomaly'] = ((daily['IsoForestAnomaly'] == 1) | (daily['ZScoreAnomaly'] == 1)).astype(int)
    
    # Anomaly Type Classification (Spike vs Drop)
    def classify_anomaly(row):
        if row['IsAnomaly'] == 0:
            return 'Normal'
        mean_rev = daily['DailyRevenue'].mean()
        if row['DailyRevenue'] > mean_rev * 1.5:
            return 'Revenue Spike'
        elif row['DailyRevenue'] < mean_rev * 0.3:
            return 'Revenue Drop'
        else:
            return 'Volume Anomaly'
            
    daily['AnomalyType'] = daily.apply(classify_anomaly, axis=1)
    
    anomalies_count = daily['IsAnomaly'].sum()
    logger.info(f"Anomaly Detection complete: Identified {anomalies_count} anomalous daily events.")
    return daily
