import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_squared_error
from src.utils.logger import get_logger

logger = get_logger("forecasting")

def calculate_mape(y_true, y_pred):
    """Calculate Mean Absolute Percentage Error (MAPE)."""
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    non_zero = y_true != 0
    return float(np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100.0)

def forecast_monthly_revenue(df_clean: pd.DataFrame, forecast_horizon_months: int = 6) -> dict:
    """
    Time-series forecasting framework for monthly revenue.
    Includes temporal train/test split, model benchmarking (Naive, Holt-Winters, SARIMA),
    evaluation metrics (MAE, RMSE, MAPE), and 80%/95% confidence intervals.
    """
    logger.info("Executing Monthly Revenue Time-Series Forecasting Pipeline...")
    
    # Aggregate to monthly revenue series
    df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'])
    monthly = df_clean.set_index('InvoiceDate').resample('ME')['TotalLineAmount'].sum().reset_index()
    monthly.columns = ['Date', 'Revenue']
    monthly = monthly.sort_values(by='Date').reset_index(drop=True)
    
    # Drop incomplete trailing month if last month has < 10 days of data
    max_dt = df_clean['InvoiceDate'].max()
    if max_dt.day < 10:
        monthly = monthly.iloc[:-1].copy()
        
    n_total = len(monthly)
    test_size = min(4, max(2, int(n_total * 0.2)))
    train_size = n_total - test_size
    
    train = monthly.iloc[:train_size].copy()
    test = monthly.iloc[train_size:].copy()
    
    logger.info(f"Monthly Series Length: {n_total}. Train: {len(train)}, Test: {len(test)}")
    
    # 1. Naive Baseline Model
    last_train_val = train['Revenue'].iloc[-1]
    test_naive = np.full(len(test), last_train_val)
    
    # 2. Holt-Winters Exponential Smoothing
    hw_model = ExponentialSmoothing(
        train['Revenue'],
        trend='add',
        seasonal=None, # Short 24-month horizon
        initialization_method='estimated'
    ).fit()
    test_hw = hw_model.forecast(len(test)).values
    
    # 3. SARIMA Model (p=1, d=1, q=1)
    sarima_model = SARIMAX(
        train['Revenue'],
        order=(1, 1, 1),
        enforce_stationarity=False,
        enforce_invertibility=False
    ).fit(disp=False)
    test_sarima = sarima_model.forecast(len(test)).values
    
    # Benchmarking Metrics
    models_eval = {
        "Naive Baseline": {
            "pred": test_naive,
            "MAE": round(float(mean_absolute_error(test['Revenue'], test_naive)), 2),
            "RMSE": round(float(np.sqrt(mean_squared_error(test['Revenue'], test_naive))), 2),
            "MAPE": round(calculate_mape(test['Revenue'], test_naive), 2)
        },
        "Holt-Winters": {
            "pred": test_hw,
            "MAE": round(float(mean_absolute_error(test['Revenue'], test_hw)), 2),
            "RMSE": round(float(np.sqrt(mean_squared_error(test['Revenue'], test_hw))), 2),
            "MAPE": round(calculate_mape(test['Revenue'], test_hw), 2)
        },
        "SARIMA": {
            "pred": test_sarima,
            "MAE": round(float(mean_absolute_error(test['Revenue'], test_sarima)), 2),
            "RMSE": round(float(np.sqrt(mean_squared_error(test['Revenue'], test_sarima))), 2),
            "MAPE": round(calculate_mape(test['Revenue'], test_sarima), 2)
        }
    }
    
    # Select best model based on lowest MAE
    best_model_name = min(models_eval.keys(), key=lambda k: models_eval[k]["MAE"])
    logger.info(f"Model Benchmarking Complete. Best Model: {best_model_name}")
    
    # Refit Best Model on Full Historical Data for Future Forecasting
    full_series = monthly['Revenue']
    if best_model_name == "Holt-Winters":
        final_model = ExponentialSmoothing(full_series, trend='add', initialization_method='estimated').fit()
        future_forecast = final_model.forecast(forecast_horizon_months).values
        # Empirical residual std error for confidence bounds
        resid_std = np.std(final_model.resid)
        lower_80 = future_forecast - 1.28 * resid_std
        upper_80 = future_forecast + 1.28 * resid_std
        lower_95 = future_forecast - 1.96 * resid_std
        upper_95 = future_forecast + 1.96 * resid_std
    else:
        final_model = SARIMAX(full_series, order=(1, 1, 1), enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
        forecast_obj = final_model.get_forecast(steps=forecast_horizon_months)
        future_forecast = forecast_obj.predicted_mean.values
        conf_int_80 = forecast_obj.conf_int(alpha=0.20)
        conf_int_95 = forecast_obj.conf_int(alpha=0.05)
        lower_80 = conf_int_80.iloc[:, 0].values
        upper_80 = conf_int_80.iloc[:, 1].values
        lower_95 = conf_int_95.iloc[:, 0].values
        upper_95 = conf_int_95.iloc[:, 1].values
        
    future_dates = pd.date_range(start=monthly['Date'].iloc[-1] + pd.DateOffset(months=1), periods=forecast_horizon_months, freq='ME')
    
    future_df = pd.DataFrame({
        "Date": future_dates,
        "ForecastRevenue": future_forecast.round(2),
        "Lower80": np.maximum(0, lower_80).round(2),
        "Upper80": upper_80.round(2),
        "Lower95": np.maximum(0, lower_95).round(2),
        "Upper95": upper_95.round(2)
    })
    
    return {
        "historical_monthly": monthly,
        "test_actual": test,
        "evaluations": models_eval,
        "best_model_name": best_model_name,
        "future_forecast": future_df
    }
