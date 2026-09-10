"""Feature engineering for scouting / clustering.

Normalizes per-90 stats, separates by position_group (GK/DF/MF/FW),
scales with StandardScaler (one per group).
Output: dict of {position_group: DataFrame_escalado} + list of feature names.
"""
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sklearn.preprocessing import StandardScaler
from supabase import create_client

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

FEATURE_NAMES = [
    "goals_per90",
    "assists_per90",
    "shots_per90",
    "tackles_per90",
    "interceptions_per90",
]

POSITION_MAP = {"GK": "GK", "DF": "DF", "MF": "MF", "FW": "FW"}


def get_player_stats(client):
    """Pull player_stats with player info for position."""
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
        return pd.DataFrame()

    # Merge position
    merged = stats_df.merge(players_df, left_on="player_id", right_on="id", how="left")
    return merged


def build_scouting_features():
    """Build normalized, scaled features per position group.

    Returns: (scaled_dfs, feature_names, scalers)
      scaled_dfs: {position_group: DataFrame with player_id, season, feature_vector, normalized_features}
      feature_names: list of feature column names
      scalers: {position_group: fitted StandardScaler}
    """
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("Fetching player stats...")
    df = get_player_stats(client)
    if df.empty:
        print("No data available")
        return None, None, None

    # Keep latest season per player
    df = df.sort_values("season", ascending=False).drop_duplicates(subset=["player_id"], keep="first")

    # Minimum minutes
    df = df[df["minutes_played"] >= 270].copy()

    # Map position
    df["position_group"] = df["position"].map(POSITION_MAP)
    df = df.dropna(subset=["position_group"])

    # Per-90
    for col in ["goals", "assists", "shots", "tackles", "interceptions"]:
        per90 = f"{col}_per90"
        df[per90] = df[col] / (df["minutes_played"] / 90)

    # Fill NaN
    df[FEATURE_NAMES] = df[FEATURE_NAMES].fillna(0)

    # Scale per position group
    scaled_dfs = {}
    scalers = {}

    for group in ["GK", "DF", "MF", "FW"]:
        group_df = df[df["position_group"] == group].copy()
        if group_df.empty:
            continue

        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(group_df[FEATURE_NAMES])

        group_df["feature_vector"] = [row.tolist() for row in features_scaled]
        group_df["normalized_features"] = [
            {fn: round(float(v), 4) for fn, v in zip(FEATURE_NAMES, row)}
            for row in features_scaled
        ]

        scaled_dfs[group] = group_df[["player_id", "season", "position_group", "feature_vector", "normalized_features"]].copy()
        scalers[group] = scaler
        print(f"  {group}: {len(group_df)} players")

    print(f"Total: {sum(len(v) for v in scaled_dfs.values())} players across {len(scaled_dfs)} groups")
    return scaled_dfs, FEATURE_NAMES, scalers


if __name__ == "__main__":
    scaled_dfs, features, _ = build_scouting_features()
    if scaled_dfs:
        print(f"\nFeatures: {features}")
        for g, df in scaled_dfs.items():
            print(f"\n{g} sample:")
            print(df.head(2).to_string())
