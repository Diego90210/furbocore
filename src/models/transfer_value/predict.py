"""Predict transfer values for all players and upsert to Supabase.

Loads the most recent model, predicts on current player_stats,
calculates value_gap_pct, and writes to transfer_values.
"""
import os
import sys
from datetime import date
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
FEATURE_COLS = [
    "minutes_played",
    "goals_per90",
    "assists_per90",
    "age_at_season",
    "pos_DF",
    "pos_FW",
    "pos_GK",
    "pos_MF",
]


def find_latest_model():
    """Find the most recent .joblib model file."""
    models = sorted(MODELS_DIR.glob("transfer_value_*.joblib"), reverse=True)
    if not models:
        print("ERROR: No model files found")
        sys.exit(1)
    return models[0]


def get_current_stats(client):
    """Pull current player_stats with latest season per player + position."""
    stats_resp = client.table("player_stats").select("*").execute()
    df = pd.DataFrame(stats_resp.data)
    if df.empty:
        return df

    # Keep only latest season per player
    df = df.sort_values("season", ascending=False).drop_duplicates(subset=["player_id"], keep="first")

    # Get position from players table
    pl_resp = client.table("players").select("id,position").execute()
    pl_df = pd.DataFrame(pl_resp.data)
    df = df.merge(pl_df, left_on="player_id", right_on="id", how="left", suffixes=("", "_player"))
    return df


def prepare_features(stats_df):
    """Calculate per-90 stats and one-hot position for prediction."""
    df = stats_df.copy()
    df = df[df["minutes_played"] >= 270].copy()

    df["goals_per90"] = df["goals"] / (df["minutes_played"] / 90)
    df["assists_per90"] = df["assists"] / (df["minutes_played"] / 90)

    df["position"] = df["position"].fillna("MF")
    df["age_at_season"] = df["age_at_season"].fillna(25)
    pos_dummies = pd.get_dummies(df["position"], prefix="pos")
    df = pd.concat([df, pos_dummies], axis=1)

    for col in ["pos_DF", "pos_FW", "pos_GK", "pos_MF"]:
        if col not in df.columns:
            df[col] = 0

    X = df[FEATURE_COLS].fillna(0)
    return X, df


def predict_and_upsert():
    """Load model, predict, upsert to transfer_values."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY")
        sys.exit(1)

    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    model_path = find_latest_model()
    print(f"Loading model: {model_path.name}")
    model = joblib.load(model_path)

    model_version = model_path.stem.replace("transfer_value_", "")

    print("Fetching current stats...")
    stats_df = get_current_stats(client)
    if stats_df.empty:
        print("No stats available")
        return

    print(f"Preparing features for {len(stats_df)} players...")
    X, df = prepare_features(stats_df)
    if X.empty:
        print("No players with sufficient minutes")
        return

    print("Predicting...")
    y_pred_log = model.predict(X)
    y_pred_eur = np.expm1(y_pred_log)

    # Fetch existing real values in bulk
    print("Fetching existing real values...")
    tv_rows = []
    offset = 0
    while True:
        resp = client.table("transfer_values").select("player_id,real_value_eur").range(offset, offset + 999).execute()
        if not resp.data:
            break
        tv_rows.extend(resp.data)
        offset += 1000
    real_map = {r["player_id"]: r.get("real_value_eur") for r in tv_rows if r.get("real_value_eur")}

    # Build upsert rows
    rows = []
    for i, (_, row) in enumerate(df.iterrows()):
        predicted = float(y_pred_eur[i])
        real_value = real_map.get(row["player_id"])
        gap_pct = round((predicted - real_value) / real_value * 100, 2) if real_value and real_value > 0 else None
        rows.append({
            "player_id": row["player_id"],
            "predicted_value_eur": round(predicted, 2),
            "value_gap_pct": gap_pct,
            "model_version": model_version,
        })

    # Batch upsert
    BATCH = 200
    for i in range(0, len(rows), BATCH):
        client.table("transfer_values").upsert(rows[i:i+BATCH], on_conflict="player_id").execute()
        print(f"  Upserted {min(i+BATCH, len(rows))}/{len(rows)}")

    print(f"Upserted {len(rows)} predictions")


if __name__ == "__main__":
    predict_and_upsert()
