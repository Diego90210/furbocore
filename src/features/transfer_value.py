"""Feature engineering for transfer value prediction.

Builds training set from player_stats + transfer_values in Supabase.
Target: log1p(real_value_eur). Features: per-90 stats, age, position.
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


def build_training_set():
    """Pull data from Supabase and return (X, y, meta) for model training."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Pull stats
    stats_rows = []
    offset = 0
    while True:
        resp = client.table("player_stats").select("*").range(offset, offset + 999).execute()
        if not resp.data:
            break
        stats_rows.extend(resp.data)
        offset += 1000
    stats_df = pd.DataFrame(stats_rows)

    # Pull transfer values (only players with real values)
    val_rows = []
    offset = 0
    while True:
        resp = (
            client.table("transfer_values")
            .select("player_id,real_value_eur,real_value_date")
            .not_.is_("real_value_eur", "null")
            .range(offset, offset + 999)
            .execute()
        )
        if not resp.data:
            break
        val_rows.extend(resp.data)
        offset += 1000
    val_df = pd.DataFrame(val_rows)

    if stats_df.empty or val_df.empty:
        print(f"WARNING: stats={len(stats_df)} rows, vals={len(val_df)} rows — no training data")
        return None, None, None

    # Pull players for position
    pl_rows = []
    offset = 0
    while True:
        resp = client.table("players").select("id,position").range(offset, offset + 999).execute()
        if not resp.data:
            break
        pl_rows.extend(resp.data)
        offset += 1000
    pl_df = pd.DataFrame(pl_rows)

    # Merge: start from transfer_values (all with real values), left join stats + position
    merged = val_df.merge(pl_df, left_on="player_id", right_on="id", how="left", suffixes=("", "_player"))
    merged = merged.merge(stats_df, on="player_id", how="left", suffixes=("", "_stat"))
    print(f"Merged: {len(merged)} rows with real_value_eur")

    # Fill missing stats with 0 for players without player_stats
    for col in ["minutes_played", "goals", "assists", "age_at_season"]:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)
        else:
            merged[col] = 0

    # Per-90 stats (0 for players without minutes)
    merged["goals_per90"] = merged.apply(
        lambda r: r["goals"] / (r["minutes_played"] / 90) if r["minutes_played"] > 0 else 0, axis=1
    )
    merged["assists_per90"] = merged.apply(
        lambda r: r["assists"] / (r["minutes_played"] / 90) if r["minutes_played"] > 0 else 0, axis=1
    )

    # One-hot position
    merged["position"] = merged["position"].fillna("MF")
    pos_dummies = pd.get_dummies(merged["position"], prefix="pos")
    merged = pd.concat([merged, pos_dummies], axis=1)

    # Ensure all pos columns exist
    for col in ["pos_DF", "pos_FW", "pos_GK", "pos_MF"]:
        if col not in merged.columns:
            merged[col] = 0

    # Drop rows with NaN target
    merged = merged.dropna(subset=["real_value_eur"])

    # Target: log1p
    y = np.log1p(merged["real_value_eur"].astype(float))

    # Meta for reference
    meta_cols = ["player_id", "real_value_eur"]
    if "season" in merged.columns:
        meta_cols.insert(1, "season")
    meta = merged[meta_cols].copy()

    # Features
    X = merged[FEATURE_COLS].fillna(0)

    print(f"Training set: {X.shape[0]} rows, {X.shape[1]} features")
    return X, y, meta


if __name__ == "__main__":
    X, y, meta = build_training_set()
    if X is not None:
        print(f"\nFeature columns: {list(X.columns)}")
        print(f"Target range: €{np.expm1(y.min()):,.0f} — €{np.expm1(y.max()):,.0f}")
        print(f"\nSample:\n{X.head()}")
