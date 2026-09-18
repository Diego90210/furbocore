# Furbocore Analytics

Premier League football analytics platform with transfer value predictions, match outcome forecasts, and AI-powered player scouting.

## Live Deployment

- **Frontend:** https://furbocore.vercel.app
- **Database:** Supabase (Postgres 17 + pgvector + pg_trgm)
- **CI/CD:** GitHub Actions (monthly + weekly pipelines)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 (App Router) + React 19 + TypeScript 5 + Tailwind CSS 4 |
| Database | Supabase (Postgres 17, pgvector 0.8.2, pg_trgm 1.6, pgcrypto 1.3) |
| ML Pipeline | Python 3.13, scikit-learn 1.6.1, XGBoost 2.1.3, pandas 2.2.3 |
| Data Sources | Kaggle (player-scores), Transfermarkt (R2 snapshot), football-data.org |
| Deployment | Vercel (frontend), GitHub Actions (ML pipelines) |

## Modules

### Transfer Value Analyzer (`/transfers`)

Predicts player market value using a RandomForestRegressor trained on real Transfermarkt valuations.

- **Features (8):** minutes_played, goals_per90, assists_per90, age_at_season, position one-hot (DF/FW/GK/MF)
- **Target:** `log1p(real_value_eur)`
- **Model:** 200 trees, max_depth=12, min_samples_leaf=5
- **Training data:** 265 players with real Transfermarkt valuations
- **Output:** predicted_value_eur + value_gap_pct (over/undervalued assessment)

### Match Predictions (`/matches`)

Upcoming Premier League fixtures with AI-powered win/draw/loss probabilities.

- **Features:** Form-based (last 5 results), ELO ratings
- **Model:** XGBClassifier
- **Schedule:** Weekly retrain (Monday 6am UTC)
- **Data source:** football-data.org API (2 seasons + scheduled fixtures)

### Scouting Tool (`/scouting`)

Find similar players using KMeans clustering and pgvector L2 similarity search.

- **Features:** goals_per90, assists_per90 (per position group)
- **Groups:** GK, DF, MF, FW (separate KMeans per group)
- **Vector dimension:** vector(2) for pgvector similarity
- **RPC:** `similar_players(query_vector, pos_group, exclude_id, match_count)`
- **Output:** Top-10 most similar players by L2 distance

## Database Schema

| Table | Rows | Description |
|-------|------|-------------|
| `players` | 3,365 | All players (deduplicated by name) |
| `player_stats` | 7,496 | Season-level stats (goals, assists, minutes, age) |
| `transfer_values` | 3,365 | Real + predicted market values per player |
| `matches` | 1,125 | Historical + scheduled PL fixtures |
| `match_predictions` | 365 | Win/draw/loss probabilities per match |
| `player_clusters` | 1,547 | Cluster assignments + feature vectors (vector(2)) |

### Key Extensions

- `vector` 0.8.2 — pgvector for similarity search
- `pg_trgm` 1.6 — trigram text search
- `pgcrypto` 1.3 — UUID generation

### RLS Policies

All tables have RLS enabled with public read-only access (`SELECT` for `anon` role). No `INSERT`/`UPDATE`/`DELETE` from the frontend. Pipeline writes use the `service_role` key.

## Project Structure

```
app/                          # Next.js App Router
  layout.tsx                  # Root layout, nav, footer
  page.tsx                    # Landing page
  globals.css                 # Tailwind + custom gradients
  transfers/                  # Transfer Value module
    page.tsx                  # Server component + search
    PlayerCard.tsx            # Stats table + valuation
  matches/                    # Match Prediction module
    page.tsx                  # Server component
    MatchCard.tsx             # Probabilities + form badges
  scouting/                   # Scouting module
    page.tsx                  # Server component + search
    SimilarPlayers.tsx        # Radar chart + similarity table

lib/
  supabase.ts                 # Frontend Supabase client (anon key)

components/
  PlayerSearchBox.tsx         # Shared debounced search + dropdown

src/
  features/                   # Feature engineering
    transfer_value.py         # 8 features: stats + position
    scouting.py               # 2 features: goals/assists per-90
    match_outcome.py          # Form-based features
  ingestion/                  # Data pipelines
    player_stats_kaggle.py    # Kaggle → players + player_stats
    transfermarkt_values.py   # Transfermarkt R2 → transfer_values
    football_data_org.py      # football-data.org API → matches
  models/
    transfer_value/
      train.py                # RandomForestRegressor
      predict.py              # Predict + upsert
      run_pipeline.py         # Orchestrator (train → predict)
    scouting/
      train.py                # KMeans per position group
      predict.py              # Assign clusters + upsert vector
    match_outcome/
      train.py                # Match outcome model
      predict.py              # Predict scheduled matches
```

## Environment Variables

| Variable | Scope | Purpose |
|----------|-------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Frontend | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Frontend | Supabase anon key (RLS) |
| `SUPABASE_SERVICE_KEY` | Pipeline | Supabase service role key |
| `KAGGLE_USERNAME` | Pipeline | Kaggle API username |
| `KAGGLE_KEY` | Pipeline | Kaggle API key |
| `FOOTBALL_DATA_ORG_TOKEN` | Pipeline | football-data.org API token |

`.env.local` is gitignored. GitHub Actions secrets store the pipeline keys.

## CI/CD Pipelines

### Transfer Value Pipeline (monthly)

- **Schedule:** 1st of each month, 6am UTC
- **Manual trigger:** Yes
- **Steps:**
  1. Ingest player stats from Kaggle
  2. Ingest Transfermarkt market values
  3. Train transfer value model (RandomForest)
  4. Predict for all players
  5. Train scouting clusters (KMeans)
  6. Assign clusters + upsert vectors

### Match Pipeline (weekly)

- **Schedule:** Every Monday, 6am UTC
- **Manual trigger:** Yes
- **Steps:**
  1. Ingest matches from football-data.org
  2. Train match outcome model
  3. Predict scheduled matches

## Commands

```bash
# Frontend
npm run dev          # Dev server (localhost:3000)
npm run build        # Production build
npm run lint         # ESLint

# Python pipelines
.\.venv\Scripts\activate                    # Windows venv activation
python src/ingestion/player_stats_kaggle.py  # Ingest from Kaggle
python src/ingestion/transfermarkt_values.py  # Ingest Transfermarkt
python src/ingestion/football_data_org.py     # Ingest matches
python src/models/transfer_value/run_pipeline.py  # Train + predict transfers
python src/models/scouting/train.py           # Train scouting clusters
python src/models/scouting/predict.py         # Assign clusters
python src/models/match_outcome/train.py      # Train match model
python src/models/match_outcome/predict.py    # Predict matches
```

## Known Limitations

1. **Transfer value training data:** Only 265 players have real Transfermarkt valuations (dataset frozen since Jul 2026). The model's MAE is ~€223k. Accuracy will improve with a more comprehensive market value source.

2. **Kaggle data gaps:** The Kaggle `appearances.csv` only provides goals and assists. Shots, tackles, and interceptions are not available, so scouting features are limited to 2 dimensions.

3. **football-data.org free tier:** Limited to ~2 historical seasons (2023-24 and 2024-25). Older seasons return 403.

4. **FBref blocked:** Direct FBref scraping returns 403. Circumvented via Kaggle dataset.

5. **Transfermarkt static:** Dataset hosted on R2 is a frozen snapshot. Market values won't update until a new snapshot is published.

## License

Private project — not licensed for distribution.
