# ThreatVision AI — Cyber Attack Trend Prediction

IA 3 project for Cyber Threat Intelligence and Analytics.

## Features
- Historical cyber attack analytics dashboard
- Phishing, Malware, DDoS, Ransomware and SQL Injection analysis
- Attack-category distribution chart
- Monthly cyber attack trend visualization
- Machine-learning trend forecasting using Linear Regression
- Risk classification and mitigation recommendation
- Flask REST API + HTML/CSS/JavaScript frontend

## How to run on Windows / VS Code

1. Extract/open the project folder in VS Code.
2. Open **Terminal > New Terminal**.
3. Optional but recommended: create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run:
   ```bash
   python app.py
   ```
6. Open the address shown in terminal, normally:
   `http://127.0.0.1:5000`

The application automatically trains the ML models and creates `attack_models.pkl` the first time it starts.

## Project architecture

Frontend (HTML + CSS + JavaScript + Chart.js)
→ Flask API
→ Pandas preprocessing
→ Scikit-learn Linear Regression model
→ Cyber attack trend prediction

## Academic note
`cyber_attacks.csv` is a demonstration dataset created for this prototype. For a final research submission, replace it with a properly cited public cyber-threat dataset and retrain the model.
