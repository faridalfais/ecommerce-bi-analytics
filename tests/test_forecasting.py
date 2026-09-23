import pandas as pd
from src.forecasting.revenue_forecast import forecast_monthly_revenue


def test_forecast_monthly_revenue():
    # 24 months synthetic monthly data
    dates = pd.date_range(start="2009-12-01", periods=24, freq="ME")
    revenue_vals = [10000 + i*500 + (i%3)*1000 for i in range(24)]
    
    records = []
    for d, rev in zip(dates, revenue_vals):
        records.append({
            'InvoiceDate': d,
            'TotalLineAmount': rev,
            'Quantity': 100,
            'Price': 10.0,
            'Invoice': f'INV_{d.strftime("%Y%m")}',
            'CustomerID': 'C100',
            'Country': 'United Kingdom',
            'IsCancelled': False
        })
        
    df = pd.DataFrame(records)
    res = forecast_monthly_revenue(df, forecast_horizon_months=6)
    
    assert "historical_monthly" in res
    assert "evaluations" in res
    assert "best_model_name" in res
    assert "future_forecast" in res
    assert len(res["future_forecast"]) == 6
    assert "ForecastRevenue" in res["future_forecast"].columns
