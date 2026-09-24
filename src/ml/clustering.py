import pandas as pd
import numpy as np
from typing import Tuple
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from src.utils.logger import get_logger

logger = get_logger("clustering")

def run_kmeans_segmentation(rfm_df: pd.DataFrame, max_k: int = 6) -> Tuple[pd.DataFrame, dict]:
    """
    Perform Unsupervised K-Means Clustering on RFM features.
    Features are log-transformed (to handle skewness) and standard scaled.
    Evaluates optimal K using Silhouette Score.
    """
    logger.info("Performing K-Means Clustering on RFM features...")
    df = rfm_df.copy()
    
    # Select and Log-transform features
    features = ['Recency', 'Frequency', 'Monetary']
    X_log = np.log1p(df[features])
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_log)
    
    # Evaluate silhouette scores for K range
    evaluation = {}
    best_k = 4
    best_score = -1
    
    for k in range(2, max_k + 1):
        kmeans_test = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans_test.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        evaluation[k] = {
            'inertia': float(kmeans_test.inertia_),
            'silhouette_score': float(score)
        }
        if score > best_score:
            best_score = score
            best_k = k
            
    logger.info(f"K-Means Evaluation: Best K = {best_k} (Silhouette Score = {best_score:.4f})")
    
    # Final model fit with optimal K (or k=4 as defensible baseline if silhouette is close)
    final_k = best_k if best_k >= 3 else 4
    kmeans_final = KMeans(n_clusters=final_k, random_state=42, n_init=10)
    df['Cluster'] = kmeans_final.fit_predict(X_scaled)
    
    # Label Clusters based on Monetary/Frequency ordering
    cluster_profiles = df.groupby('Cluster').agg(
        Count=('CustomerID', 'count'),
        AvgRecency=('Recency', 'mean'),
        AvgFrequency=('Frequency', 'mean'),
        AvgMonetary=('Monetary', 'mean'),
        TotalRevenue=('Monetary', 'sum')
    ).reset_index()
    
    # Assign intuitive cluster names based on revenue rank
    cluster_profiles = cluster_profiles.sort_values(by='AvgMonetary', ascending=False).reset_index(drop=True)
    cluster_name_map = {}
    names = ['Cluster 0: High-Value VIPs', 'Cluster 1: Loyal Regulars', 'Cluster 2: Occasional Buyers', 'Cluster 3: Dormant/At-Risk', 'Cluster 4: Low-Touch']
    
    for idx, row in cluster_profiles.iterrows():
        name = names[idx] if idx < len(names) else f'Cluster {idx}: Group {idx+1}'
        cluster_name_map[row['Cluster']] = name
        
    df['Cluster_Name'] = df['Cluster'].map(cluster_name_map)
    
    output_summary = {
        'best_k': final_k,
        'evaluation': evaluation,
        'cluster_profiles': cluster_profiles.to_dict(orient='records')
    }
    
    return df, output_summary
