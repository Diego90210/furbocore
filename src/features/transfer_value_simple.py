"""Simplified feature engineering for transfer value.

Uses only Transfermarkt data (players + transfer_values) — no FBref dependency.
Features: position one-hot, age. Target: log1p(real_value_eur).
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

FEATURE_COLS = ["pos_DF", "pos_FW", "pos_GK", "pos_MF"]


def build_training_set():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Pull players
    players_rows = []
    offset = 0
    while True:
        resp = client.table("players").select("id,name,position").range(offset, offset + 999).execute()
        if not resp.data:
            break
        players_rows.extend(resp.data)
        offset += 1000

    # Pull transfer values
    val_rows = []
    offset = 0
    while True:
        resp = (
            client.table("transfer_values")
            .select("player_id,real_value_eur")
            .not_.is_("real_value_eur", "null")
            .range(offset, offset + 999)
            .execute()
        )
        if not resp.data:
            break
        val_rows.extend(resp.data)
        offset += 1000

    players_df = pd.DataFrame(players_rows)
    val_df = pd.DataFrame(val_rows)
    print(f"Players: {len(players_df)}, Transfer values: {len(val_df)}")

    if players_df.empty or val_df.empty:
        print("WARNING: no data available")
        return None, None, None

    merged = players_df.merge(val_df, left_on="id", right_on="player_id", how="inner")
    merged = merged.dropna(subset=["real_value_eur"])
    merged = merged[merged["real_value_eur"] > 0].copy()
    print(f"Merged: {len(merged)} rows with real_value_eur")

    # One-hot position
    merged["position"] = merged["position"].fillna("MF")
    pos_dummies = pd.get_dummies(merged["position"], prefix="pos")
    merged = pd.concat([merged, pos_dummies], axis=1)

    for col in FEATURE_COLS:
        if col not in merged.columns:
            merged[col] = 0

    y = np.log1p(merged["real_value_eur"].astype(float))
    meta = merged[["player_id", "name", "real_value_eur"]].copy()
    X = merged[FEATURE_COLS].fillna(0)

    print(f"Training set: {X.shape[0]} rows, {X.shape[1]} features")
    return X, y, meta


if __name__ == "__main__":
    X, y, meta = build_training_set()
    if X is not None:
        print(f"Target range: EUR {np.expm1(y.min()):,.0f} - EUR {np.expm1(y.max()):,.0f}")
        print(f"\nSample:\n{X.head()}")
