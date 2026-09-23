import pandas as pd
import numpy as np
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger("rfm_segmentation")

def calculate_rfm(df: pd.DataFrame, reference_date: datetime = None) -> pd.DataFrame:
    """
    Calculate Recency, Frequency, Monetary (RFM) metrics for registered customers.
    Filters out missing CustomerID transactions.
    """
    logger.info("Computing Customer RFM metrics...")
    valid_df = df.dropna(subset=['CustomerID']).copy()
    valid_df['InvoiceDate'] = pd.to_datetime(valid_df['InvoiceDate'])
    
    if reference_date is None:
        reference_date = valid_df['InvoiceDate'].max() + pd.Timedelta(days=1)
        
    rfm = valid_df.groupby('CustomerID').agg(
        Recency=('InvoiceDate', lambda x: (reference_date - x.max()).days),
        Frequency=('Invoice', 'nunique'),
        Monetary=('TotalLineAmount', 'sum'),
        FirstPurchase=('InvoiceDate', 'min'),
        LastPurchase=('InvoiceDate', 'max'),
        Country=('Country', 'last')
    ).reset_index()
    
    rfm['Monetary'] = rfm['Monetary'].round(2)
    rfm['AvgOrderValue'] = (rfm['Monetary'] / rfm['Frequency']).round(2)
    
    # 1-5 Score assignment using quantiles (labels 1-5)
    # For Recency: lower days = higher score (5 is best)
    rfm['R_Score'] = pd.qcut(rfm['Recency'], q=5, labels=[5, 4, 3, 2, 1], duplicates='drop').astype(int)
    # For Frequency and Monetary: higher value = higher score (5 is best)
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    
    rfm['RFM_Cell'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
    rfm['RFM_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']
    
    # Business Segment Mapping
    def assign_segment(row):
        r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
        if r >= 4 and f >= 4 and m >= 4:
            return 'Champions'
        elif f >= 3 and m >= 3 and r >= 3:
            return 'Loyal Customers'
        elif r >= 4 and f <= 2:
            return 'New Customers'
        elif r >= 3 and f >= 2:
            return 'Potential Loyalists'
        elif r == 3 and f <= 2:
            return 'Promising'
        elif r == 2 and f >= 3:
            return 'At Risk'
        elif r == 2 and f <= 2:
            return 'About To Sleep'
        elif r == 1 and f >= 3:
            return 'Can\'t Lose Them'
        else:
            return 'Hibernating / Lost'
            
    rfm['Segment'] = rfm.apply(assign_segment, axis=1)
    
    logger.info(f"Calculated RFM for {len(rfm)} unique registered customers.")
    return rfm

def get_rfm_segment_summary(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate customer counts and financial metrics by RFM Segment."""
    summary = rfm_df.groupby('Segment').agg(
        CustomerCount=('CustomerID', 'count'),
        AvgRecencyDays=('Recency', 'mean'),
        AvgFrequency=('Frequency', 'mean'),
        TotalRevenue=('Monetary', 'sum'),
        AvgRevenuePerCustomer=('Monetary', 'mean')
    ).reset_index()
    
    total_rev = summary['TotalRevenue'].sum()
    summary['RevenueSharePct'] = (summary['TotalRevenue'] / total_rev * 100.0).round(2)
    summary['AvgRecencyDays'] = summary['AvgRecencyDays'].round(1)
    summary['AvgFrequency'] = summary['AvgFrequency'].round(1)
    summary['AvgRevenuePerCustomer'] = summary['AvgRevenuePerCustomer'].round(2)
    
    return summary.sort_values(by='TotalRevenue', ascending=False)
