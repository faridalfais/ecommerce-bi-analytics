"""Data validation, schema checking, and quality auditing module."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from src.ingestion.config import (
    REQUIRED_COLUMNS,
    OPTIONAL_COLUMNS,
    DEFAULT_COLUMN_ALIASES,
    DataValidationError,
    load_custom_column_mapping,
)
from src.utils.logger import get_logger

logger = get_logger("validator")


def resolve_and_map_columns(
    df: pd.DataFrame,
    custom_mapping: Optional[Dict[str, str]] = None
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Map raw dataframe columns to canonical schema names using:
    1. User custom mapping config (if provided or found in data/raw/custom/column_mapping.json)
    2. Intelligent default alias matching (case-insensitive, normalized)
    3. Direct matching with existing canonical columns
    """
    df = df.copy()
    raw_columns = list(df.columns)
    mapped_dict: Dict[str, str] = {}
    
    # 1. Apply explicit custom mapping if provided
    if custom_mapping is None:
        custom_mapping = load_custom_column_mapping()

    if custom_mapping:
        for k, v in custom_mapping.items():
            # Check if k is in raw and v is canonical
            if k in raw_columns and v in list(REQUIRED_COLUMNS.keys()) + list(OPTIONAL_COLUMNS.keys()):
                mapped_dict[k] = v
            # Or if v is in raw and k is canonical
            elif v in raw_columns and k in list(REQUIRED_COLUMNS.keys()) + list(OPTIONAL_COLUMNS.keys()):
                mapped_dict[v] = k

    # 2. Automated resolution using default aliases
    normalized_raw = {str(col).strip().lower().replace(" ", "_").replace("-", "_"): col for col in raw_columns}
    
    all_targets = {**REQUIRED_COLUMNS, **OPTIONAL_COLUMNS}
    for canonical_name, aliases in DEFAULT_COLUMN_ALIASES.items():
        if canonical_name in mapped_dict.values():
            continue  # Already mapped via custom mapping
            
        # Direct match (case-insensitive)
        can_norm = canonical_name.lower().replace(" ", "_")
        if can_norm in normalized_raw:
            raw_orig = normalized_raw[can_norm]
            mapped_dict[raw_orig] = canonical_name
            continue
            
        # Alias match
        for alias in aliases:
            alias_norm = alias.lower().replace(" ", "_")
            if alias_norm in normalized_raw:
                raw_orig = normalized_raw[alias_norm]
                if raw_orig not in mapped_dict:
                    mapped_dict[raw_orig] = canonical_name
                    break

    # Apply rename
    df.rename(columns=mapped_dict, inplace=True)
    return df, mapped_dict


def validate_required_schema(df: pd.DataFrame) -> None:
    """
    Verify that all minimum required canonical columns exist in the DataFrame.
    Raises DataValidationError with clear diagnostic information if any are missing.
    """
    present_columns = set(df.columns)
    missing_required = [col for col in REQUIRED_COLUMNS if col not in present_columns]
    
    if missing_required:
        missing_details = [f" - '{col}': {REQUIRED_COLUMNS[col]}" for col in missing_required]
        err_msg = (
            f"\n[DATA VALIDATION ERROR] Missing {len(missing_required)} required column(s) in dataset:\n"
            + "\n".join(missing_details)
            + f"\n\nColumns present in your dataset:\n {list(df.columns)}\n\n"
            + "How to resolve:\n"
            + "1. Ensure your dataset contains the required fields (transaction ID, date, product ID, quantity, price).\n"
            + "2. Map your column names in 'data/raw/custom/column_mapping.json' or use supported standard aliases.\n"
            + "   Example column_mapping.json:\n"
            + '   {\n     "my_order_id": "Invoice",\n     "my_order_date": "InvoiceDate",\n'
            + '     "my_item_code": "StockCode",\n     "units": "Quantity",\n     "rate": "Price"\n   }'
        )
        logger.error(err_msg)
        raise DataValidationError(err_msg)


def audit_raw_quality(df: pd.DataFrame) -> Dict[str, any]:
    """
    Perform pre-ingestion data quality checks and return comprehensive diagnostics.
    Does NOT modify the data or fabricate metrics.
    """
    total_records = len(df)
    
    # 1. Missing values per column
    missing_per_col = {col: int(df[col].isna().sum()) for col in df.columns}
    
    # 2. Date parseability
    invalid_dates_count = 0
    if "InvoiceDate" in df.columns:
        parsed_dates = pd.to_datetime(df["InvoiceDate"], errors="coerce")
        invalid_dates_count = int(parsed_dates.isna().sum() - df["InvoiceDate"].isna().sum())
    
    # 3. Numeric validity (Quantity & Price)
    invalid_qty_count = 0
    negative_qty_count = 0
    zero_qty_count = 0
    if "Quantity" in df.columns:
        numeric_qty = pd.to_numeric(df["Quantity"], errors="coerce")
        invalid_qty_count = int(numeric_qty.isna().sum() - df["Quantity"].isna().sum())
        negative_qty_count = int((numeric_qty < 0).sum())
        zero_qty_count = int((numeric_qty == 0).sum())
        
    invalid_price_count = 0
    negative_price_count = 0
    zero_price_count = 0
    if "Price" in df.columns:
        numeric_price = pd.to_numeric(df["Price"], errors="coerce")
        invalid_price_count = int(numeric_price.isna().sum() - df["Price"].isna().sum())
        negative_price_count = int((numeric_price < 0).sum())
        zero_price_count = int((numeric_price == 0).sum())

    # 4. Duplicates
    duplicate_rows_count = int(df.duplicated().sum())
    
    # 5. Cancellations detection (if Invoice is string)
    cancellation_count = 0
    if "Invoice" in df.columns:
        inv_str = df["Invoice"].astype(str).str.strip()
        cancellation_count = int(inv_str.str.startswith("C").sum())
        if "Quantity" in df.columns:
            # negative quantities also count as cancellation/return indicators
            cancellation_count = max(cancellation_count, negative_qty_count)

    quality_audit = {
        "total_records": total_records,
        "duplicate_rows": duplicate_rows_count,
        "missing_values_by_column": missing_per_col,
        "invalid_date_formats": invalid_dates_count,
        "quantity_anomalies": {
            "negative_quantities": negative_qty_count,
            "zero_quantities": zero_qty_count,
            "non_numeric_quantities": invalid_qty_count
        },
        "price_anomalies": {
            "negative_prices": negative_price_count,
            "zero_prices": zero_price_count,
            "non_numeric_prices": invalid_price_count
        },
        "cancellations_or_returns": cancellation_count
    }
    
    return quality_audit
