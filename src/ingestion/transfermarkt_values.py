"""Ingest Transfermarkt market values → transfer_values table.

Dataset: dcaribou/transfermarkt-datasets (CSV or DuckDB).
Treat as static snapshot — updates paused since Jul 2026.
"""
import os
import sys
from pathlib import Path
from io import BytesIO

import httpx
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

R2_BASE = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data"
TRANSFERMARKT_URL = f"{R2_BASE}/players.csv.gz"
VALUATIONS_URL = f"{R2_BASE}/player_valuations.csv.gz"

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def download_snapshot():
    """Download Transfermarkt CSVs (idempotent — skips if already cached)."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    players_path = RAW_DIR / "tm_players.csv.gz"
    vals_path = RAW_DIR / "tm_player_valuations.csv.gz"

    client = httpx.Client(
        headers={"User-Agent": "Mozilla/5.0"},
        follow_redirects=True,
        timeout=60,
    )

    if not players_path.exists():
        print("Downloading players.csv.gz...")
        r = client.get(TRANSFERMARKT_URL)
        r.raise_for_status()
        players_path.write_bytes(r.content)
    else:
        print("Using cached players snapshot")

    if not vals_path.exists():
        print("Downloading player_valuations.csv.gz...")
        r = client.get(VALUATIONS_URL)
        r.raise_for_status()
        vals_path.write_bytes(r.content)
    else:
        print("Using cached valuations snapshot")

    client.close()
    return players_path, vals_path


def load_data(players_path, vals_path):
    players = pd.read_csv(players_path, compression="gzip")
    valuations = pd.read_csv(vals_path, compression="gzip")
    print(f"Loaded {len(players)} players, {len(valuations)} valuations")
    return players, valuations


def fuzzy_match_name(fbref_name, tm_names):
    """Simple fuzzy match: lowercase + strip accents."""
    from unidecode import unidecode

    normalized = unidecode(str(fbref_name)).lower().strip()
    for tm_name in tm_names:
        if unidecode(str(tm_name)).lower().strip() == normalized:
            return tm_name
    return None


def build_transfer_values(players_df, valuations_df):
    """Get latest market value per player from Transfermarkt data."""
    # Filter to Premier League / ENG1
    league_col = next((c for c in players_df.columns if "league" in c.lower()), None)
    if league_col:
        pl_players = players_df[
            players_df[league_col].astype(str).str.contains("GB1|ENG", case=False, na=False)
        ].copy()
    else:
        pl_players = players_df.copy()

    # Get latest valuation per player
    val_col = next((c for c in valuations_df.columns if "market_value" in c.lower()), None)
    date_col = next((c for c in valuations_df.columns if "date" in c.lower()), None)
    pid_col = next((c for c in valuations_df.columns if "player" in c.lower() and "id" in c.lower()), None)

    if not all([val_col, date_col, pid_col]):
        print(f"WARNING: Could not identify columns in valuations. Columns: {list(valuations_df.columns)}")
        return pd.DataFrame()

    valuations_df[date_col] = pd.to_datetime(valuations_df[date_col], errors="coerce")
    latest = valuations_df.sort_values(date_col).groupby(pid_col).last().reset_index()

    return pl_players, latest, val_col, pid_col


def upsert_transfer_values(client, pl_players, latest_vals, val_col, pid_col):
    """Match FBref players to Transfermarkt values and upsert."""
    # Get existing players from Supabase
    resp = client.table("players").select("id, name, team").execute()
    existing = {r["name"]: r for r in resp.data}

    # Get Transfermarkt player names
    tm_name_col = next((c for c in pl_players.columns if "name" in c.lower() or "player_name" in c.lower()), None)
    tm_id_col = next((c for c in pl_players.columns if "player" in c.lower() and "id" in c.lower()), None)

    if not tm_name_col:
        print(f"WARNING: No name column in Transfermarkt. Columns: {list(pl_players.columns)}")
        return

    matched = 0
    unmatched = 0

    for tm_row in pl_players.itertuples():
        tm_name = str(getattr(tm_row, tm_name_col, "")).strip()
        if not tm_name:
            continue

        # Find matching FBref player
        fbref_player = None
        for fbref_name, fbref_data in existing.items():
            if fuzzy_match_name(fbref_name, [tm_name]):
                fbref_player = fbref_data
                break

        if not fbref_player:
            unmatched += 1
            continue

        # Get latest valuation
        tm_player_id = getattr(tm_row, tm_id_col, None) if tm_id_col else None
        val_row = latest_vals[latest_vals[pid_col] == tm_player_id] if tm_player_id else pd.DataFrame()

        if val_row.empty:
            continue

        real_value = float(val_row[val_col].iloc[0]) if pd.notna(val_row[val_col].iloc[0]) else None
        val_date = str(val_row["date"].iloc[0]) if "date" in val_row.columns else None

        client.table("transfer_values").upsert(
            {
                "player_id": fbref_player["id"],
                "real_value_eur": real_value,
                "real_value_date": val_date,
            },
            on_conflict="player_id",
        ).execute()
        matched += 1

    print(f"Matched {matched} players, {unmatched} unmatched")


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY env vars")
        sys.exit(1)

    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    players_path, vals_path = download_snapshot()
    players_df, valuations_df = load_data(players_path, vals_path)

    result = build_transfer_values(players_df, valuations_df)
    if isinstance(result, tuple):
        pl_players, latest_vals, val_col, pid_col = result
        upsert_transfer_values(client, pl_players, latest_vals, val_col, pid_col)
    else:
        print("No data to process")

    print("Done.")


if __name__ == "__main__":
    main()
