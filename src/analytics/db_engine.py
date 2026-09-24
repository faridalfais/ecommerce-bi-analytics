import os
import sqlite3
import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

# Gracefully load environment variables from .env if python-dotenv is present
_ROOT = Path(__file__).resolve().parents[2]
try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    env_file = _ROOT / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

# SQLAlchemy optional import with native sqlite3 compatibility
try:
    from sqlalchemy import create_engine, text
    _HAS_SQLALCHEMY = True
except ImportError:
    create_engine = None
    text = None
    _HAS_SQLALCHEMY = False

logger = get_logger("db_engine")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/ecommerce.db")
DATABASE_DIR = _ROOT / "database"


def get_db_engine():
    """Create and return SQLAlchemy database engine or SQLite connection wrapper."""
    if _HAS_SQLALCHEMY:
        db_url = DATABASE_URL
        if db_url.startswith("sqlite"):
            # Resolve relative sqlite paths to absolute using repo root
            # This prevents CWD-dependent path failures on Streamlit Cloud
            db_path_str = db_url.replace("sqlite:///", "", 1)
            db_path = Path(db_path_str)
            if not db_path.is_absolute():
                db_path = _ROOT / db_path_str
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{db_path.as_posix()}"
        return create_engine(db_url, echo=False)
    else:
        # Fallback to direct SQLite connection wrapper
        db_path = DATABASE_DIR / "ecommerce.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(str(db_path))


def init_database_schema(engine=None):
    """Execute schema.sql to create database tables and indexes."""
    if engine is None:
        engine = get_db_engine()
        
    schema_path = DATABASE_DIR / "schema.sql"
    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}")
        return
        
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        
    if _HAS_SQLALCHEMY and hasattr(engine, "url"):
        logger.info(f"Initializing database schema via engine {engine.url}...")
        if engine.url.drivername.startswith("sqlite"):
            raw_conn = engine.raw_connection()
            try:
                cursor = raw_conn.cursor()
                cursor.executescript(schema_sql)
                raw_conn.commit()
                logger.info("SQLite schema initialized successfully.")
            finally:
                raw_conn.close()
        else:
            with engine.begin() as conn:
                for statement in schema_sql.split(";"):
                    stmt = statement.strip()
                    if stmt:
                        conn.execute(text(stmt))
            logger.info("PostgreSQL schema initialized successfully.")
    else:
        # Direct sqlite3 connection
        conn = engine if isinstance(engine, sqlite3.Connection) else sqlite3.connect(str(DATABASE_DIR / "ecommerce.db"))
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()
        logger.info("SQLite schema initialized successfully (native).")


def populate_database(df_clean: pd.DataFrame, engine=None):
    """Populate fact and dimension tables from cleaned DataFrame."""
    if engine is None:
        engine = get_db_engine()
        
    logger.info(f"Populating database tables with {len(df_clean)} cleaned records...")
    
    # 1. Fact Transactions
    fact_df = df_clean[[
        'Invoice', 'StockCode', 'Description', 'Quantity',
        'InvoiceDate', 'Price', 'TotalLineAmount', 'CustomerID', 'Country'
    ]].copy()
    fact_df.rename(columns={
        'Invoice': 'invoice_no',
        'StockCode': 'stock_code',
        'Description': 'description',
        'Quantity': 'quantity',
        'InvoiceDate': 'invoice_date',
        'Price': 'unit_price',
        'TotalLineAmount': 'total_line_amount',
        'CustomerID': 'customer_id',
        'Country': 'country'
    }, inplace=True)
    fact_df['is_cancelled'] = False
    
    fact_df.to_sql("fact_transactions", con=engine, if_exists="append", index=False, chunksize=50000)
    logger.info("fact_transactions table populated.")
    
    # 2. Dim Customer
    valid_cust = df_clean.dropna(subset=['CustomerID'])
    cust_dim = valid_cust.groupby('CustomerID').agg(
        country=('Country', 'last'),
        first_purchase_date=('InvoiceDate', 'min'),
        last_purchase_date=('InvoiceDate', 'max'),
        total_orders=('Invoice', 'nunique'),
        total_spend=('TotalLineAmount', 'sum')
    ).reset_index()
    cust_dim.rename(columns={'CustomerID': 'customer_id'}, inplace=True)
    cust_dim['total_spend'] = cust_dim['total_spend'].round(2)
    
    cust_dim.to_sql("dim_customer", con=engine, if_exists="append", index=False)
    logger.info("dim_customer table populated.")
    
    # 3. Dim Product
    prod_dim = df_clean.groupby('StockCode').agg(
        description=('Description', 'last'),
        latest_unit_price=('Price', 'last'),
        total_units_sold=('Quantity', 'sum'),
        total_revenue=('TotalLineAmount', 'sum')
    ).reset_index()
    prod_dim.rename(columns={'StockCode': 'stock_code'}, inplace=True)
    prod_dim['total_revenue'] = prod_dim['total_revenue'].round(2)
    
    prod_dim.to_sql("dim_product", con=engine, if_exists="append", index=False)
    logger.info("dim_product table populated.")
    
    # 4. Dim Date
    dates = pd.date_range(start=df_clean['InvoiceDate'].min().floor('D'),
                          end=df_clean['InvoiceDate'].max().ceil('D'), freq='D')
    date_dim = pd.DataFrame({
        'date_key': dates.date,
        'year': dates.year,
        'month': dates.month,
        'year_month': dates.strftime('%Y-%m'),
        'day': dates.day,
        'day_name': dates.day_name(),
        'quarter': dates.quarter
    })
    date_dim.to_sql("dim_date", con=engine, if_exists="append", index=False)
    logger.info("dim_date table populated.")


def run_sql_query(query_str_or_file: str, engine=None) -> pd.DataFrame:
    """Execute SQL query string or read SQL query from file path. Handles multi-statement files."""
    if engine is None:
        engine = get_db_engine()
        
    sql_text = query_str_or_file
    query_file = DATABASE_DIR / "queries" / query_str_or_file
    if query_file.exists():
        with open(query_file, "r", encoding="utf-8") as f:
            sql_text = f.read()
            
    # Clean SQL comments and split multi-statement SQL files
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]
    
    df = pd.DataFrame()
    if _HAS_SQLALCHEMY and hasattr(engine, "connect"):
        with engine.connect() as conn:
            for stmt in statements:
                lines = [l for l in stmt.split('\n') if not l.strip().startswith('--')]
                clean_stmt = '\n'.join(lines).strip()
                if clean_stmt:
                    df = pd.read_sql_query(text(clean_stmt), conn)
    else:
        conn = engine if isinstance(engine, sqlite3.Connection) else sqlite3.connect(str(DATABASE_DIR / "ecommerce.db"))
        for stmt in statements:
            lines = [l for l in stmt.split('\n') if not l.strip().startswith('--')]
            clean_stmt = '\n'.join(lines).strip()
            if clean_stmt:
                df = pd.read_sql_query(clean_stmt, conn)
    return df


if __name__ == "__main__":
    eng = get_db_engine()
    init_database_schema(eng)
