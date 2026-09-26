import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

DATA_FILE = "cyber_attacks.csv"
MODEL_FILE = "attack_models.pkl"

def train_models():
    data = pd.read_csv(DATA_FILE)
    models = {}

    for attack_type, group in data.groupby("attack_type"):
        X = group[["month_number"]]
        y = group["attack_count"]
        model = LinearRegression()
        model.fit(X, y)
        models[attack_type] = model

    joblib.dump(models, MODEL_FILE)
    print(f"Saved {len(models)} trained models to {MODEL_FILE}")

if __name__ == "__main__":
    train_models()
