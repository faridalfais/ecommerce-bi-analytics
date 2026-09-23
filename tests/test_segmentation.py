import pandas as pd
from datetime import datetime
from src.segmentation.rfm import calculate_rfm


def test_calculate_rfm():
    data = pd.DataFrame({
        'Invoice': ['101', '102', '103', '104', '105'],
        'StockCode': ['A', 'B', 'C', 'D', 'E'],
        'Quantity': [1, 2, 3, 4, 5],
        'Price': [10.0, 10.0, 10.0, 10.0, 10.0],
        'TotalLineAmount': [10.0, 20.0, 30.0, 40.0, 50.0],
        'CustomerID': ['C1', 'C2', 'C3', 'C4', 'C5'],
        'Country': ['United Kingdom'] * 5,
        'InvoiceDate': [
            datetime(2010, 1, 1), datetime(2010, 2, 1), datetime(2010, 3, 1),
            datetime(2010, 4, 1), datetime(2010, 5, 1)
        ],
        'IsCancelled': [False] * 5
    })
    
    rfm = calculate_rfm(data, reference_date=datetime(2010, 6, 1))
    
    assert len(rfm) == 5
    assert 'Recency' in rfm.columns
    assert 'Frequency' in rfm.columns
    assert 'Monetary' in rfm.columns
    assert 'Segment' in rfm.columns
    assert set(rfm['R_Score']).issubset({1, 2, 3, 4, 5})
