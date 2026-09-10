"""Ingest player stats from FBref via soccerdata → players + player_stats tables."""
import os
import sys
import warnings
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

warnings.filterwarnings("ignore")

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")
# Also try env vars from GitHub Actions
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

SEASONS = ["2019-2020", "2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025"]

POSITION_MAP = {"Goalkeeper": "GK", "Defender": "DF", "Midfielder": "MF", "Forward": "FW"}


def fetch_fbref_data():
    import soccerdata as sd

    fbref = sd.FBref(leagues="ENG-Premier League", seasons=SEASONS)

    print("Fetching standard stats...")
    standard = fbref.read_player_season_stats(stat_type="standard")
    print("Fetching passing stats...")
    passing = fbref.read_player_season_stats(stat_type="passing")
    print("Fetching possession stats...")
    possession = fbref.read_player_season_stats(stat_type="possession")
    print("Fetching defense stats...")
    defense = fbref.read_player_season_stats(stat_type="defense")

    return standard, passing, possession, defense


def flatten_multi_index(df):
    """Flatten multi-level column index from soccerdata."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join(col).strip("_") for col in df.columns.values]
    return df


def build_players_and_stats(standard, passing, possession, defense):
    """Merge stat DataFrames and produce players + player_stats."""
    std = flatten_multi_index(standard.copy())
    pas = flatten_multi_index(passing.copy())
    poss = flatten_multi_index(possession.copy())
    defs = flatten_multi_index(defense.copy())

    # Find common index columns
    idx_cols = [c for c in std.index.names if c]

    # Flatten index for merge
    std = std.reset_index()
    pas = pas.reset_index()
    poss = poss.reset_index()
    defs = defs.reset_index()

    # Merge on player + season
    merge_keys = [c for c in std.columns if c.startswith("player") or c.startswith("season")]
    if not merge_keys:
        merge_keys = idx_cols[:2] if len(idx_cols) >= 2 else idx_cols

    merged = std.copy()

    # Select columns from each df to avoid duplicates
    for source, label in [(pas, "pass"), (poss, "poss"), (defs, "def")]:
        src_cols = [c for c in source.columns if c not in merged.columns or c in merge_keys]
        keep = [c for c in src_cols if any(k in c.lower() for k in ["total_", "per90_", "age"])]
        if not keep:
            keep = [c for c in src_cols if c not in merge_keys][:5]
        if keep:
            merged = merged.merge(source[merge_keys + keep], on=merge_keys, how="left", suffixes=("", f"_{label}"))

    return merged


def upsert_players_and_stats(client, merged_df):
    """Upsert players and player_stats to Supabase."""
    players_upserted = 0
    stats_upserted = 0

    # Determine column names (soccerdata uses varying column naming)
    name_col = next((c for c in merged_df.columns if "player" in c.lower() and "name" in c.lower()), None)
    if not name_col:
        name_col = next((c for c in merged_df.columns if "player" in c.lower()), merged_df.columns[0])

    team_col = next((c for c in merged_df.columns if "team" in c.lower() and "opp" not in c.lower()), None)
    pos_col = next((c for c in merged_df.columns if "position" in c.lower() or "pos" in c.lower()), None)
    age_col = next((c for c in merged_df.columns if "age" in c.lower()), None)
    season_col = next((c for c in merged_df.columns if "season" in c.lower()), None)

    if not name_col or not season_col:
        print(f"ERROR: Could not identify columns. Available: {list(merged_df.columns)}")
        return

    for _, row in merged_df.iterrows():
        name = str(row.get(name_col, "")).strip()
        if not name or name == "nan":
            continue

        team = str(row.get(team_col, "")).strip() if team_col else ""
        position = POSITION_MAP.get(str(row.get(pos_col, "")).strip(), "MF") if pos_col else "MF"
        season = str(row.get(season_col, "")).strip() if season_col else ""
        age = float(row[age_col]) if age_col and pd.notna(row.get(age_col)) else None

        # Upsert player
        player_resp = (
            client.table("players")
            .upsert(
                {
                    "fbref_id": f"{name}_{team}_{season}",
                    "name": name,
                    "team": team,
                    "position": position,
                    "league": "ENG-Premier League",
                },
                on_conflict="fbref_id",
            )
            .execute()
        )
        player_id = player_resp.data[0]["id"] if player_resp.data else None
        if not player_id:
            continue
        players_upserted += 1

        # Upsert stats
        minutes = _safe_int(row, ["minutes_played", "playing_time_minutes", "Min"])
        goals = _safe_int(row, ["goals", "performance_Gls", "Gls"])
        assists = _safe_int(row, ["assists", "performance_Ast", "Ast"])
        shots = _safe_int(row, ["shots", "standard_Sh", "Sh"])
        tacles = _safe_int(row, ["tackles_Tkl", "Tackles_Tkl", "tackles"])
        interceptions = _safe_int(row, ["tackles_Int", "Tackles_Int", "interceptions"])

        stats_row = {
            "player_id": player_id,
            "season": season,
            "team": team,
            "minutes_played": minutes,
            "goals": goals,
            "assists": assists,
            "shots": shots,
            "tackles": tacles,
            "interceptions": interceptions,
            "age_at_season": age,
        }
        client.table("player_stats").upsert(stats_row, on_conflict="player_id,season").execute()
        stats_upserted += 1

    print(f"Upserted {players_upserted} players, {stats_upserted} stat rows")


def _safe_int(row, candidates):
    """Try multiple column names and return first valid int."""
    for col in candidates:
        if col in row.index:
            val = row[col]
            if pd.notna(val):
                return int(val)
    return 0


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY env vars")
        sys.exit(1)

    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("Fetching data from FBref...")
    standard, passing, possession, defense = fetch_fbref_data()
    print(f"  standard: {standard.shape}, passing: {passing.shape}")

    print("Building merged dataset...")
    merged = build_players_and_stats(standard, passing, possession, defense)
    print(f"  Merged shape: {merged.shape}")

    print("Upserting to Supabase...")
    upsert_players_and_stats(client, merged)
    print("Done.")


if __name__ == "__main__":
    main()
