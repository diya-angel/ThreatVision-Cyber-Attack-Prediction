
import json
import os

import joblib
import numpy as np
import pandas as pd
from datasets import load_dataset
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.pipeline import make_pipeline

DATA_FILE = "cyber_attacks.csv"
MODEL_FILE = "attack_models.pkl"

CICIDS_MODEL_FILE = "cicids2017_model.pkl"
CICIDS_METRICS_FILE = "cicids2017_metrics.json"

def train_models():
    """Keep the existing monthly trend prediction models."""
    data = pd.read_csv(DATA_FILE)
    models = {}

    for attack_type, group in data.groupby("attack_type"):
        X = group[["month_number"]]
        y = group["attack_count"]

        model = __import__(
            "sklearn.linear_model", fromlist=["LinearRegression"]
        ).LinearRegression()
        model.fit(X, y)
        models[attack_type] = model

    joblib.dump(models, MODEL_FILE)
    print(f"Saved {len(models)} monthly trend models.")


def train_cicids2017():
    """Train a separate binary classifier on a small CICIDS2017 subset."""
    print("Loading CICIDS2017 dataset from Hugging Face...")

    train_data = load_dataset(
        "lacg030175/CICIDS2017",
        "temporal",
        split="train[:50000]",
    )
    test_data = load_dataset(
        "lacg030175/CICIDS2017",
        "temporal",
        split="test[:15000]",
    )

    train_df = train_data.to_pandas()
    test_df = test_data.to_pandas()

    label_column = next(
        (c for c in train_df.columns if c.lower() == "label"),
        None,
    )
    if label_column is None:
        raise ValueError(
            f"Could not find a label column. Available columns: {list(train_df.columns)}"
        )

    # Use numeric network-traffic features only; exclude the target label.
    feature_columns = [
        c for c in train_df.select_dtypes(include=np.number).columns
        if c != label_column
    ]
    if not feature_columns:
        raise ValueError("No numeric network-traffic features were found.")

    X_train = train_df[feature_columns].replace([np.inf, -np.inf], np.nan)
    X_test = test_df[feature_columns].replace([np.inf, -np.inf], np.nan)

    y_train = train_df[label_column].astype(str).str.strip().str.upper()
    y_test = test_df[label_column].astype(str).str.strip().str.upper()

    # Convert BENIGN to 0 and all attack labels to 1.
    y_train = (y_train != "BENIGN").astype(int)
    y_test = (y_test != "BENIGN").astype(int)

    pipeline = make_pipeline(
        SimpleImputer(strategy="median"),
        RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",
        ),
    )

    print(f"Training on {len(X_train):,} rows and {len(feature_columns)} features...")
    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)

    metrics = {
        "dataset": "CICIDS2017",
        "task": "Binary classification: benign vs attack",
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "feature_count": int(len(feature_columns)),
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
    }

    joblib.dump(
        {"model": pipeline, "features": feature_columns},
        CICIDS_MODEL_FILE,
    )
    with open(CICIDS_METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("CICIDS2017 evaluation metrics:")
    print(json.dumps(metrics, indent=2))
    print(f"Saved model to {CICIDS_MODEL_FILE}")
    print(f"Saved metrics to {CICIDS_METRICS_FILE}")


if __name__ == "__main__":
    train_models()
    train_cicids2017()
