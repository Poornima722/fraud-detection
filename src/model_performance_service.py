from functools import lru_cache
import json
from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "model" / "final_fraud_catboost.cbm"
CONFIG_PATH = PROJECT_ROOT / "model" / "model_config.json"
EVALUATION_DATASET_PATH = PROJECT_ROOT / "processed_test.parquet"


@lru_cache(maxsize=1)
def calculate_model_performance():
    """Evaluate the saved model on the held-out processed test dataset."""

    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    evaluation_data = pd.read_parquet(EVALUATION_DATASET_PATH)
    model_features = config["model_features"]
    labels = evaluation_data["is_fraud"].astype(int)

    model = CatBoostClassifier()
    model.load_model(str(MODEL_PATH))
    fraud_probabilities = model.predict_proba(
        evaluation_data[model_features]
    )[:, 1]

    threshold = float(config["threshold"])
    predictions = (fraud_probabilities >= threshold).astype(int)
    true_negative, false_positive, false_negative, true_positive = (
        confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    )

    return {
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1_score": float(f1_score(labels, predictions, zero_division=0)),
        "false_positive_rate": float(
            false_positive / (false_positive + true_negative)
        ),
        "threshold": threshold,
        "evaluation_set": EVALUATION_DATASET_PATH.name,
        "sample_count": int(len(labels)),
        "confusion_matrix": {
            "true_negatives": int(true_negative),
            "false_positives": int(false_positive),
            "false_negatives": int(false_negative),
            "true_positives": int(true_positive),
        },
    }