"""Seed Supabase from Transfermarkt CSV cache.

Reads data/raw/tm_players.csv.gz + tm_player_valuations.csv.gz,
filters to PL players, upserts into players + transfer_values tables.
Run with: python src/seed_transfermarkt.py
"""
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
POSITION_MAP = {"Defender": "DF", "Midfield": "MF", "Attack": "FW", "Goalkeeper": "GK"}


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY")
        sys.exit(1)

    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Load CSVs
    players_path = RAW_DIR / "tm_players.csv.gz"
    vals_path = RAW_DIR / "tm_player_valuations.csv.gz"
    if not players_path.exists() or not vals_path.exists():
        print(f"ERROR: Missing CSV files in {RAW_DIR}")
        sys.exit(1)

    tm_players = pd.read_csv(players_path, compression="gzip")
    tm_vals = pd.read_csv(vals_path, compression="gzip")
    print(f"Loaded {len(tm_players)} players, {len(tm_vals)} valuations")

    # Filter to Premier League
    pl = tm_players[tm_players["current_club_domestic_competition_id"] == "GB1"].copy()
    print(f"PL players: {len(pl)}")

    # Get latest valuation per player
    tm_vals["date"] = pd.to_datetime(tm_vals["date"], errors="coerce")
    latest = tm_vals.sort_values("date").groupby("player_id").last().reset_index()

    # Upsert players
    upserted = 0
    skipped = 0
    player_id_map = {}  # tm_player_id -> supabase_player_id

    for _, row in pl.iterrows():
        tm_id = row["player_id"]
        name = str(row.get("name", "")).strip()
        team = str(row.get("current_club_name", "")).strip()
        position = POSITION_MAP.get(str(row.get("position", "")).strip(), "MF")

        if not name or name == "nan":
            skipped += 1
            continue

        resp = (
            client.table("players")
            .upsert(
                {
                    "fbref_id": f"tm_{tm_id}",
                    "name": name,
                    "team": team,
                    "position": position,
                    "league": "ENG-Premier League",
                },
                on_conflict="fbref_id",
            )
            .execute()
        )
        if resp.data:
            player_id_map[tm_id] = resp.data[0]["id"]
            upserted += 1

    print(f"Upserted {upserted} players, skipped {skipped}")

    # Upsert transfer_values (latest valuation per player)
    tv_upserted = 0
    for tm_id, supabase_id in player_id_map.items():
        val_row = latest[latest["player_id"] == tm_id]
        if val_row.empty:
            continue

        value = val_row["market_value_in_eur"].iloc[0]
        val_date = str(val_row["date"].iloc[0])[:10] if pd.notna(val_row["date"].iloc[0]) else None

        if pd.isna(value) or value == 0:
            continue

        client.table("transfer_values").upsert(
            {
                "player_id": supabase_id,
                "real_value_eur": float(value),
                "real_value_date": val_date,
            },
            on_conflict="player_id",
        ).execute()
        tv_upserted += 1

    print(f"Upserted {tv_upserted} transfer values")
    print("Done.")


if __name__ == "__main__":
    main()
