"""Assign cluster IDs and upsert to player_clusters.

Loads fitted models, predicts clusters, writes:
- cluster_id
- normalized_features (jsonb)
- feature_vector (vector(2)) for pgvector similarity search
"""
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

MODELS_DIR = Path(__file__).resolve().parent

FEATURE_NAMES = [
    "goals_per90",
    "assists_per90",
]


def find_latest_models():
    """Find latest model/scaler pairs per position group."""
    models = {}
    for group in ["GK", "DF", "MF", "FW"]:
        model_files = sorted(MODELS_DIR.glob(f"scouting_{group}_*.joblib"), reverse=True)
        scaler_files = sorted(MODELS_DIR.glob(f"scaler_{group}_*.joblib"), reverse=True)
        if model_files and scaler_files:
            models[group] = {
                "model": joblib.load(model_files[0]),
                "scaler": joblib.load(scaler_files[0]),
                "version": model_files[0].stem.split("_")[-1],
            }
    return models


def predict_and_upsert():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY")
        sys.exit(1)

    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    models = find_latest_models()
    if not models:
        print("ERROR: No trained models found")
        sys.exit(1)

    print(f"Loaded models for: {list(models.keys())}")

    # Pull player_stats + players
    stats_rows = []
    offset = 0
    while True:
        resp = client.table("player_stats").select("*").range(offset, offset + 999).execute()
        if not resp.data:
            break
        stats_rows.extend(resp.data)
        offset += 1000

    players_rows = []
    offset = 0
    while True:
        resp = client.table("players").select("id,position").range(offset, offset + 999).execute()
        if not resp.data:
            break
        players_rows.extend(resp.data)
        offset += 1000

    stats_df = pd.DataFrame(stats_rows)
    players_df = pd.DataFrame(players_rows)

    if stats_df.empty or players_df.empty:
        print("No data")
        return

    # Latest season per player
    stats_df = stats_df.sort_values("season", ascending=False).drop_duplicates(subset=["player_id"], keep="first")
    stats_df = stats_df[stats_df["minutes_played"] >= 270].copy()

    # Merge position
    merged = stats_df.merge(players_df, left_on="player_id", right_on="id", how="left")
    merged["position_group"] = merged["position"].map({"GK": "GK", "DF": "DF", "MF": "MF", "FW": "FW"})

    # Per-90
    for col in ["goals", "assists"]:
        merged[f"{col}_per90"] = merged[col] / (merged["minutes_played"] / 90)
    merged[FEATURE_NAMES] = merged[FEATURE_NAMES].fillna(0)

    # Predict per group
    upserted = 0
    BATCH = 200
    for group, model_info in models.items():
        group_df = merged[merged["position_group"] == group].copy()
        if group_df.empty:
            continue

        X_raw = group_df[FEATURE_NAMES].values
        X_scaled = model_info["scaler"].transform(X_raw)
        labels = model_info["model"].predict(X_scaled)

        rows = []
        for i, (_, row) in enumerate(group_df.iterrows()):
            vec = X_scaled[i].tolist()
            norm = {fn: round(float(v), 4) for fn, v in zip(FEATURE_NAMES, X_scaled[i])}
            rows.append({
                "player_id": row["player_id"],
                "season": row["season"],
                "position_group": group,
                "cluster_id": int(labels[i]),
                "normalized_features": norm,
                "feature_vector": vec,
                "model_version": model_info["version"],
            })

        for j in range(0, len(rows), BATCH):
            client.table("player_clusters").upsert(
                rows[j:j+BATCH], on_conflict="player_id,season"
            ).execute()
        upserted += len(rows)
        print(f"  {group}: {len(group_df)} players clustered")

    print(f"Upserted {upserted} cluster assignments")


if __name__ == "__main__":
    predict_and_upsert()
