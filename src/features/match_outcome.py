"""Feature engineering for match outcome prediction.

For each historical match, calculates:
- Recent form (last 5 matches W/D/L) using ONLY prior matches (no leakage)
- Elo ratings for home/away teams
- Target: home_win / draw / away_win (multiclass)
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")


def get_matches(client):
    """Pull all played matches from Supabase."""
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


def calc_form(matches_df, n=5):
    """Calculate W/D/L form string for each team before each match.

    Uses ONLY matches before match_date — no temporal leakage.
    """
    matches_df = matches_df.sort_values("match_date").reset_index(drop=True)

    # Build team results dict: team -> list of (date, result)
    team_results = {}

    form_home = []
    form_away = []

    for _, row in matches_df.iterrows():
        date = row["match_date"]
        home = row["home_team"]
        away = row["away_team"]
        hg = row.get("home_goals")
        ag = row.get("away_goals")

        # Get form BEFORE this match
        h_form = _get_form(team_results.get(home, []), date, n)
        a_form = _get_form(team_results.get(away, []), date, n)
        form_home.append(h_form)
        form_away.append(a_form)

        # Record result for both teams
        if hg is not None and ag is not None:
            if hg > ag:
                h_result, a_result = "W", "L"
            elif hg < ag:
                h_result, a_result = "L", "W"
            else:
                h_result, a_result = "D", "D"

            team_results.setdefault(home, []).append((date, h_result))
            team_results.setdefault(away, []).append((date, a_result))

    matches_df["home_form_summary"] = form_home
    matches_df["away_form_summary"] = form_away

    # Numeric form: wins in last N
    matches_df["home_form_wins"] = matches_df["home_form_summary"].apply(
        lambda s: s.count("W") / max(len(s), 1) if s else 0
    )
    matches_df["away_form_wins"] = matches_df["away_form_summary"].apply(
        lambda s: s.count("W") / max(len(s), 1) if s else 0
    )
    matches_df["home_form_drops"] = matches_df["home_form_summary"].apply(
        lambda s: s.count("L") / max(len(s), 1) if s else 0
    )
    matches_df["away_form_drops"] = matches_df["away_form_summary"].apply(
        lambda s: s.count("L") / max(len(s), 1) if s else 0
    )

    return matches_df


def _get_form(results, before_date, n):
    """Get form string (e.g. 'W-W-D-L-W') for last n matches before date."""
    prior = [(d, r) for d, r in results if d < before_date]
    last_n = prior[-n:]
    return "-".join(r for _, r in last_n) if last_n else ""


def calc_target(matches_df):
    """Add multiclass target: 0=home_win, 1=draw, 2=away_win."""
    def _target(row):
        hg, ag = row.get("home_goals"), row.get("away_goals")
        if hg is None or ag is None:
            return None
        if hg > ag:
            return 0
        elif hg == ag:
            return 1
        else:
            return 2

    matches_df["target"] = matches_df.apply(_target, axis=1)
    return matches_df


def build_training_set():
    """Build full feature set for match outcome prediction."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("Fetching matches...")
    matches = get_matches(client)
    if matches.empty:
        print("No matches found")
        return None, None, None

    print(f"  {len(matches)} played matches")

    print("Calculating form (no leakage)...")
    matches = calc_form(matches)

    print("Calculating target...")
    matches = calc_target(matches)

    # Drop rows without target
    matches = matches.dropna(subset=["target"])

    # Features
    feature_cols = [
        "home_form_wins",
        "away_form_wins",
        "home_form_drops",
        "away_form_drops",
    ]
    X = matches[feature_cols].fillna(0)
    y = matches["target"].astype(int)

    meta = matches[["id", "home_team", "away_team", "match_date", "home_form_summary", "away_form_summary"]].copy()

    print(f"Training set: {X.shape[0]} rows, {X.shape[1]} features")
    return X, y, meta


if __name__ == "__main__":
    X, y, meta = build_training_set()
    if X is not None:
        print(f"\nTarget distribution:\n{y.value_counts().to_string()}")
        print(f"\nSample features:\n{X.head()}")
