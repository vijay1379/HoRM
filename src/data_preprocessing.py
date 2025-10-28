# src/data_preprocessing.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from datetime import time

def to_hours(x):
    """Convert time string or time object to float hour."""
    if pd.isna(x):
        return np.nan
    if isinstance(x, time):
        return x.hour + x.minute / 60
    try:
        parts = str(x).split(':')
        h, m = float(parts[0]), float(parts[1]) if len(parts) > 1 else 0
        return h + m / 60
    except:
        return np.nan


def preprocess_attendance(path: str):
    df = pd.read_excel(path)

    # Feature engineering - Basic time conversions
    df['avg_in_time_hr'] = df['Avg_In_Tim'].apply(to_hours)
    df['avg_office_hours'] = df['Avg_Office_hr'].apply(to_hours)
    df['avg_break_hours'] = df['Avg_Break_hr'].apply(to_hours)
    df['avg_ooo_hours'] = df['Avg_OOO_hr'].apply(to_hours)
    df['total_leaves'] = df['Half_Day'] + df['Full_Day']
    df['unbilled_flag'] = df['Unbilled'].astype(str).str.lower().eq('unbilled').astype(int)
    df['unallocated_flag'] = df['Unallocated'].astype(str).str.lower().eq('yes').astype(int)

    # Additional derived time columns for analysis
    df['bay_hours'] = df['Avg_Bay_hr'].apply(to_hours)     # ✅ renamed to match usage
    df['cafeteria_hours'] = df['Avg_Cafeteria'].apply(to_hours)

    # Calculate efficiency using Total Productive Time formula:
    # Efficiency (%) = bay_hours / Office_hours * 100
    df['efficiency'] = (
        df['bay_hours'].fillna(0) / df['avg_office_hours'].replace({0: np.nan})
    ) * 100
    df['efficiency'] = df['efficiency'].fillna(0)

    # Calculate break utilization: total break time vs office time
    df['break_utilization'] = (
        df['avg_break_hours'].fillna(0) / df['avg_office_hours'].replace({0: np.nan})
    )
    df['break_utilization'] = df['break_utilization'].fillna(0)

    # Calculate punctuality: deviation from 9 AM start time (assuming 9.0)
    df['punctuality'] = (df['avg_in_time_hr'] - 9.0).abs()

    # Calculate absenteeism days (weighted: full day = 1, half day = 0.5)
    df['absenteeism_days'] = df['Full_Day'].fillna(0) + 0.5 * df['Half_Day'].fillna(0)

    # Calculate burnout hours: office hours exceeding 9 hours
    df['burnout_hours'] = np.maximum(0, df['avg_office_hours'].fillna(0) - 9.0)

    # Selected numeric features for clustering
    features = [
        'avg_in_time_hr', 'avg_office_hours', 'avg_break_hours', 'avg_ooo_hours',
        'total_leaves', 'Online_Checkin', 'unbilled_flag', 'unallocated_flag',
        'efficiency', 'break_utilization', 'punctuality', 'burnout_hours'
    ]

    X = df[features].fillna(df[features].median())
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return df, X_scaled, scaler, features