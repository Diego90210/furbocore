import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
POSITION_MAP = {"Defender": "DF", "Midfield": "MF", "Attack": "FW", "Goalkeeper": "GK"}

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load and filter PL players
tm_players = pd.read_csv(RAW_DIR / "tm_players.csv.gz", compression="gzip")
pl = tm_players[tm_players["current_club_domestic_competition_id"] == "GB1"].copy()
print(f"PL players: {len(pl)}")

# Load latest valuations
tm_vals = pd.read_csv(RAW_DIR / "tm_player_valuations.csv.gz", compression="gzip")
tm_vals["date"] = pd.to_datetime(tm_vals["date"], errors="coerce")
latest = tm_vals.sort_values("date").groupby("player_id").last().reset_index()

# Upsert players in batches of 100
BATCH = 100
rows = []
for _, r in pl.iterrows():
    name = str(r.get("name", "")).strip()
    team = str(r.get("current_club_name", "")).strip()
    pos = POSITION_MAP.get(str(r.get("position", "")).strip(), "MF")
    tm_id = r["player_id"]
    if not name or name == "nan":
        continue
    rows.append({
        "fbref_id": f"tm_{tm_id}",
        "name": name,
        "team": team,
        "position": pos,
        "league": "ENG-Premier League",
    })

for i in range(0, len(rows), BATCH):
    batch = rows[i:i+BATCH]
    resp = client.table("players").upsert(batch, on_conflict="fbref_id").execute()
    print(f"  Players {i+len(batch)}/{len(rows)}")

# Now fetch all players to build tm_id -> supabase_id mapping
all_players = client.table("players").select("id, fbref_id").execute()
id_map = {}
for p in all_players.data:
    fbref = p["fbref_id"]
    if fbref.startswith("tm_"):
        tm_id = int(fbref[3:])
        id_map[tm_id] = p["id"]

print(f"Mapped {len(id_map)} players")

# Upsert transfer values in batches
pl_ids = set(pl["player_id"].tolist())
val_rows = []
for _, v in latest.iterrows():
    pid = v["player_id"]
    if pid not in pl_ids or pid not in id_map:
        continue
    val = v["market_value_in_eur"]
    if pd.isna(val) or val == 0:
        continue
    val_rows.append({
        "player_id": id_map[pid],
        "real_value_eur": float(val),
        "real_value_date": str(v["date"])[:10] if pd.notna(v["date"]) else None,
    })

print(f"Transfer values to upsert: {len(val_rows)}")
for i in range(0, len(val_rows), BATCH):
    batch = val_rows[i:i+BATCH]
    client.table("transfer_values").upsert(batch, on_conflict="player_id").execute()
    print(f"  Values {i+len(batch)}/{len(val_rows)}")

print("Done.")
