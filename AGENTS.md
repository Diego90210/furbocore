# Furbocore Analytics — Agent Instructions

Premier League analytics app: transfer values, match predictions, scouting (player similarity via pgvector).

## 1. Before you begin (mandatory)

1. Read `progress/current.md` so you know where the last session ended.
2. Read `feature_list.json` and choose ONE task with `pending` status. Do not work on more than one task at a time.

## 2. Repository map

| File / Folder | What it contains | When to read it |
|---|---|---|
| `feature_list.json` | All features with status (pending/in_progress/done/blocked) | Start of every session — pick your task |
| `progress/current.md` | Live session log — feature, start time, plan, notes | Start of session; update continuously while working |
| `progress/history.md` | Completed session summaries (append-only) | Start of session — avoid repeating past work |
| `docs/` | Reference documentation (architecture, data sources, API notes) | When you don't know something — search here first |
| `app/` | Next.js App Router pages (transfers, matches, scouting) | Working on frontend UI |
| `lib/` | Supabase client singleton | Working with DB queries from frontend |
| `components/` | Shared React components (PlayerSearchBox) | Working on shared UI |
| `src/ingestion/` | Data fetchers (Kaggle, Transfermarkt, football-data.org) | Working on data pipelines |
| `src/features/` | Feature engineering per model | Working on ML features |
| `src/models/` | `train.py` + `predict.py` per module | Working on ML training/prediction |
| `src/models/*/run_pipeline.py` | Orchestrators called by CI | Working on pipeline entry points |
| `.github/workflows/` | CI pipelines (transfer-value monthly, match weekly) | Working on CI/CD |
| `README.md` | Full project status, schema, commands | Need project overview |
| `.env.local` | Secrets (gitignored) | Never commit; check var names only |
| `AGENTS.md` | This file — session rules and lifecycle | Every session |

## 3. Hard rules (non-negotiables)

- **One feature at a time.** Do not mix changes from various tasks in the same session.
- **Do not declare a task as "done" without green tests.** Execute the test file indicated to you. The test block must pass at 100%.
- **Document what you do in `progress/current.md` while you work**, not at the end of the session.
- **Leave the repository clean.** Before closing the session: no temporary files, no debug `print()`, no TODOs without context.
- **If you don't know something, search `docs/` first** before making something up.

## 4. How to choose a task

1. Open `feature_list.json`.
2. Filter by `status == "pending"`.
3. Choose the one with the **lesser `id`**.
4. Change its status to `"in_progress"`.
5. Take note in `progress/current.md`: Feature, start time, short plan.

## 5. Session closing (lifecycle)

1. Execute the test file (the one we will create later). Must pass 100%.
2. If the task is done: set `"status": "done"` in `feature_list.json`.
3. Move the summary from `progress/current.md` to the end of `progress/history.md`.
4. Blank `progress/current.md`, leaving just the template.
5. Remove any temporary files, debug `print()` calls, or context-free TODOs.

## 6. If you block

- Reread the relevant section of `docs/`.
- If a tool does not do what you expect, **do not work around it**: document the blockage in `progress/current.md` and stop the session.

## Stack reference

- **Frontend:** Next.js 16 App Router + Tailwind CSS 4 + TypeScript — `app/` directory
- **Database:** Supabase (Postgres 17 + pgvector + pg_trgm + pgcrypto) — project `kswtdayhvzzhrbdwzgqb`
- **Pipeline:** Python 3.13 in `.venv/` — pandas, scikit-learn, xgboost, supabase-py, kagglehub

## Commands

```bash
# Frontend
npm run dev          # dev server
npm run build        # production build
npm run lint         # ESLint

# Python
.\.venv\Scripts\activate          # Windows venv
PYTHONPATH=. python src/...       # run any pipeline script
```

## Conventions

- **RLS on all tables** — `select` for `anon`, no `insert`/`update`/`delete` from frontend
- **ISR over fetch** — `revalidate: 86400` (transfers/scouting), `3600` (matches)
- **Pipeline writes via service_role key only** — never expose to frontend
- **Python scripts are idempotent** — safe to re-run; they upsert, not insert
- **Transfermarkt dataset is frozen** — snapshot since Jul 2026, treat as static
- **Supabase MCP** — Project ID `kswtdayhvzzhrbdwzgqb`, use `supabase_*` tools for schema/RLS
