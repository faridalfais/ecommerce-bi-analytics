import pandas as pd
import numpy as np
from scipy import stats
from src.utils.logger import get_logger

logger = get_logger("stats_analysis")

def analyze_macro_correlations(monthly_revenue_df: pd.DataFrame, macro_df: pd.DataFrame) -> dict:
    """
    Perform statistical correlation analysis between annual macro-economic indicators
    (UK Inflation rate, GDP growth) and aggregate retailer performance.
    """
    logger.info("Performing statistical correlation and hypothesis testing...")
    
    monthly_rev = monthly_revenue_df.copy()
    monthly_rev['Year'] = pd.to_datetime(monthly_rev['Date']).dt.year
    
    annual_rev = monthly_rev.groupby('Year').agg(
        AnnualRevenue=('Revenue', 'sum'),
        AvgMonthlyRevenue=('Revenue', 'mean'),
        MonthCount=('Revenue', 'count')
    ).reset_index()
    
    merged = pd.merge(annual_rev, macro_df, left_on='Year', right_on='year', how='inner')
    
    correlations = {}
    if len(merged) >= 2:
        for indicator in merged['indicator_code'].unique():
            sub = merged[merged['indicator_code'] == indicator]
            if len(sub) >= 2:
                r_val, p_val = stats.pearsonr(sub['AnnualRevenue'], sub['value'])
                s_val, sp_val = stats.spearmanr(sub['AnnualRevenue'], sub['value'])
                correlations[indicator] = {
                    "indicator_name": sub['indicator_name'].iloc[0],
                    "pearson_r": round(float(r_val), 4),
                    "pearson_pvalue": round(float(p_val), 4),
                    "spearman_r": round(float(s_val), 4),
                    "spearman_pvalue": round(float(sp_val), 4),
                    "sample_size": len(sub)
                }
                
    # Descriptive statistics summary of transaction amounts
    desc_stats = {
        "mean_revenue": float(monthly_rev['Revenue'].mean()),
        "std_revenue": float(monthly_rev['Revenue'].std()),
        "skewness": float(stats.skew(monthly_rev['Revenue'])),
        "kurtosis": float(stats.kurtosis(monthly_rev['Revenue']))
    }
    
    return {
        "macro_merged": merged,
        "correlations": correlations,
        "descriptive_stats": desc_stats
    }
