# train_model.py
from src.data_preprocessing import preprocess_attendance
from src.clustering_model import run_clustering
import joblib

print("🔧 Preprocessing data...")
df, X_scaled, scaler, features = preprocess_attendance("Cleaned_Attendance_Data.xlsx")
print("✅ Done preprocessing.")

print("🚀 Running clustering...")
df, model = run_clustering(df, X_scaled, k=4, scaler=scaler, save=True)
print("✅ All done! Files saved in /data and /models")
