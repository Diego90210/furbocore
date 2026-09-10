import json
from pathlib import Path

# Generate SQL for players
with open('data/seed_players.json') as f:
    players = json.load(f)

# Build INSERT with ON CONFLICT DO UPDATE
chunks = []
for i in range(0, len(players), 200):
    batch = players[i:i+200]
    values = ", ".join(
        f"(gen_random_uuid(), 'tm_{tm_id}', '{name}', '{team}', '{pos}', 'ENG-Premier League')"
        for tm_id, name, team, pos in batch
    )
    sql = f"""INSERT INTO players (id, fbref_id, name, team, position, league)
VALUES {values}
ON CONFLICT (fbref_id) DO UPDATE SET name=EXCLUDED.name, team=EXCLUDED.team, position=EXCLUDED.position;"""
    chunks.append(sql)

Path('data/seed_players.sql').write_text('\n'.join(f"-- chunk {i}\n{c}" for i, c in enumerate(chunks)))
print(f"Generated {len(chunks)} SQL chunks for players")

# Generate SQL for valuations
with open('data/seed_vals.json') as f:
    vals = json.load(f)

val_chunks = []
for i in range(0, len(vals), 200):
    batch = vals[i:i+200]
    lines = []
    for tm_id, value, date in batch:
        date_expr = f"'{date}'" if date else "NULL"
        lines.append(f"(p.id, {value}, {date_expr})")
    values = ", ".join(lines)
    sql = f"""INSERT INTO transfer_values (player_id, real_value_eur, real_value_date)
SELECT p.id, v.val, v.dt FROM (VALUES {values}) AS v(player_fbref, val, dt)
JOIN players p ON p.fbref_id = 'tm_' || v.player_fbref
ON CONFLICT (player_id) DO UPDATE SET real_value_eur=EXCLUDED.real_value_eur, real_value_date=EXCLUDED.real_value_date;"""
    val_chunks.append(sql)

Path('data/seed_vals.sql').write_text('\n'.join(f"-- chunk {i}\n{c}" for i, c in enumerate(val_chunks)))
print(f"Generated {len(val_chunks)} SQL chunks for valuations")
