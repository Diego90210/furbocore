"""Ingest matches from football-data.org API → matches table.

Batch upserts for speed. Free tier: 2 seasons + scheduled.
"""
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
FDORG_TOKEN = os.getenv("FOOTBALL_DATA_ORG_TOKEN")

BASE_URL = "https://api.football-data.org/v4/competitions/PL/matches"
SEASONS = [2024, 2023]
BATCH = 200


def fetch_matches(status=None, season=None):
    headers = {"X-Auth-Token": FDORG_TOKEN}
    params = {"limit": 500}
    if status:
        params["status"] = status
    if season:
        params["season"] = season
    r = httpx.get(BASE_URL, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("matches", [])


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY"); sys.exit(1)
    if not FDORG_TOKEN:
        print("ERROR: Set FOOTBALL_DATA_ORG_TOKEN"); sys.exit(1)

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    all_rows = []

    for season in SEASONS:
        print(f"Fetching season {season}...")
        matches = fetch_matches(status="FINISHED", season=season)
        print(f"  {len(matches)} finished")
        for m in matches:
            all_rows.append(_to_row(m))

    print("Fetching scheduled...")
    matches = fetch_matches(status="SCHEDULED")
    print(f"  {len(matches)} scheduled")
    for m in matches:
        all_rows.append(_to_row(m))

    print(f"Total: {len(all_rows)} matches. Upserting...")
    for i in range(0, len(all_rows), BATCH):
        client.table("matches").upsert(
            all_rows[i:i+BATCH], on_conflict="home_team,away_team,match_date"
        ).execute()
        print(f"  {min(i+BATCH, len(all_rows))}/{len(all_rows)}")

    print("Done.")


def _to_row(m):
    home_team = m["homeTeam"]["name"]
    away_team = m["awayTeam"]["name"]
    match_date = m["utcDate"][:10]
    home_goals = m["score"]["fullTime"]["home"]
    away_goals = m["score"]["fullTime"]["away"]

    status = m.get("status", "")
    db_status = "played" if status == "FINISHED" else (
        "scheduled" if status in ("SCHEDULED", "TIMED") else status.lower()
    )

    year = int(match_date[:4])
    month = int(match_date[5:7])
    season = f"{year}-{year+1}" if month >= 7 else f"{year-1}-{year}"

    return {
        "league": "ENG-Premier League",
        "season": season,
        "match_date": match_date,
        "home_team": home_team,
        "away_team": away_team,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "status": db_status,
    }


if __name__ == "__main__":
    main()
