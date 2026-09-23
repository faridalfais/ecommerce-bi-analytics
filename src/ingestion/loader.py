import io
import os
import zipfile
import requests
import pandas as pd
from pathlib import Path
from typing import Optional, Dict
from src.utils.logger import get_logger
from src.ingestion.config import (
    DataValidationError,
    load_custom_column_mapping,
)
from src.cleaning.validator import (
    resolve_and_map_columns,
    validate_required_schema,
    audit_raw_quality
)

logger = get_logger("ingestion")

UCI_DATASET_URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
DEFAULT_ECOM_DIR = Path("data/raw/ecommerce")
CUSTOM_DATA_DIR = Path("data/raw/custom")
PROCESSED_DATA_DIR = Path("data/processed")


def download_uci_dataset(dest_dir: Path = DEFAULT_ECOM_DIR) -> Path:
    """Download official UCI Online Retail II zip archive if not already present."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / "online_retail_II.zip"
    
    # Also check fallback root raw dir
    fallback_zip = Path("data/raw/online_retail_II.zip")
    if zip_path.exists() and zip_path.stat().st_size > 0:
        return zip_path
    elif fallback_zip.exists() and fallback_zip.stat().st_size > 0:
        return fallback_zip
        
    logger.info(f"Downloading UCI Online Retail II dataset from {UCI_DATASET_URL}...")
    response = requests.get(UCI_DATASET_URL, stream=True, timeout=120)
    response.raise_for_status()
    
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                
    logger.info(f"Downloaded raw dataset zip successfully to {zip_path} ({zip_path.stat().st_size} bytes)")
    return zip_path


def detect_custom_dataset(custom_dir: Path = CUSTOM_DATA_DIR) -> Optional[Path]:
    """Find any custom dataset file (.csv, .parquet, .xlsx, .xls) in data/raw/custom/."""
    if not custom_dir.exists():
        return None
        
    supported_extensions = [".parquet", ".csv", ".xlsx", ".xls"]
    for ext in supported_extensions:
        files = [p for p in custom_dir.glob(f"*{ext}") if not p.name.startswith(".")]
        if files:
            # Pick first found custom file
            logger.info(f"Detected custom dataset at {files[0]}")
            return files[0]
    return None


def read_dataset_file(file_path: Path) -> pd.DataFrame:
    """Read a dataset from disk based on its file extension."""
    suffix = file_path.suffix.lower()
    logger.info(f"Reading dataset file: {file_path}")
    
    if suffix == ".parquet":
        return pd.read_parquet(file_path)
    elif suffix == ".csv":
        return pd.read_csv(file_path, low_memory=False)
    elif suffix in [".xlsx", ".xls"]:
        excel_file = pd.ExcelFile(file_path)
        dfs = [pd.read_excel(excel_file, sheet_name=s) for s in excel_file.sheet_names]
        return pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
    else:
        raise ValueError(f"Unsupported file format '{suffix}'. Supported: .csv, .parquet, .xlsx, .xls")


def load_raw_data(
    source_path: Optional[Path] = None,
    custom_mapping: Optional[Dict[str, str]] = None,
    raw_dir: Path = DEFAULT_ECOM_DIR
) -> pd.DataFrame:
    """
    Standardized entry point for loading raw transaction datasets.
    
    Order of precedence:
    1. Explicit source_path argument if provided.
    2. Any custom dataset dropped into data/raw/custom/.
    3. Cached default ecommerce parquet (data/raw/ecommerce/ or data/raw/).
    4. Download/extract UCI Online Retail II archive.
    
    Applies automatic/custom column mapping and validates minimum required schema.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    df: Optional[pd.DataFrame] = None
    
    # 1. Check explicit source path
    if source_path is not None:
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Specified dataset path does not exist: {source_path}")
        df = read_dataset_file(source_path)
    
    # 2. Check data/raw/custom/ directory
    if df is None:
        custom_file = detect_custom_dataset()
        if custom_file is not None:
            df = read_dataset_file(custom_file)
            
    # 3. Default UCI Dataset
    if df is None:
        parquet_path = raw_dir / "online_retail_raw.parquet"
        fallback_parquet = Path("data/raw/online_retail_raw.parquet")
        
        if parquet_path.exists():
            logger.info(f"Loading default cached raw DataFrame from {parquet_path}")
            df = pd.read_parquet(parquet_path)
        elif fallback_parquet.exists():
            logger.info(f"Loading default cached raw DataFrame from {fallback_parquet}")
            df = pd.read_parquet(fallback_parquet)
        else:
            # Extract from zip
            zip_path = download_uci_dataset(raw_dir)
            logger.info(f"Extracting Excel file from zip: {zip_path}")
            with zipfile.ZipFile(zip_path, 'r') as z:
                excel_filename = [name for name in z.namelist() if name.endswith('.xlsx') or name.endswith('.xls')][0]
                excel_bytes = z.read(excel_filename)
                
            logger.info(f"Reading sheets from Excel file '{excel_filename}'...")
            excel_file = pd.ExcelFile(io.BytesIO(excel_bytes))
            dfs = [pd.read_excel(excel_file, sheet_name=s) for s in excel_file.sheet_names]
            df = pd.concat(dfs, ignore_index=True)
            
            # Cache to parquet for future runs
            try:
                df.to_parquet(parquet_path, index=False)
            except Exception:
                pass

    # 4. Column Resolution and Standard Mapping
    df, mapped_cols = resolve_and_map_columns(df, custom_mapping=custom_mapping)
    logger.info(f"Applied column mappings: {mapped_cols}")
    
    # 5. Schema Validation (Checks minimum required columns)
    validate_required_schema(df)
    
    # 6. Ensure optional canonical columns exist with defaults if omitted
    if "CustomerID" not in df.columns:
        logger.info("Optional column 'CustomerID' not found; defaulting to NaN (guest checkout).")
        df["CustomerID"] = float("nan")
    if "Description" not in df.columns:
        logger.info("Optional column 'Description' not found; defaulting to StockCode or 'UNKNOWN'.")
        df["Description"] = df["StockCode"].astype(str) if "StockCode" in df.columns else "UNKNOWN"
    if "Country" not in df.columns:
        logger.info("Optional column 'Country' not found; defaulting to 'Unspecified'.")
        df["Country"] = "Unspecified"

    # 7. Standardize string columns
    for col in ["Invoice", "StockCode", "Description", "Country"]:
        if col in df.columns:
            df[col] = df[col].astype(str)
            
    logger.info(f"Loaded {len(df):,} raw records successfully.")
    return df


if __name__ == "__main__":
    df = load_raw_data()
    print(df.head())
    print("Shape:", df.shape)
