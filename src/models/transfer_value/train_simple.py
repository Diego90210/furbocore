"""Train + predict transfer values using simplified features.

All-in-one: build training set, train RandomForest, predict, upsert to DB.
"""
import os
import json
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")
load_dotenv(Path.cwd() / ".env.local")
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

MODEL_DIR = Path(__file__).resolve().parents[2] / "models"
FEATURE_COLS = ["pos_DF", "pos_FW", "pos_GK", "pos_MF"]


def build_training_set():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    players_rows = []
    offset = 0
    while True:
        resp = client.table("players").select("id,name,position").range(offset, offset + 999).execute()
        if not resp.data:
            break
        players_rows.extend(resp.data)
        offset += 1000

    val_rows = []
    offset = 0
    while True:
        resp = (
            client.table("transfer_values")
            .select("player_id,real_value_eur")
            .not_.is_("real_value_eur", "null")
            .range(offset, offset + 999)
            .execute()
        )
        if not resp.data:
            break
        val_rows.extend(resp.data)
        offset += 1000

    players_df = pd.DataFrame(players_rows)
    val_df = pd.DataFrame(val_rows)

    merged = players_df.merge(val_df, left_on="id", right_on="player_id", how="inner")
    merged = merged.dropna(subset=["real_value_eur"])
    merged = merged[merged["real_value_eur"] > 0].copy()

    merged["position"] = merged["position"].fillna("MF")
    pos_dummies = pd.get_dummies(merged["position"], prefix="pos")
    merged = pd.concat([merged, pos_dummies], axis=1)
    for col in FEATURE_COLS:
        if col not in merged.columns:
            merged[col] = 0

    y = np.log1p(merged["real_value_eur"].astype(float))
    meta = merged[["player_id", "name", "real_value_eur"]].copy()
    X = merged[FEATURE_COLS].fillna(0)
    return X, y, meta


def train():
    X, y, meta = build_training_set()
    if X is None:
        print("No training data")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"MAE (log): {mae:.4f}, R2: {r2:.4f}")
    print(f"MAE (EUR): EUR {np.expm1(mae):,.0f}")
    print(f"Value range: EUR {np.expm1(y.min()):,.0f} - EUR {np.expm1(y.max()):,.0f}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_DIR / "transfer_value_model.pkl")
    print(f"Model saved to {MODEL_DIR / 'transfer_value_model.pkl'}")
    return model


def predict(model):
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    players_rows = []
    offset = 0
    while True:
        resp = client.table("players").select("id,name,position").range(offset, offset + 999).execute()
        if not resp.data:
            break
        players_rows.extend(resp.data)
        offset += 1000

    players_df = pd.DataFrame(players_rows)
    players_df["position"] = players_df["position"].fillna("MF")
    pos_dummies = pd.get_dummies(players_df["position"], prefix="pos")
    players_df = pd.concat([players_df, pos_dummies], axis=1)
    for col in FEATURE_COLS:
        if col not in players_df.columns:
            players_df[col] = 0

    X_pred = players_df[FEATURE_COLS].fillna(0)
    players_df["predicted_log"] = model.predict(X_pred)
    players_df["predicted_value_eur"] = np.expm1(players_df["predicted_log"]).round(0)

    # Get real values
    val_rows = []
    offset = 0
    while True:
        resp = (
            client.table("transfer_values")
            .select("player_id,real_value_eur")
            .not_.is_("real_value_eur", "null")
            .range(offset, offset + 999)
            .execute()
        )
        if not resp.data:
            break
        val_rows.extend(resp.data)
        offset += 1000

    val_df = pd.DataFrame(val_rows)
    players_df = players_df.merge(val_df, left_on="id", right_on="player_id", how="left")

    players_df["value_gap_pct"] = None
    mask = players_df["real_value_eur"].notna() & (players_df["real_value_eur"] > 0)
    players_df.loc[mask, "value_gap_pct"] = (
        (players_df.loc[mask, "predicted_value_eur"] - players_df.loc[mask, "real_value_eur"])
        / players_df.loc[mask, "real_value_eur"]
        * 100
    ).round(1)

    # Upsert predictions
    upserted = 0
    for _, row in players_df.iterrows():
        client.table("transfer_values").upsert(
            {
                "player_id": row["id"],
                "predicted_value_eur": float(row["predicted_value_eur"]),
                "value_gap_pct": float(row["value_gap_pct"]) if pd.notna(row["value_gap_pct"]) else None,
            },
            on_conflict="player_id",
        ).execute()
        upserted += 1

    print(f"Upserted {upserted} predictions")
    print(f"\nTop 10 most overvalued:")
    top_over = players_df.dropna(subset=["value_gap_pct"]).nlargest(10, "value_gap_pct")
    for _, r in top_over.iterrows():
        print(f"  {r['name']}: predicted EUR {r['predicted_value_eur']:,.0f} vs real EUR {r.get('real_value_eur', 0):,.0f} ({r['value_gap_pct']:+.1f}%)")


if __name__ == "__main__":
    model = train()
    if model:
        predict(model)
