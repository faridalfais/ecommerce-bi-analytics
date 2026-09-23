"""Configuration and schema mapping definitions for data ingestion."""

from pathlib import Path
import json
from typing import Dict, List, Optional
from src.utils.logger import get_logger

logger = get_logger("ingestion_config")

# Canonical internal column names required by analytics/database pipeline
REQUIRED_COLUMNS = {
    "Invoice": "Transaction/Invoice identifier (string or integer)",
    "InvoiceDate": "Transaction date/timestamp",
    "StockCode": "Product or SKU identifier",
    "Quantity": "Number of units purchased (numeric)",
    "Price": "Unit price in transaction currency (numeric)"
}

OPTIONAL_COLUMNS = {
    "CustomerID": "Unique customer/client identifier (string or numeric, optional for guest checkout)",
    "Description": "Product/item description or title",
    "Country": "Country or geographic market of the customer/order",
    "Category": "Product category/department (optional)"
}

# Default aliases mapping commonly found header names to canonical column names
DEFAULT_COLUMN_ALIASES: Dict[str, List[str]] = {
    "Invoice": [
        "invoice", "invoiceno", "invoice_no", "invoice_num", "invoice_number",
        "invoice_id", "transaction_id", "transactionid", "trans_id",
        "order_id", "orderid", "order_number", "order_no", "receipt_id", "id"
    ],
    "InvoiceDate": [
        "invoicedate", "invoice_date", "transaction_date", "transactiondate",
        "trans_date", "order_date", "orderdate", "date", "datetime",
        "timestamp", "purchase_date", "sale_date", "created_at"
    ],
    "StockCode": [
        "stockcode", "stock_code", "product_id", "productid", "product_code",
        "productcode", "sku", "item_id", "itemid", "item_code", "itemcode",
        "article_id", "code"
    ],
    "Description": [
        "description", "desc", "product_name", "productname", "product_desc",
        "item_name", "itemname", "item_description", "title", "name"
    ],
    "Quantity": [
        "quantity", "qty", "units", "units_sold", "volume", "item_count",
        "count", "amount_units", "quantity_sold"
    ],
    "Price": [
        "price", "unitprice", "unit_price", "item_price", "sale_price",
        "rate", "unit_cost", "cost", "price_each"
    ],
    "CustomerID": [
        "customerid", "customer_id", "customer id", "client_id", "clientid",
        "user_id", "userid", "account_id", "shopper_id", "buyer_id"
    ],
    "Country": [
        "country", "nation", "region", "market", "country_name", "location",
        "customer_country", "billing_country", "ship_country"
    ],
    "Category": [
        "category", "product_category", "department", "item_group", "segment"
    ]
}


class DataValidationError(Exception):
    """Raised when incoming dataset fails schema requirements or validation."""
    pass


def load_custom_column_mapping(mapping_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load user-defined column mapping JSON file if present.
    Accepts both:
      { "raw_col_name": "CanonicalColName" }
    or
      { "CanonicalColName": "raw_col_name" }
    """
    if mapping_path is None:
        mapping_path = Path("data/raw/custom/column_mapping.json")

    if not mapping_path.exists():
        return {}

    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            logger.warning(f"Mapping at {mapping_path} is not a valid JSON object. Ignoring.")
            return {}

        logger.info(f"Loaded custom column mapping from {mapping_path}: {data}")
        return data
    except Exception as e:
        logger.warning(f"Failed to read custom mapping file {mapping_path}: {e}")
        return {}
