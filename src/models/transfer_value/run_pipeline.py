import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client
from sklearn.ensemble import RandomForestRegressor
import joblib

load_dotenv(Path.cwd() / ".env.local")
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY"); sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)
FEATURE_COLS = ["pos_DF", "pos_FW", "pos_GK", "pos_MF"]

print("Fetching players...")
p_rows = []
offset = 0
while True:
    resp = client.table("players").select("id,name,position").range(offset, offset + 999).execute()
    if not resp.data: break
    p_rows.extend(resp.data)
    offset += 1000
print(f"  {len(p_rows)} players")

print("Fetching transfer values...")
v_rows = []
offset = 0
while True:
    resp = client.table("transfer_values").select("player_id,real_value_eur").not_.is_("real_value_eur", "null").range(offset, offset + 999).execute()
    if not resp.data: break
    v_rows.extend(resp.data)
    offset += 1000
print(f"  {len(v_rows)} values")

pdf = pd.DataFrame(p_rows)
vdf = pd.DataFrame(v_rows)
merged = pdf.merge(vdf, left_on="id", right_on="player_id", how="inner").dropna(subset=["real_value_eur"])
merged = merged[merged["real_value_eur"] > 0].copy()
print(f"Merged: {len(merged)} rows")

# Features
merged["position"] = merged["position"].fillna("MF")
pos_dummies = pd.get_dummies(merged["position"], prefix="pos")
merged = pd.concat([merged, pos_dummies], axis=1)
for col in FEATURE_COLS:
    if col not in merged.columns: merged[col] = 0

y = np.log1p(merged["real_value_eur"].astype(float))
X = merged[FEATURE_COLS].fillna(0)

print("Training RandomForest...")
model = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
model.fit(X, y)
Path("models").mkdir(exist_ok=True)
joblib.dump(model, "models/transfer_value_model.pkl")
print("Model saved")

# Predict for ALL players
print("Predicting for all players...")
pdf["position"] = pdf["position"].fillna("MF")
pos_dummies = pd.get_dummies(pdf["position"], prefix="pos")
pdf = pd.concat([pdf, pos_dummies], axis=1)
for col in FEATURE_COLS:
    if col not in pdf.columns: pdf[col] = 0
X_pred = pdf[FEATURE_COLS].fillna(0)
pdf["predicted_value_eur"] = np.expm1(model.predict(X_pred)).round(0)

# Merge real values
pdf = pdf.merge(vdf, left_on="id", right_on="player_id", how="left")
mask = pdf["real_value_eur"].notna() & (pdf["real_value_eur"] > 0)
pdf["value_gap_pct"] = None
pdf.loc[mask, "value_gap_pct"] = ((pdf.loc[mask, "predicted_value_eur"] - pdf.loc[mask, "real_value_eur"]) / pdf.loc[mask, "real_value_eur"] * 100).round(1)

# Batch upsert
rows = []
for _, r in pdf.iterrows():
    rows.append({
        "player_id": r["id"],
        "predicted_value_eur": float(r["predicted_value_eur"]),
        "value_gap_pct": float(r["value_gap_pct"]) if pd.notna(r["value_gap_pct"]) else None,
    })

BATCH = 200
for i in range(0, len(rows), BATCH):
    client.table("transfer_values").upsert(rows[i:i+BATCH], on_conflict="player_id").execute()
    print(f"  Upserted {min(i+BATCH, len(rows))}/{len(rows)}")

print("Done.")
