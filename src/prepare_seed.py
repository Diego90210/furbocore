import pandas as pd
import json

pl = pd.read_csv('data/raw/tm_players.csv.gz', compression='gzip')
pl = pl[pl['current_club_domestic_competition_id'] == 'GB1'].copy()

pos_map = {'Defender': 'DF', 'Midfield': 'MF', 'Attack': 'FW', 'Goalkeeper': 'GK'}

rows = []
for _, r in pl.iterrows():
    name = str(r.get('name', '')).strip().replace("'", "''")
    team = str(r.get('current_club_name', '')).strip().replace("'", "''")
    pos = pos_map.get(str(r.get('position', '')).strip(), 'MF')
    tm_id = r['player_id']
    if not name or name == 'nan':
        continue
    rows.append((tm_id, name, team, pos))

print(f'{len(rows)} players to insert')
with open('data/seed_players.json', 'w') as f:
    json.dump(rows, f)

vals = pd.read_csv('data/raw/tm_player_valuations.csv.gz', compression='gzip')
vals['date'] = pd.to_datetime(vals['date'], errors='coerce')
latest = vals.sort_values('date').groupby('player_id').last().reset_index()

pl_ids = set(pl['player_id'].tolist())
val_rows = []
for _, v in latest.iterrows():
    if v['player_id'] not in pl_ids:
        continue
    val = v['market_value_in_eur']
    if pd.isna(val) or val == 0:
        continue
    val_rows.append((int(v['player_id']), float(val), str(v['date'])[:10] if pd.notna(v['date']) else None))

print(f'{len(val_rows)} valuations to insert')
with open('data/seed_vals.json', 'w') as f:
    json.dump(val_rows, f)
