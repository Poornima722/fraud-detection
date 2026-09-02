from pathlib import Path
import json
import pandas as pd

from catboost import CatBoostClassifier


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Model files
MODEL_PATH = PROJECT_ROOT / "model" / "final_fraud_catboost.cbm"
CONFIG_PATH = PROJECT_ROOT / "model" / "model_config.json"


# Load configuration
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)


# Load trained CatBoost model
model = CatBoostClassifier()
model.load_model(str(MODEL_PATH))


def predict_fraud(transaction):
    """
    Predict fraud probability for one prepared transaction.
    """

    input_df = pd.DataFrame([transaction])

    # Ensure exact feature order used during training
    input_df = input_df[config["model_features"]]

    probability = model.predict_proba(input_df)[0][1]

    threshold = config["threshold"]

    decision = (
        "FRAUD"
        if probability >= threshold
        else "LEGITIMATE"
    )

    return {
        "fraud_probability": float(probability),
        "threshold": float(threshold),
        "decision": decision
    }


