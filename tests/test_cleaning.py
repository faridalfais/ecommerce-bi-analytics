import pandas as pd
from datetime import datetime
from src.cleaning.cleaner import clean_transaction_data


def test_clean_transaction_data():
    raw_data = pd.DataFrame({
        'Invoice': ['489434', 'C489435', '489436', '489436', '489437'],
        'StockCode': ['85048', '79323', '22041', '22041', '21232'],
        'Description': ['Item A', 'Item B', 'Item C', 'Item C', 'Item D'],
        'Quantity': [10, -5, 2, 2, 0],
        'InvoiceDate': [datetime(2009, 12, 1), datetime(2009, 12, 1), datetime(2009, 12, 2), datetime(2009, 12, 2), datetime(2009, 12, 3)],
        'Price': [2.50, 5.00, 1.00, 1.00, 0.00],
        'CustomerID': [13085.0, 13085.0, 13086.0, 13086.0, None],
        'Country': ['United Kingdom', 'United Kingdom', 'France', 'France', 'United Kingdom']
    })
    
    usable_df, summary = clean_transaction_data(raw_data, save_processed=False)
    
    assert summary['raw_record_count'] == 5
    assert summary['cancellation_record_count'] == 1
    assert summary['duplicate_count'] == 1
    assert summary['invalid_price_count'] == 1
    assert len(usable_df) == 2  # Only Invoice 489434 and one 489436
    assert 'TotalLineAmount' in usable_df.columns
    assert usable_df['TotalLineAmount'].iloc[0] == 25.0  # 10 * 2.50
