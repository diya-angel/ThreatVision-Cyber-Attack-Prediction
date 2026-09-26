from flask import Flask, render_template, request, jsonify
import os
import pandas as pd
import joblib
from train_model import train_models

app = Flask(__name__)
DATA_FILE = "cyber_attacks.csv"
MODEL_FILE = "attack_models.pkl"

RECOMMENDATIONS = {
    "Phishing": "Enable email filtering, MFA, and regular phishing-awareness training.",
    "Malware": "Keep endpoints patched, use EDR/antivirus, and restrict unknown downloads.",
    "DDoS": "Use rate limiting, CDN/WAF protection, and traffic anomaly monitoring.",
    "Ransomware": "Maintain offline backups, apply least privilege, and segment critical networks.",
    "SQL Injection": "Use parameterized queries, input validation, and a web application firewall."
}

def load_models():
    if not os.path.exists(MODEL_FILE):
        train_models()
    return joblib.load(MODEL_FILE)

models = load_models()

def risk_level(value):
    if value >= 450:
        return "Critical"
    if value >= 300:
        return "High"
    if value >= 180:
        return "Medium"
    return "Low"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/summary")
def summary():
    data = pd.read_csv(DATA_FILE)
    latest = data[data["month_number"] == data["month_number"].max()]
    totals = data.groupby("attack_type")["attack_count"].sum().sort_values(ascending=False)
    monthly = data.groupby("month_number")["attack_count"].sum().sort_index()
    return jsonify({
        "total_attacks": int(data["attack_count"].sum()),
        "highest_attack": totals.index[0],
        "highest_count": int(totals.iloc[0]),
        "latest_total": int(latest["attack_count"].sum()),
        "attack_types": totals.index.tolist(),
        "attack_totals": [int(v) for v in totals.values],
        "months": [int(v) for v in monthly.index.tolist()],
        "monthly_totals": [int(v) for v in monthly.values.tolist()]
    })

@app.route("/api/predict", methods=["POST"])
def predict():
    payload = request.get_json(silent=True) or {}
    attack_type = payload.get("attack_type", "Phishing")
    months_ahead = int(payload.get("months_ahead", 1))

    if attack_type not in models:
        return jsonify({"error": "Unknown attack type"}), 400

    months_ahead = max(1, min(months_ahead, 6))
    target_month = 12 + months_ahead
    prediction = max(0, int(round(models[attack_type].predict([[target_month]])[0])))

    data = pd.read_csv(DATA_FILE)
    group = data[data["attack_type"] == attack_type].sort_values("month_number")
    current = int(group.iloc[-1]["attack_count"])

    if prediction > current * 1.05:
        trend = "Increasing"
    elif prediction < current * 0.95:
        trend = "Decreasing"
    else:
        trend = "Stable"

    confidence = min(96, 82 + months_ahead)

    return jsonify({
        "attack_type": attack_type,
        "months_ahead": months_ahead,
        "current_attacks": current,
        "predicted_attacks": prediction,
        "trend": trend,
        "risk": risk_level(prediction),
        "confidence": confidence,
        "recommendation": RECOMMENDATIONS.get(attack_type, "Monitor threat intelligence feeds and strengthen preventive controls.")
    })

if __name__ == "__main__":
    app.run(debug=True)
