"""Train match outcome prediction model.

Split: temporal (test on most recent season).
Algorithm: XGBClassifier with multi:softprob.
Metrics: log-loss (primary), accuracy, F1 per class.
Handles class imbalance via sample_weight.
"""
import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, log_loss
from xgboost import XGBClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.features.match_outcome import build_training_set

MODELS_DIR = Path(__file__).resolve().parent


def train():
    X, y, meta = build_training_set()
    if X is None:
        print("ERROR: No training data")
        sys.exit(1)

    # Temporal split: last season as test
    # Use match_date from meta
    meta["_date"] = pd.to_datetime(meta["match_date"])
    meta["_year"] = meta["_date"].dt.year
    max_year = meta["_year"].max()
    test_mask = meta["_year"] == max_year

    X_train, X_test = X[~test_mask], X[test_mask]
    y_train, y_test = y[~test_mask], y[test_mask]

    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    # Class weights for imbalance (draws are underrepresented)
    class_counts = y_train.value_counts()
    total = len(y_train)
    weights = {cls: total / (len(class_counts) * count) for cls, count in class_counts.items()}
    sample_weight = y_train.map(weights)

    # Train
    model = XGBClassifier(
        objective="multi:softprob",
        num_class=3,
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="mlogloss",
        use_label_encoder=False,
    )
    model.fit(X_train, y_train, sample_weight=sample_weight)

    # Evaluate
    y_prob = model.predict_proba(X_test)
    y_pred = model.predict(X_test)

    ll = log_loss(y_test, y_prob)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average=None)

    print(f"\nMetrics:")
    print(f"  Log-loss: {ll:.4f}")
    print(f"  Accuracy: {acc:.4f}")
    print(f"  F1 per class: {dict(enumerate(f1))}")
    print(f"    home_win={f1[0]:.3f}, draw={f1[1]:.3f}, away_win={f1[2]:.3f}")

    # Serialize
    model_version = date.today().isoformat()
    model_path = MODELS_DIR / f"match_outcome_{model_version}.joblib"
    joblib.dump(model, model_path)
    print(f"\nSaved: {model_path}")

    return model


if __name__ == "__main__":
    train()
