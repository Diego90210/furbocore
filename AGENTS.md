# Football Analytics Platform

Premier League analytics app: transfer values, match predictions, scouting (player similarity via pgvector).

## Stack

- **Frontend:** Next.js 16 App Router + Tailwind CSS 4 + TypeScript — `app/` directory
- **Database:** Supabase (Postgres 17 + pgvector + pg_trgm + pgcrypto) — project `kswtdayhvzzhrbdwzgqb`
- **Pipeline:** Python 3.13 in `.venv/` — soccerdata, pandas, scikit-learn, xgboost, supabase-py

## Commands

```bash
# Frontend
npm run dev          # dev server
npm run build        # production build
npm run lint         # ESLint

# Python
.\.venv\Scripts\activate          # Windows venv
python -c "import soccerdata"     # verify venv
```

## Environment

- `.env.local` — Supabase anon key (gitignored, never commit)
- `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` — GitHub Actions secrets for pipeline writes
- The Python pipeline uses `service_role` key; frontend uses `anon` key only

## Project structure

```
app/              # Next.js App Router pages (transfers, matches, scouting)
lib/              # Supabase client, shared utils
components/       # React components
src/ingestion/    # Data fetchers (FBref, Transfermarkt, matches/elo)
src/features/     # Feature engineering scripts
src/models/       # train.py + predict.py per module
data/raw/         # Cached data from ingestion
data/processed/   # Engineered features
```

## Conventions

- **RLS on all tables** — `select` for `anon`, no `insert`/`update`/`delete` from frontend
- **ISR over fetch** — `revalidate: 86400` (transfers/scouting), `3600` (matches)
- **Pipeline writes via service_role key only** — never expose to frontend
- **Python scripts are idempotent** — safe to re-run; they upsert, not insert
- **Transfermarkt dataset is frozen** — updates paused since Jul 2026, treat as static snapshot

## Supabase MCP

Project ID: `kswtdayhvzzhrbdwzgqb` — use `supabase_*` tools for schema queries, RLS checks, edge functions.
