import json
import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger("data_quality")

_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIR = _ROOT / "data" / "processed"

def generate_data_quality_report(quality_summary: dict, output_dir: Path = PROCESSED_DATA_DIR) -> Path:
    """Generate structured Data Quality Audit report in JSON and Markdown."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "data_quality_report.json"
    md_path = output_dir / "data_quality_report.md"
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(quality_summary, f, indent=4)
        
    md_content = f"""# Data Quality Audit Report

## Executive Data Hygiene Summary
- **Raw Transaction Records Ingested**: {quality_summary.get('raw_record_count', 0):,}
- **Usable Positive Sales Transactions**: {quality_summary.get('cleaned_usable_record_count', 0):,}
- **Total Valid Revenue Processed**: £{quality_summary.get('total_cleaned_revenue', 0.0):,.2f}
- **Unique Registered Customers**: {quality_summary.get('unique_customers_count', 0):,}
- **Unique Product SKUs**: {quality_summary.get('unique_products_count', 0):,}

## Anomaly & Data Anomaly Breakdown
| Audit Metric | Count | Impact & Handling Strategy |
| :--- | :--- | :--- |
| **Duplicate Rows** | {quality_summary.get('duplicate_count', 0):,} | Dropped exact duplicated transaction records. |
| **Cancelled Invoices ('C')** | {quality_summary.get('cancellation_record_count', 0):,} | Isolated into audit dataset; excluded from positive revenue metrics. |
| **Missing Customer ID** | {quality_summary.get('missing_customer_id_count', 0):,} | Retained for financial revenue rollup; excluded from RFM/Churn modeling. |
| **Invalid/Zero Unit Price** | {quality_summary.get('invalid_price_count', 0):,} | Excluded (system adjustments/samples/bad debt). |
| **Invalid/Zero Quantity** | {quality_summary.get('invalid_quantity_count', 0):,} | Excluded (zero or negative items). |

*Report generated automatically by E-Commerce BI Quality Pipeline.*
"""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    logger.info(f"Data quality report saved to {json_path} and {md_path}")
    return json_path

if __name__ == "__main__":
    dummy_summary = {"raw_record_count": 1000000, "cleaned_usable_record_count": 800000}
    generate_data_quality_report(dummy_summary)
