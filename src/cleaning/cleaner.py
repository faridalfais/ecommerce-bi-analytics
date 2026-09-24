import gc
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict
from src.utils.logger import get_logger
from src.cleaning.validator import audit_raw_quality

logger = get_logger("cleaning")

_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIR = _ROOT / "data" / "processed"


def _downcast_df(df: pd.DataFrame) -> None:
    """
    In-place dtype downcasting to reduce memory footprint.
    - float64  → float32  (halves float storage; sufficient for currency)
    - int64    → smallest safe int type
    Modifies the DataFrame in-place; returns None.
    """
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = df[col].astype("float32")
    for col in df.select_dtypes(include=["int64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")


def clean_transaction_data(df: pd.DataFrame, save_processed: bool = True) -> Tuple[pd.DataFrame, Dict[str, any]]:
    """
    Perform rigorous, documented data cleaning on raw transaction datasets.
    
    Cleaning Rationale & Rules:
    1. Standardize Strings & Dates: Strips whitespace, parses timestamps cleanly.
    2. Cancellations: Invoices prefixed with 'C' or lines with Quantity < 0 are flagged in
       'IsCancelled' and segregated from positive sales.
    3. Invalid Prices/Quantities: Records with Price <= 0 or Quantity <= 0 are excluded from net sales.
    4. Missing Customer ID: Kept for total revenue calculations (guest purchases), flagged for customer modeling.
    5. Duplicates: Exact duplicate rows are removed.
    6. Calculated Fields: TotalLineAmount = (Quantity * Price). Temporal attributes engineered.
    """
    logger.info("Starting data cleaning pipeline...")
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    raw_count = len(df)
    
    # Pre-cleaning quality audit
    raw_audit = audit_raw_quality(df)
    
    # 1. Standardize types and strings
    df = df.copy()
    if 'Invoice' in df.columns:
        df['Invoice'] = df['Invoice'].astype(str).str.strip()
    if 'StockCode' in df.columns:
        df['StockCode'] = df['StockCode'].astype(str).str.strip()
    
    if 'Description' in df.columns:
        df['Description'] = df['Description'].fillna("UNKNOWN").astype(str).str.strip()
    else:
        df['Description'] = df['StockCode'].astype(str) if 'StockCode' in df.columns else "UNKNOWN"

    if 'Country' in df.columns:
        df['Country'] = df['Country'].fillna("Unspecified").astype(str).str.strip()
    else:
        df['Country'] = "Unspecified"
    
    # Parse dates safely
    if 'InvoiceDate' in df.columns:
        df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
        invalid_dates = df['InvoiceDate'].isna()
        if invalid_dates.sum() > 0:
            logger.warning(f"Dropping {invalid_dates.sum()} records with unparseable InvoiceDate")
            df = df[~invalid_dates].copy()
    
    # Clean CustomerID: convert floats/strings like 13085.0 to string "13085", retain NaN as NaN
    def clean_cust_id(val):
        if pd.isna(val) or val is None or str(val).strip() in ('', 'nan', 'NaN', 'None', '<NA>'):
            return np.nan
        try:
            return str(int(float(val)))
        except (ValueError, TypeError):
            return str(val).strip()

    if 'CustomerID' in df.columns:
        df['CustomerID'] = df['CustomerID'].apply(clean_cust_id)
    else:
        df['CustomerID'] = np.nan
    
    # Ensure numeric columns
    if 'Quantity' in df.columns:
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)
    if 'Price' in df.columns:
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0.0)
    
    # 2. Identify Cancellations
    inv_series = df['Invoice'] if 'Invoice' in df.columns else pd.Series([""] * len(df))
    qty_series = df['Quantity'] if 'Quantity' in df.columns else pd.Series([0] * len(df))
    df['IsCancelled'] = inv_series.str.startswith('C') | (qty_series < 0)
    
    # 3. Data Quality Metric Collection
    duplicate_count = int(df.duplicated().sum())
    missing_customer_count = int(df['CustomerID'].isna().sum())
    missing_desc_count = int((df['Description'].isin(["UNKNOWN", ""])).sum())
    cancellation_count = int(df['IsCancelled'].sum())
    invalid_price_count = int((df['Price'] <= 0).sum()) if 'Price' in df.columns else 0
    invalid_qty_count = int((df['Quantity'] <= 0).sum()) if 'Quantity' in df.columns else 0
    
    # 4. Remove Duplicates
    df = df.drop_duplicates().reset_index(drop=True)
    
    # 5. Filter Usable Sales Transactions (Positive net sales)
    usable_df = df[
        (~df['IsCancelled']) & 
        (df['Quantity'] > 0) & 
        (df['Price'] > 0)
    ].copy()
    
    # 6. Feature Engineering on Cleaned Transactions
    usable_df['TotalLineAmount'] = (usable_df['Quantity'] * usable_df['Price']).round(2)
    usable_df['InvoiceYear'] = usable_df['InvoiceDate'].dt.year
    usable_df['InvoiceMonth'] = usable_df['InvoiceDate'].dt.month
    usable_df['InvoiceYearMonth'] = usable_df['InvoiceDate'].dt.strftime('%Y-%m')
    usable_df['InvoiceDay'] = usable_df['InvoiceDate'].dt.day
    usable_df['DayOfWeek'] = usable_df['InvoiceDate'].dt.day_name()
    usable_df['Hour'] = usable_df['InvoiceDate'].dt.hour
    
    quality_summary = {
        "raw_record_count": raw_count,
        "duplicate_count": duplicate_count,
        "missing_customer_id_count": missing_customer_count,
        "missing_description_count": missing_desc_count,
        "cancellation_record_count": cancellation_count,
        "invalid_price_count": invalid_price_count,
        "invalid_quantity_count": invalid_qty_count,
        "cleaned_usable_record_count": len(usable_df),
        "unique_customers_count": int(usable_df['CustomerID'].dropna().nunique()),
        "unique_products_count": int(usable_df['StockCode'].nunique()) if 'StockCode' in usable_df.columns else 0,
        "total_cleaned_revenue": float(usable_df['TotalLineAmount'].sum()),
        "audit_details": raw_audit
    }
    
    logger.info(f"Data cleaning complete. Raw: {raw_count:,} -> Usable: {len(usable_df):,} records")
    logger.info(f"Total Cleaned Revenue: £{quality_summary['total_cleaned_revenue']:,.2f}")

    if save_processed:
        # MEM: Downcast numeric columns before writing to parquet to reduce
        # the on-disk and in-memory footprint by ~30-40%.
        _downcast_df(usable_df)
        usable_df.to_parquet(PROCESSED_DATA_DIR / "cleaned_transactions.parquet", index=False)

        # Save the flagged full-transaction file then immediately free it
        _downcast_df(df)
        df.to_parquet(PROCESSED_DATA_DIR / "all_transactions_flagged.parquet", index=False)
        del df
        gc.collect()
        logger.info(f"Saved processed files to {PROCESSED_DATA_DIR}")

    return usable_df, quality_summary


if __name__ == "__main__":
    from src.ingestion.loader import load_raw_data
    raw = load_raw_data()
    clean_df, summary = clean_transaction_data(raw)
    print("Quality Summary:", summary)
