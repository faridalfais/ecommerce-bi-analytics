import pandas as pd
from src.external_data.economic_api import fetch_world_bank_data


def test_fetch_world_bank_data():
    df = fetch_world_bank_data(country_code="GBR", start_year=2009, end_year=2011)
    
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert 'indicator_code' in df.columns
        assert 'value' in df.columns
        assert 'year' in df.columns
        assert set(df['year'].unique()).issubset({2009, 2010, 2011})
