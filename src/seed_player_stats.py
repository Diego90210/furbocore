import os, sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path.cwd() / ".env.local")
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

import kagglehub
path = kagglehub.dataset_download("davidcariboo/player-scores")

print("Loading appearances...")
app = pd.read_csv(os.path.join(path, "appearances.csv"), low_memory=False)
pl = app[app["competition_id"] == "GB1"].copy()
print(f"PL appearances: {len(pl)}")

pl["date"] = pd.to_datetime(pl["date"], errors="coerce")
pl["year"] = pl["date"].dt.year
pl["month"] = pl["date"].dt.month
pl["season"] = pl.apply(
    lambda r: f"{r['year']}-{r['year']+1}" if r["month"] >= 7 else f"{r['year']-1}-{r['year']}",
    axis=1,
)

agg = (
    pl.groupby(["player_id", "player_name", "season"])
    .agg(goals=("goals", "sum"), assists=("assists", "sum"), minutes_played=("minutes_played", "sum"))
    .reset_index()
)
print(f"Player-season rows: {len(agg)}")

# Get kaggle player IDs -> supabase IDs
client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("Fetching kaggle players from DB...")
k_players = []
offset = 0
while True:
    resp = client.table("players").select("id,fbref_id").like("fbref_id", "kaggle_%").range(offset, offset + 999).execute()
    if not resp.data: break
    k_players.extend(resp.data)
    offset += 1000

id_map = {}
for p in k_players:
    k_id = int(p["fbref_id"].replace("kaggle_", ""))
    id_map[k_id] = p["id"]
print(f"Mapped {len(id_map)} players")

# Build stats rows
stats_rows = []
for _, row in agg.iterrows():
    pid = row["player_id"]
    if pid not in id_map:
        continue
    stats_rows.append({
        "player_id": id_map[pid],
        "season": row["season"],
        "team": "",
        "minutes_played": int(row["minutes_played"]),
        "goals": int(row["goals"]),
        "assists": int(row["assists"]),
        "shots": 0,
        "tackles": 0,
        "interceptions": 0,
        "age_at_season": None,
    })

print(f"Stats to upsert: {len(stats_rows)}")
BATCH = 200
for i in range(0, len(stats_rows), BATCH):
    client.table("player_stats").upsert(stats_rows[i:i+BATCH], on_conflict="player_id,season").execute()
    print(f"  {min(i+BATCH, len(stats_rows))}/{len(stats_rows)}")

print("Done.")
