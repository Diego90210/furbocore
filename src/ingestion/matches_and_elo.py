"""Ingest match results + Elo ratings → matches table.

Uses soccerdata's MatchHistory (football-data.co.uk) and ClubElo.
"""
import os
import sys
import warnings
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

warnings.filterwarnings("ignore")

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

SEASONS = ["19-20", "20-21", "21-22", "22-23", "23-24", "24-25"]


def fetch_matches():
    """Fetch match results from football-data.co.uk via soccerdata."""
    import soccerdata as sd

    mh = sd.MatchHistory("ENG-Premier League", SEASONS)
    games = mh.read_games()
    print(f"Fetched {len(games)} matches")
    return games


def fetch_elo():
    """Fetch current Elo ratings from clubelo.com."""
    import soccerdata as sd

    elo = sd.ClubElo(current_competition="ENG-Premier League")
    try:
        current = elo.read_by_date()
        print(f"Fetched {len(current)} Elo ratings")
        return current
    except Exception as e:
        print(f"WARNING: Could not fetch Elo: {e}")
        return pd.DataFrame()


def flatten_multi_index(df):
    """Flatten multi-level column index."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join(col).strip("_") for col in df.columns.values]
    return df


def upsert_matches(client, games):
    """Upsert match data to Supabase."""
    df = flatten_multi_index(games.copy())
    df = df.reset_index()

    # Identify columns
    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    home_col = next((c for c in df.columns if "home" in c.lower() and "team" in c.lower()), None)
    away_col = next((c for c in df.columns if "away" in c.lower() and "team" in c.lower()), None)
    home_goals_col = next((c for c in df.columns if "home" in c.lower() and ("goal" in c.lower() or "score" in c.lower())), None)
    away_goals_col = next((c for c in df.columns if "away" in c.lower() and ("goal" in c.lower() or "score" in c.lower())), None)
    home_shots_col = next((c for c in df.columns if "home" in c.lower() and "shot" in c.lower()), None)
    away_shots_col = next((c for c in df.columns if "away" in c.lower() and "shot" in c.lower()), None)
    home_corners_col = next((c for c in df.columns if "home" in c.lower() and "corner" in c.lower()), None)
    away_corners_col = next((c for c in df.columns if "away" in c.lower() and "corner" in c.lower()), None)
    season_col = next((c for c in df.columns if "season" in c.lower()), None)

    upserted = 0
    for _, row in df.iterrows():
        match_date = str(row[date_col])[:10] if date_col and pd.notna(row.get(date_col)) else None
        home_team = str(row[home_col]).strip() if home_col and pd.notna(row.get(home_col)) else None
        away_team = str(row[away_col]).strip() if away_col and pd.notna(row.get(away_col)) else None

        if not match_date or not home_team or not away_team:
            continue

        # Determine status
        home_goals = _safe_int(row, [home_goals_col]) if home_goals_col else None
        away_goals = _safe_int(row, [away_goals_col]) if away_goals_col else None
        status = "played" if home_goals is not None and away_goals is not None else "scheduled"

        season = str(row.get(season_col, ""))[:7] if season_col and pd.notna(row.get(season_col)) else "2024-2025"

        match_row = {
            "league": "ENG-Premier League",
            "season": season,
            "match_date": match_date,
            "home_team": home_team,
            "away_team": away_team,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "home_shots": _safe_int(row, [home_shots_col]) if home_shots_col else None,
            "away_shots": _safe_int(row, [away_shots_col]) if away_shots_col else None,
            "home_corners": _safe_int(row, [home_corners_col]) if home_corners_col else None,
            "away_corners": _safe_int(row, [away_corners_col]) if away_corners_col else None,
            "status": status,
        }

        # Use unique constraint — upsert on (home_team, away_team, match_date)
        client.table("matches").upsert(match_row, on_conflict="home_team,away_team,match_date").execute()
        upserted += 1

    print(f"Upserted {upserted} matches")


def _safe_int(row, candidates):
    for col in candidates:
        if col and col in row.index and pd.notna(row[col]):
            try:
                return int(row[col])
            except (ValueError, TypeError):
                pass
    return None


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY env vars")
        sys.exit(1)

    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("Fetching matches...")
    games = fetch_matches()

    print("Upserting to Supabase...")
    upsert_matches(client, games)

    print("Fetching Elo (optional)...")
    try:
        elo = fetch_elo()
        if not elo.empty:
            print(f"  Elo data available: {len(elo)} teams")
    except Exception as e:
        print(f"WARNING: Could not fetch Elo: {e}")

    print("Done.")


if __name__ == "__main__":
    main()
