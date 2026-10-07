# Architecture — What "Doing a Good Job" Means

> This document defines the quality standard. Reviewer agents evaluate code against this file. If it is not stated here, it is not a requirement.

## Principles

1. **Clear layers.** The project has three layers, and only three:

   * **Frontend** — `app/` (pages), `components/` (shared UI), `lib/` (Supabase client). Next.js App Router, React Server Components by default.
   * **Data access** — `src/ingestion/` (fetchers), `src/features/` (feature engineering). Pure Python, no model logic.
   * **ML** — `src/models/` (`train.py` + `predict.py` per module, `run_pipeline.py` orchestrator).

   Do not introduce additional layers (services, repositories, API routes) until there is a concrete reason documented in `feature_list.json`.

2. **Dependencies are allowed but declared.** Frontend deps live in `package.json`, Python deps in `requirements.txt`. Never add a dependency to `requirements.txt` if it duplicates an already-installed package. Kaggle data is accessed via `kagglehub`, football-data.org via `requests`/`httpx` if already present.

3. **Explicit errors.** Python functions that can fail (missing env var, API error, empty dataset) must raise named exceptions rather than return `None`. React pages must have `loading.tsx` and `error.tsx` for every route.

4. **RLS everywhere.** All tables have Row Level Security enabled. Frontend reads via `anon` key only (SELECT policy). Writes go exclusively through the `service_role` key in Python pipelines — never from the browser.

5. **Idempotent writes.** Every Python script must be safe to re-run: use `upsert()` with `on_conflict`, never raw `insert()`. Batch upserts (BATCH=200) — never per-row API calls.

6. **ISR over fetch.** Server-rendered pages use `revalidate` (86400s for transfers/scouting, 3600s for matches) instead of client-side data fetching where possible.

7. **Batch before you loop.** When writing to Supabase from Python, collect rows and send in batches. Do not open a connection per row.

## Data Flow

```text
Kaggle / Transfermarkt / football-data.org
        │
        ▼
src/ingestion/  ──→  Supabase (Postgres + pgvector)
        │                    │
        ▼                    ▼
src/features/          lib/supabase.ts (anon key)
        │                    │
        ▼                    ▼
src/models/train.py    app/ pages (RSC + ISR)
src/models/predict.py       │
        │                    ▼
        ▼              components/ (PlayerSearchBox, cards)
Supabase (upsert via service_role)
```

## What NOT to Do

* Do not expose `SUPABASE_SERVICE_KEY` or any secret to the frontend. Only `NEXT_PUBLIC_*` vars reach the browser.
* Do not fetch data client-side when ISR can serve it. Use `fetch` + `revalidate` in server components.
* Do not write to Supabase from React. The frontend is read-only (RLS enforces this).
* Do not call the Kaggle or football-data.org APIs inside a loop in Python. Fetch once, process in memory, batch upsert.
* Do not add `print()` debugging in committed code. Use `logging` or remove before commit.
* Do not create a new table or column without documenting it in `docs/` and updating `README.md`.
* Do not skip `PYTHONPATH=.` when running Python scripts from the project root — `src` modules will not resolve.
