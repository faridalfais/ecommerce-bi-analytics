# Data Directory & Ingestion Guide

This directory manages the storage, ingestion, and validation of raw and processed transaction datasets for the Business Intelligence & Customer Analytics platform.

---

## 1. Directory Structure

```
data/
├── raw/
│   ├── ecommerce/               # Default UCI Online Retail II dataset (cache/archive)
│   │   ├── online_retail_II.zip
│   │   └── online_retail_raw.parquet
│   │
│   └── custom/                  # Drop-in location for user-provided custom datasets
│       ├── .gitkeep
│       ├── column_mapping.example.json
│       └── [your_dataset.csv / .parquet / .xlsx]
│
├── processed/                   # Cleaned transaction outputs & validation audit reports
│   ├── cleaned_transactions.parquet
│   ├── all_transactions_flagged.parquet
│   ├── data_quality_report.json
│   └── data_quality_report.md
│
└── external/                    # Macro-economic reference indicators
    └── metadata.json
```

---

## 2. Where to Put Your Data

Drop any compatible transaction-level dataset file (`.csv`, `.parquet`, `.xlsx`, or `.xls`) into:

```
data/raw/custom/my_dataset.csv
```

When a file is detected in `data/raw/custom/`, the pipeline will automatically prioritize it over the default UCI dataset.

---

## 3. Required Data Structure

The pipeline is designed to work with transaction-level sales data.

### Minimum Required Columns:
| Canonical Field | Description | Supported Aliases |
| :--- | :--- | :--- |
| **`Invoice`** | Transaction / invoice / order ID | `invoice`, `invoiceno`, `transaction_id`, `order_id`, `receipt_id`, `id` |
| **`InvoiceDate`** | Date and time of purchase | `invoicedate`, `transaction_date`, `order_date`, `date`, `datetime`, `timestamp` |
| **`StockCode`** | Unique SKU or product identifier | `stockcode`, `product_id`, `sku`, `item_id`, `item_code`, `code` |
| **`Quantity`** | Units purchased (positive numeric for sales) | `quantity`, `qty`, `units`, `units_sold`, `volume`, `count` |
| **`Price`** | Unit price in local currency (positive numeric) | `price`, `unit_price`, `unitprice`, `rate`, `sale_price` |

### Optional Columns (Handled Gracefully if Missing):
| Canonical Field | Description | Default if Omitted |
| :--- | :--- | :--- |
| **`CustomerID`** | Unique customer identifier | Defaulted to `NaN` (tracked as guest checkout) |
| **`Description`** | Product / item name or description | Defaulted to SKU `StockCode` |
| **`Country`** | Customer country or geographic market | Defaulted to `"Unspecified"` |
| **`Category`** | Product category / department | Preserved if present |

> **Validation Rule**: If any minimum required column is missing, the ingestion system will halt and output an explicit diagnostic message showing which columns are missing and what columns were found in your file.

---

## 4. Column Mapping Configuration

If your dataset uses custom column headers not covered by the automatic aliases, you can define a mapping configuration in `data/raw/custom/column_mapping.json`.

### Example `data/raw/custom/column_mapping.json`:

```json
{
  "order_reference": "Invoice",
  "purchased_at": "InvoiceDate",
  "sku_number": "StockCode",
  "product_title": "Description",
  "item_qty": "Quantity",
  "unit_cost": "Price",
  "buyer_id": "CustomerID",
  "shipping_country": "Country"
}
```

---

## 5. Pre-Processing & Data Quality Rules

Before analytics tables and models are generated, the validation engine conducts:
1. **Schema Check**: Validates that all required fields are present.
2. **Cancellation Detection**: Flags invoice IDs starting with `'C'` or lines with negative quantities.
3. **Price/Quantity Scrubbing**: Segregates records with zero/negative price or quantity.
4. **Duplicate Purge**: Removes exact duplicate transaction rows.
5. **Quality Audit Report**: Automatically saves `data_quality_report.json` and `data_quality_report.md` in `data/processed/`.

No artificial metrics (such as COGS or profit margins) are fabricated.
