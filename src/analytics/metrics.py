import pandas as pd
import numpy as np
from src.utils.logger import get_logger

logger = get_logger("metrics")

def compute_overall_kpis(df_clean: pd.DataFrame) -> dict:
    """Compute top-level business executive KPIs from cleaned transaction dataset."""
    valid_df = df_clean[~df_clean['IsCancelled']].copy()
    
    total_revenue = float(valid_df['TotalLineAmount'].sum())
    total_orders = int(valid_df['Invoice'].nunique())
    total_units = int(valid_df['Quantity'].sum())
    
    reg_df = valid_df.dropna(subset=['CustomerID'])
    active_customers = int(reg_df['CustomerID'].nunique())
    
    aov = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
    arpu = round(total_revenue / active_customers, 2) if active_customers > 0 else 0.0
    
    # Customer Repeat Purchase Rate
    cust_orders = reg_df.groupby('CustomerID')['Invoice'].nunique()
    repeat_cust_count = int((cust_orders > 1).sum())
    repeat_rate_pct = round((repeat_cust_count / active_customers * 100.0), 2) if active_customers > 0 else 0.0
    
    # Monthly Growth Rate
    valid_df['InvoiceDate'] = pd.to_datetime(valid_df['InvoiceDate'])
    monthly_rev = valid_df.resample('ME', on='InvoiceDate')['TotalLineAmount'].sum()
    if len(monthly_rev) >= 2:
        latest_mom = round(((monthly_rev.iloc[-1] - monthly_rev.iloc[-2]) / monthly_rev.iloc[-2] * 100.0), 2)
    else:
        latest_mom = 0.0
        
    # Top Country Share
    uk_rev = float(valid_df[valid_df['Country'] == 'United Kingdom']['TotalLineAmount'].sum())
    uk_share_pct = round((uk_rev / total_revenue * 100.0), 2) if total_revenue > 0 else 0.0
    
    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_units_sold": total_units,
        "active_customers": active_customers,
        "average_order_value": aov,
        "average_revenue_per_user": arpu,
        "repeat_purchase_rate_pct": repeat_rate_pct,
        "latest_mom_growth_pct": latest_mom,
        "uk_revenue_share_pct": uk_share_pct,
        "max_transaction_date": valid_df['InvoiceDate'].max().strftime('%Y-%m-%d %H:%M')
    }

def generate_executive_insights(kpi_dict: dict, rfm_summary: pd.DataFrame = None, forecast_dict: dict = None) -> dict:
    """
    Synthesize computed analytical results into structured data-driven executive narrative.
    Strictly follows: WHAT HAPPENED? -> WHY? -> BUSINESS IMPACT -> WHAT SHOULD MANAGEMENT WATCH?
    """
    mom_growth = kpi_dict.get('latest_mom_growth_pct', 0.0)
    repeat_rate = kpi_dict.get('repeat_purchase_rate_pct', 0.0)
    aov = kpi_dict.get('average_order_value', 0.0)
    uk_share = kpi_dict.get('uk_revenue_share_pct', 0.0)
    
    # What Happened
    if mom_growth >= 0:
        what_happened_en = f"Total cumulative revenue reached £{kpi_dict['total_revenue']:,.2f} across {kpi_dict['total_orders']:,} orders. The most recent month demonstrated positive revenue expansion of +{mom_growth}% MoM."
        what_happened_id = f"Total akumulasi pendapatan mencapai £{kpi_dict['total_revenue']:,.2f} dari {kpi_dict['total_orders']:,} pesanan. Bulan terbaru menunjukkan pertumbuhan positif sebesar +{mom_growth}% MoM."
    else:
        what_happened_en = f"Total cumulative revenue reached £{kpi_dict['total_revenue']:,.2f} across {kpi_dict['total_orders']:,} orders. The latest month saw a revenue contraction of {mom_growth}% MoM."
        what_happened_id = f"Total akumulasi pendapatan mencapai £{kpi_dict['total_revenue']:,.2f} dari {kpi_dict['total_orders']:,} pesanan. Bulan terbaru mengalami penurunan pendapatan sebesar {mom_growth}% MoM."
        
    # Why
    why_en = f"Growth dynamics are primarily propelled by an Average Order Value of £{aov:.2f} and a solid customer repeat purchase rate of {repeat_rate}%. Geographic revenue is heavily concentrated in the domestic UK market ({uk_share}% of sales)."
    why_id = f"Dinamika pertumbuhan utamanya didorong oleh Rata-rata Nilai Pesanan sebesar £{aov:.2f} dan tingkat pembelian berulang pelanggan yang solid sebesar {repeat_rate}%. Pendapatan geografis terpusat di pasar domestik Inggris ({uk_share}% dari total penjualan)."
    
    # Business Impact
    impact_en = f"Repeat customers generate higher lifetime monetary value than first-time buyers. However, heavy reliance on the domestic UK market increases vulnerability to UK macro-economic demand shifts."
    impact_id = f"Pelanggan berulang menghasilkan nilai moneter seumur hidup yang lebih tinggi dibanding pembeli baru. Namun, ketergantungan yang tinggi pada pasar domestik Inggris meningkatkan kerentanan terhadap pergeseran permintaan makro-ekonomi Inggris."
    
    # What Should Management Watch
    watch_en = f"1. Monitor customer churn risk among 'At-Risk' and 'About To Sleep' RFM cohorts.\n2. Expand international market distribution to reduce geographic revenue concentration risk.\n3. Optimize inventory allocation for top 20 Pareto SKUs during peak Q4 seasonal spikes."
    watch_id = f"1. Pantau risiko churn pelanggan pada segmen RFM 'At-Risk' dan 'About To Sleep'.\n2. Perluas distribusi pasar internasional untuk mengurangi risiko konsentrasi pendapatan geografis.\n3. Optimalkan alokasi persediaan untuk 20 SKU Pareto teratas selama lonjakan musiman Q4."
    
    return {
        "en": {
            "what_happened": what_happened_en,
            "why": why_en,
            "business_impact": impact_en,
            "what_should_management_watch": watch_en
        },
        "id": {
            "what_happened": what_happened_id,
            "why": why_id,
            "business_impact": impact_id,
            "what_should_management_watch": watch_id
        }
    }
