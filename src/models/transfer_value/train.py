"""Train transfer value prediction model.

Split: temporal (train on past seasons, test on latest).
Algorithm: RandomForestRegressor.
Target: log1p(real_value_eur).
Metrics: MAE/RMSE on log scale, MAE in euros.
"""
import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

# Add parent dirs to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.features.transfer_value import build_training_set

MODELS_DIR = Path(__file__).resolve().parent


def train():
    X, y, meta = build_training_set()
    if X is None:
        print("ERROR: No training data available")
        sys.exit(1)

    # Temporal split: use last season as test
    meta["season_end"] = meta["season"].str.split("-").str[1].astype(int)
    max_season = meta["season_end"].max()
    test_mask = meta["season_end"] == max_season

    X_train, X_test = X[~test_mask], X[test_mask]
    y_train, y_test = y[~test_mask], y[test_mask]

    print(f"Train: {len(X_train)} rows, Test: {len(X_test)} rows")
    print(f"Test season ends: {max_season}")

    # Train
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred_log = model.predict(X_test)
    y_pred_eur = np.expm1(y_pred_log)
    y_test_eur = np.expm1(y_test.values)

    mae_log = mean_absolute_error(y_test, y_pred_log)
    rmse_log = np.sqrt(mean_squared_error(y_test, y_pred_log))
    mae_eur = mean_absolute_error(y_test_eur, y_pred_eur)

    print(f"\nMetrics:")
    print(f"  MAE (log):  {mae_log:.4f}")
    print(f"  RMSE (log): {rmse_log:.4f}")
    print(f"  MAE (€):    €{mae_eur:,.0f}")

    # Feature importance
    fi = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
    print(f"\nTop features:")
    for feat, imp in fi.head(5).items():
        print(f"  {feat}: {imp:.3f}")

    # Serialize
    model_version = date.today().isoformat()
    model_path = MODELS_DIR / f"transfer_value_{model_version}.joblib"
    joblib.dump(model, model_path)
    print(f"\nSaved: {model_path}")

    return model, mae_log, rmse_log, mae_eur


if __name__ == "__main__":
    train()
