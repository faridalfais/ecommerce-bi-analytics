import pandas as pd
from datetime import datetime

from src.ingestion.config import DataValidationError
from src.cleaning.validator import (
    resolve_and_map_columns,
    validate_required_schema,
    audit_raw_quality
)
from src.cleaning.cleaner import clean_transaction_data


def test_resolve_and_map_columns_standard_aliases():
    """Verify standard header variations are automatically mapped to canonical names."""
    custom_df = pd.DataFrame({
        'transaction_id': ['TX1001', 'TX1002'],
        'transaction_date': ['2024-01-15 10:00:00', '2024-01-16 11:00:00'],
        'product_id': ['SKU_A', 'SKU_B'],
        'product_name': ['Widget Alpha', 'Widget Beta'],
        'units': [5, 10],
        'unit_price': [12.50, 4.00],
        'client_id': ['CUST_99', 'CUST_100'],
        'region': ['United Kingdom', 'Germany']
    })
    
    mapped_df, mapping = resolve_and_map_columns(custom_df)
    
    assert 'Invoice' in mapped_df.columns
    assert 'InvoiceDate' in mapped_df.columns
    assert 'StockCode' in mapped_df.columns
    assert 'Description' in mapped_df.columns
    assert 'Quantity' in mapped_df.columns
    assert 'Price' in mapped_df.columns
    assert 'CustomerID' in mapped_df.columns
    assert 'Country' in mapped_df.columns


def test_resolve_with_custom_mapping_dict():
    """Verify custom user dictionary overrides/maps obscure column names."""
    custom_df = pd.DataFrame({
        'order_ref': ['ORD-01'],
        'stamp': ['2024-02-01'],
        'sku_code': ['PROD-9'],
        'vol': [3],
        'cost_per_item': [19.99]
    })
    
    custom_map = {
        'order_ref': 'Invoice',
        'stamp': 'InvoiceDate',
        'sku_code': 'StockCode',
        'vol': 'Quantity',
        'cost_per_item': 'Price'
    }
    
    mapped_df, _ = resolve_and_map_columns(custom_df, custom_mapping=custom_map)
    validate_required_schema(mapped_df)
    
    assert set(['Invoice', 'InvoiceDate', 'StockCode', 'Quantity', 'Price']).issubset(mapped_df.columns)


def test_validate_required_schema_missing_column_raises_error():
    """Verify DataValidationError is raised when required columns are absent."""
    incomplete_df = pd.DataFrame({
        'Invoice': ['INV01'],
        'StockCode': ['ITEM1'],
        'Quantity': [5]
        # Missing InvoiceDate and Price
    })
    
    raised = False
    try:
        validate_required_schema(incomplete_df)
    except DataValidationError as exc:
        raised = True
        err_str = str(exc)
        assert "Missing" in err_str
        assert "InvoiceDate" in err_str
        assert "Price" in err_str
        
    assert raised, "Expected DataValidationError was not raised"


def test_optional_columns_defaulting_and_cleaning():
    """Verify clean_transaction_data handles missing optional columns (e.g. no CustomerID/Country)."""
    raw_df = pd.DataFrame({
        'Invoice': ['10001', '10002'],
        'InvoiceDate': [datetime(2024, 1, 1), datetime(2024, 1, 2)],
        'StockCode': ['SKU1', 'SKU2'],
        'Quantity': [2, 4],
        'Price': [10.0, 5.0]
        # No CustomerID, Description, or Country provided
    })
    
    clean_df, summary = clean_transaction_data(raw_df, save_processed=False)
    
    assert len(clean_df) == 2
    assert 'CustomerID' in clean_df.columns
    assert 'Country' in clean_df.columns
    assert clean_df['TotalLineAmount'].sum() == 40.0  # 2*10 + 4*5


def test_audit_raw_quality():
    """Verify pre-cleaning quality audit detects anomalies accurately."""
    dirty_df = pd.DataFrame({
        'Invoice': ['1', 'C2', '3', '3'],
        'InvoiceDate': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-03'],
        'StockCode': ['A', 'B', 'C', 'C'],
        'Quantity': [10, -5, 0, 0],
        'Price': [2.0, 2.0, -1.0, -1.0]
    })
    
    audit = audit_raw_quality(dirty_df)
    
    assert audit['total_records'] == 4
    assert audit['duplicate_rows'] == 1
    assert audit['quantity_anomalies']['negative_quantities'] == 1
    assert audit['price_anomalies']['negative_prices'] == 2
