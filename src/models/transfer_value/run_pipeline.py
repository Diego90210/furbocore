"""Orchestrator: train transfer value model + predict for all players.

Thin wrapper that delegates to train.py and predict.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.models.transfer_value.train import train
from src.models.transfer_value.predict import predict_and_upsert


def main():
    print("=" * 60)
    print("TRANSFER VALUE PIPELINE")
    print("=" * 60)

    print("\n--- Training ---")
    model, mae_log, rmse_log, mae_eur = train()

    print("\n--- Predicting ---")
    predict_and_upsert()

    print(f"\nDone. MAE: €{mae_eur:,.0f}")


if __name__ == "__main__":
    main()
