# src/clustering_model.py
from sklearn.cluster import KMeans
import joblib
import pandas as pd
import os

def run_clustering(df, X_scaled, k=4, scaler=None, save=True):
    kmeans = KMeans(n_clusters=k, random_state=42)
    df['Cluster'] = kmeans.fit_predict(X_scaled)

    # Manual labeling of clusters (to be tuned based on analysis)
    cluster_map = {
        0: "Consistent Performer",
        1: "Late Starter",
        2: "Erratic / At-Risk",
        3: "Silent Overworker"
    }

    df['Behavior_Type'] = df['Cluster'].map(cluster_map)

    if save:
        os.makedirs("data", exist_ok=True)
        os.makedirs("models", exist_ok=True)
        df.to_csv("data/processed_attendance.csv", index=False)
        joblib.dump(kmeans, "models/kmeans_model.pkl")
        joblib.dump(scaler, "models/scaler.pkl")

    return df, kmeans


