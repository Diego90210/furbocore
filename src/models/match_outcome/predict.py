"""Predict outcomes for scheduled matches and upsert to match_predictions.

Loads most recent model, pulls scheduled matches, calculates form,
predicts probabilities, and writes to match_predictions.
"""
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

MODELS_DIR = Path(__file__).resolve().parent

FEATURE_COLS = [
    "home_form_wins",
    "away_form_wins",
    "home_form_drops",
    "away_form_drops",
]


def find_latest_model():
    models = sorted(MODELS_DIR.glob("match_outcome_*.joblib"), reverse=True)
    if not models:
        print("ERROR: No model files found")
        sys.exit(1)
    return models[0]


def get_all_played(client):
    """Get all played matches for form calculation."""
    rows = []
    offset = 0
    while True:
        resp = (
            client.table("matches")
            .select("*")
            .eq("status", "played")
            .order("match_date")
            .range(offset, offset + 999)
            .execute()
        )
        if not resp.data:
            break
        rows.extend(resp.data)
        offset += 1000
    return pd.DataFrame(rows)


def get_scheduled(client):
    """Get upcoming scheduled matches."""
    resp = (
        client.table("matches")
        .select("*")
        .eq("status", "scheduled")
        .order("match_date")
        .limit(10)
        .execute()
    )
    return pd.DataFrame(resp.data)


def calc_form_for_team(team, before_date, all_played, n=5):
    """Get form string and numeric features for a team before a date."""
    team_matches = all_played[
        ((all_played["home_team"] == team) | (all_played["away_team"] == team))
        & (all_played["match_date"] < before_date)
    ].tail(n)

    results = []
    for _, row in team_matches.iterrows():
        hg, ag = row.get("home_goals"), row.get("away_goals")
        if hg is None or ag is None:
            continue
        is_home = row["home_team"] == team
        if hg > ag:
            results.append("W" if is_home else "L")
        elif hg < ag:
            results.append("L" if is_home else "W")
        else:
            results.append("D")

    form_str = "-".join(results) if results else ""
    wins = results.count("W") / max(len(results), 1)
    losses = results.count("L") / max(len(results), 1)
    return form_str, wins, losses


def predict_and_upsert():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY")
        sys.exit(1)

    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    model_path = find_latest_model()
    print(f"Loading model: {model_path.name}")
    model = joblib.load(model_path)
    model_version = model_path.stem.replace("match_outcome_", "")

    print("Fetching all played matches for form...")
    all_played = get_all_played(client)

    print("Fetching scheduled matches...")
    scheduled = get_scheduled(client)
    if scheduled.empty:
        print("No scheduled matches found")
        return

    print(f"Predicting {len(scheduled)} matches...")
    upserted = 0

    for _, row in scheduled.iterrows():
        match_id = row["id"]
        home = row["home_team"]
        away = row["away_team"]
        match_date = row["match_date"]

        h_form, h_wins, h_losses = calc_form_for_team(home, match_date, all_played)
        a_form, a_wins, a_losses = calc_form_for_team(away, match_date, all_played)

        features = pd.DataFrame(
            [[h_wins, a_wins, h_losses, a_losses]], columns=FEATURE_COLS
        )

        probs = model.predict_proba(features)[0]  # [home_win, draw, away_win]

        client.table("match_predictions").upsert(
            {
                "match_id": match_id,
                "home_win_prob": round(float(probs[0]), 4),
                "draw_prob": round(float(probs[1]), 4),
                "away_win_prob": round(float(probs[2]), 4),
                "home_form_summary": h_form,
                "away_form_summary": a_form,
                "model_version": model_version,
            },
            on_conflict="match_id",
        ).execute()
        upserted += 1

    print(f"Upserted {upserted} predictions")


if __name__ == "__main__":
    predict_and_upsert()
