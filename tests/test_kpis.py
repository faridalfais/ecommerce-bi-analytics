import pandas as pd
from datetime import datetime
from src.analytics.metrics import compute_overall_kpis


def test_compute_overall_kpis():
    data = pd.DataFrame({
        'Invoice': ['101', '102', '103', '104'],
        'StockCode': ['A', 'B', 'C', 'D'],
        'Quantity': [2, 5, 1, 4],
        'Price': [10.0, 20.0, 50.0, 5.0],
        'TotalLineAmount': [20.0, 100.0, 50.0, 20.0],
        'CustomerID': ['C1', 'C1', 'C2', 'C3'],
        'Country': ['United Kingdom', 'United Kingdom', 'France', 'United Kingdom'],
        'InvoiceDate': [datetime(2010, 1, 1), datetime(2010, 1, 15), datetime(2010, 2, 1), datetime(2010, 2, 10)],
        'IsCancelled': [False, False, False, False]
    })
    
    kpis = compute_overall_kpis(data)
    
    assert kpis['total_revenue'] == 190.0
    assert kpis['total_orders'] == 4
    assert kpis['active_customers'] == 3
    assert kpis['average_order_value'] == 47.5  # 190 / 4
    assert kpis['repeat_purchase_rate_pct'] == 33.33  # C1 has 2 orders out of 3 customers
