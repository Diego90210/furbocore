"""Ingest player stats from Kaggle dataset → players + player_stats tables.

Dataset: davidcariboo/player-scores (appearances.csv)
Covers multiple seasons of top leagues. Filter to GB1 (Premier League).
"""
import os
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

KAGGLE_DATASET = "davidcariboo/player-scores"
BATCH = 200

POSITION_MAP = {
    "Goalkeeper": "GK",
    "Defender": "DF",
    "Midfield": "MF",
    "Attack": "FW",
}

SUBPOSITION_MAP = {
    "Centre-Back": "DF",
    "Left-Back": "DF",
    "Right-Back": "DF",
    "Defensive Midfield": "MF",
    "Central Midfield": "MF",
    "Left Midfield": "MF",
    "Right Midfield": "MF",
    "Attacking Midfield": "MF",
    "Left Winger": "FW",
    "Right Winger": "FW",
    "Centre-Forward": "FW",
    "Second Striker": "FW",
}


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY"); sys.exit(1)

    import kagglehub
    path = kagglehub.dataset_download(KAGGLE_DATASET)
    print(f"Dataset at: {path}")

    # Load appearances
    print("Loading appearances.csv...")
    app = pd.read_csv(os.path.join(path, "appearances.csv"), low_memory=False)
    print(f"  Total rows: {len(app)}")

    # Filter to Premier League
    pl = app[app["competition_id"] == "GB1"].copy()
    print(f"  PL appearances: {len(pl)}")

    # Derive season from date
    pl["date"] = pd.to_datetime(pl["date"], errors="coerce")
    pl["year"] = pl["date"].dt.year
    pl["month"] = pl["date"].dt.month
    pl["season"] = pl.apply(
        lambda r: f"{r['year']}-{r['year']+1}" if r["month"] >= 7 else f"{r['year']-1}-{r['year']}",
        axis=1,
    )

    # Load players for position + birth_date
    print("Loading players.csv...")
    players_df = pd.read_csv(os.path.join(path, "players.csv"), low_memory=False)

    pos_map = {}
    birth_map = {}
    for _, p in players_df.iterrows():
        pid = p["player_id"]
        # Prefer sub_position for more specific mapping
        sub = str(p.get("sub_position", "")).strip()
        pos = str(p.get("position", "")).strip()
        pos_map[pid] = SUBPOSITION_MAP.get(sub, POSITION_MAP.get(pos, "MF"))

        dob = p.get("date_of_birth")
        if pd.notna(dob):
            try:
                birth_map[pid] = datetime.strptime(str(dob)[:10], "%Y-%m-%d").year
            except (ValueError, TypeError):
                pass

    # Aggregate per player per season
    print("Aggregating stats per player/season...")
    agg = (
        pl.groupby(["player_id", "player_name", "season"])
        .agg(
            goals=("goals", "sum"),
            assists=("assists", "sum"),
            minutes_played=("minutes_played", "sum"),
            yellow_cards=("yellow_cards", "sum"),
            red_cards=("red_cards", "sum"),
            games=("appearance_id", "count"),
        )
        .reset_index()
    )
    print(f"  {len(agg)} player-season rows")

    # Compute age_at_season
    def compute_age(row):
        pid = row["player_id"]
        if pid not in birth_map:
            return None
        season_end = int(row["season"].split("-")[1])
        return season_end - birth_map[pid]

    agg["age_at_season"] = agg.apply(compute_age, axis=1)

    # Upsert players — reuse existing rows by name to avoid duplicates
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("Loading existing players...")
    existing = {}
    offset = 0
    while True:
        resp = client.table("players").select("id,name").range(offset, offset + 999).execute()
        if not resp.data:
            break
        for r in resp.data:
            existing[r["name"]] = r["id"]
        offset += 1000
    print(f"  {len(existing)} existing players")

    print("Upserting players...")
    player_ids = {}
    for pid in agg["player_id"].unique():
        name = agg.loc[agg["player_id"] == pid, "player_name"].iloc[0]
        pos = pos_map.get(pid, "MF")
        name = str(name)

        if name in existing:
            player_ids[pid] = existing[name]
            continue

        resp = (
            client.table("players")
            .insert(
                {
                    "fbref_id": f"kaggle_{pid}",
                    "name": name,
                    "team": "Premier League",
                    "position": pos,
                    "league": "ENG-Premier League",
                }
            )
            .execute()
        )
        if resp.data:
            player_ids[pid] = resp.data[0]["id"]
            existing[name] = resp.data[0]["id"]

    print(f"  Mapped {len(player_ids)} players")

    # Upsert player_stats in batches
    print("Upserting player_stats...")
    stats_rows = []
    for _, row in agg.iterrows():
        pid = row["player_id"]
        if pid not in player_ids:
            continue
        stats_rows.append({
            "player_id": player_ids[pid],
            "season": row["season"],
            "team": "",
            "minutes_played": int(row["minutes_played"]),
            "goals": int(row["goals"]),
            "assists": int(row["assists"]),
            "shots": 0,
            "tackles": 0,
            "interceptions": 0,
            "age_at_season": int(row["age_at_season"]) if pd.notna(row["age_at_season"]) else None,
        })

    for i in range(0, len(stats_rows), BATCH):
        client.table("player_stats").upsert(
            stats_rows[i:i+BATCH], on_conflict="player_id,season"
        ).execute()
        print(f"  {min(i+BATCH, len(stats_rows))}/{len(stats_rows)}")

    print("Done.")


if __name__ == "__main__":
    main()
