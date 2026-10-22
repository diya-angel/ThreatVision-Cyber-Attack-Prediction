
import json

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
    confusion_matrix,
)
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression

DATA_FILE = "cyber_attacks.csv"
MODEL_FILE = "attack_models.pkl"
CICIDS_MODEL_FILE = "cicids2017_model.pkl"
CICIDS_METRICS_FILE = "cicids2017_metrics.json"


def train_models():
    """Keep existing monthly trend models."""
    data = pd.read_csv(DATA_FILE)
    models = {}

    for attack_type, group in data.groupby("attack_type"):
        X = group[["month_number"]]
        y = group["attack_count"]
        model = LinearRegression()
        model.fit(X, y)
        models[attack_type] = model

    joblib.dump(models, MODEL_FILE)
    print(f"Saved {len(models)} monthly trend models.")


def convert_labels(series):
    """Convert binary numeric labels or BENIGN/attack text labels."""
    if pd.api.types.is_numeric_dtype(series):
        labels = pd.to_numeric(series, errors="raise").astype(int)
        if not set(labels.unique()).issubset({0, 1}):
            raise ValueError(f"Expected binary labels 0/1, found {sorted(labels.unique())}")
        return labels

    text = series.astype(str).str.strip().str.upper()
    known = {"BENIGN", "BENIGNTRAFFIC", "0", "1"}
    if not set(text.unique()).issubset(known):
        # CICIDS2017 multiclass labels: BENIGN=0, all attacks=1.
        return (text != "BENIGN").astype(int)

    return text.map({
        "BENIGN": 0,
        "BENIGNTRAFFIC": 0,
        "0": 0,
        "1": 1,
    }).astype(int)


def train_cicids2017():
    print("Loading CICIDS2017 dataset...")

    # Keep the current dataset configuration for now.
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
        raise ValueError(f"No label column found. Columns: {list(train_df.columns)}")

    feature_columns = [
        c for c in train_df.select_dtypes(include=np.number).columns
        if c.lower() not in {"label", "class", "target"}
    ]
    if not feature_columns:
        raise ValueError("No numeric features found.")

    X_train = train_df[feature_columns].replace([np.inf, -np.inf], np.nan)
    X_test = test_df.reindex(columns=feature_columns).replace(
        [np.inf, -np.inf], np.nan
    )

    y_train = convert_labels(train_df[label_column])
    y_test = convert_labels(test_df[label_column])

    print("Training class counts:", y_train.value_counts().to_dict())
    print("Testing class counts:", y_test.value_counts().to_dict())

    if y_train.nunique() < 2:
        raise ValueError("Training data must contain both benign and attack examples.")
    if y_test.nunique() < 2:
        raise ValueError("Test data must contain both benign and attack examples.")

    pipeline = make_pipeline(
        SimpleImputer(strategy="median"),
        RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",
        ),
    )

    print(f"Training on {len(X_train)} rows, {len(feature_columns)} features.")
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)

    tn, fp, fn, tp = confusion_matrix(
        y_test, predictions, labels=[0, 1]
    ).ravel()

    metrics = {
        "dataset": "CICIDS2017",
        "task": "Binary classification: benign (0) vs attack (1)",
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "feature_count": int(len(feature_columns)),
        "train_benign_rows": int((y_train == 0).sum()),
        "train_attack_rows": int((y_train == 1).sum()),
        "test_benign_rows": int((y_test == 0).sum()),
        "test_attack_rows": int((y_test == 1).sum()),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
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

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    train_models()
    train_cicids2017()
