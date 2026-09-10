"""Train KMeans clustering model per position group.

For each position (GK/DF/MF/FW), tries k=3..8, picks best k by silhouette score.
Serializes fitted scalers and cluster models.
"""
import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.features.scouting import build_scouting_features

MODELS_DIR = Path(__file__).resolve().parent


def train():
    scaled_dfs, feature_names, scalers = build_scouting_features()
    if not scaled_dfs:
        print("ERROR: No data")
        sys.exit(1)

    model_version = date.today().isoformat()
    results = {}

    for group, df in scaled_dfs.items():
        X = np.array(df["feature_vector"].tolist())
        if len(X) < 6:
            print(f"  {group}: too few players ({len(X)}), skipping")
            continue

        best_k, best_score, best_model = None, -1, None
        for k in range(3, min(9, len(X))):
            km = KMeans(n_clusters=k, n_init=10, random_state=42)
            labels = km.fit_predict(X)
            score = silhouette_score(X, labels)
            if score > best_score:
                best_k, best_score, best_model = k, score, km

        print(f"  {group}: k={best_k}, silhouette={best_score:.3f}, {len(X)} players")

        # Serialize
        model_path = MODELS_DIR / f"scouting_{group}_{model_version}.joblib"
        scaler_path = MODELS_DIR / f"scaler_{group}_{model_version}.joblib"
        joblib.dump(best_model, model_path)
        joblib.dump(scalers[group], scaler_path)

        results[group] = {
            "k": best_k,
            "silhouette": best_score,
            "model_path": model_path.name,
            "scaler_path": scaler_path.name,
        }

    print(f"\nSaved {len(results)} models for version {model_version}")
    return results


if __name__ == "__main__":
    train()
