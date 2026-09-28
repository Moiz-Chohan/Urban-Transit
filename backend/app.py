"""Flask API for the UrbanTransit IQ dashboard."""

import hashlib
import os
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, session
from flask_cors import CORS

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_data"
OUT = ROOT / "processed_data"
DB = ROOT / "backend" / "urbantransit.db"

app = Flask(__name__)
app.secret_key = os.getenv("UTIQ_SECRET", "urbantransit-local-change-me")
CORS(app, supports_credentials=True)


def load(name, processed=True):
    paths = [OUT / name, RAW / name] if processed else [RAW / name]
    for path in paths:
        if path.exists():
            try:
                return pd.read_csv(path)
            except Exception:
                return pd.DataFrame()
    return pd.DataFrame()


def json_records(data):
    return data.replace({np.nan: None}).to_dict("records")


def password_hash(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def init():
    DB.parent.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, role TEXT)"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY, action TEXT, email TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        connection.execute(
            "INSERT INTO users(email, password, role) VALUES (?, ?, ?)",
            ("admin@gmail.com", password_hash("admin123"), "admin"),
        )
    connection.commit()
    connection.close()


def audit(action):
    connection = sqlite3.connect(DB)
    email = session.get("user", "anonymous")
    connection.execute(
        "INSERT INTO audit_log(action, email) VALUES (?, ?)", (action, email)
    )
    connection.commit()
    connection.close()


@app.post("/api/login")
def login():
    data = request.json or {}
    email = str(data.get("email", "")).strip().lower()
    password = password_hash(data.get("password", ""))
    connection = sqlite3.connect(DB)
    user = connection.execute(
        "SELECT email, role FROM users WHERE LOWER(email) = ? AND password = ?",
        (email, password),
    ).fetchone()
    connection.close()
    if not user:
        return jsonify(message="Invalid credentials"), 401
    session["user"] = user[0]
    audit("login")
    return jsonify(user={"email": user[0], "role": user[1]})


@app.get("/api/dashboard")
def dashboard():
    counts = load("passenger_counts.csv", processed=False)
    delays = load("delays.csv", processed=False)
    routes = load("routes.csv", processed=False)
    if counts.empty:
        return jsonify(records=0, routes=len(routes))
    occupancy = counts.passenger_count / counts.capacity.replace(0, np.nan)
    return jsonify(
        records=len(counts),
        routes=len(routes),
        avg_occupancy=float(occupancy.mean()),
        avg_delay=(
            float(delays.delay_minutes.clip(-10, 120).mean()) if not delays.empty else 0
        ),
        overcrowded=int((occupancy >= 0.95).sum()),
    )


@app.get("/api/routes")
def routes():
    data = load("route_performance.csv")
    if data.empty:
        data = load("route_clusters.csv")
    return jsonify(json_records(data))


@app.get("/api/flow")
def flow():
    data = load("stop_flow.csv")
    if data.empty:
        return jsonify([])
    data = data.sort_values("total_passengers", ascending=False)
    return jsonify(json_records(data.head(30)))


@app.get("/api/delays")
def delays():
    data = load("delays.csv", processed=False)
    if data.empty:
        return jsonify([])
    result = (
        data.assign(delay_minutes=data.delay_minutes.clip(-10, 120))
        .groupby("route_id", as_index=False)
        .agg(
            avg_delay=("delay_minutes", "mean"),
            delay_frequency=("delay_minutes", lambda x: (x > 5).mean()),
        )
        .sort_values("avg_delay", ascending=False)
    )
    return jsonify(json_records(result.head(30)))


@app.get("/api/occupancy")
def occupancy_api():
    data = load("route_performance.csv")
    return jsonify(
        json_records(
            data[
                [
                    c
                    for c in ["route_id", "avg_occupancy", "overcrowding_rate"]
                    if c in data.columns
                ]
            ].head(30)
        )
    )


@app.get("/api/quality")
def quality():
    return jsonify(json_records(load("data_quality_report.csv")))


@app.get("/api/recommendations")
def recommendations():
    return jsonify(json_records(load("recommendations.csv")))


@app.get("/api/forecast")
def forecast():
    historical = load("demand_forecast_predictions.csv")
    future = load("demand_future_forecast.csv")
    return jsonify(
        historical=json_records(historical.head(100)), future=json_records(future)
    )


@app.get("/api/comparison")
def comparison():
    data = load("dual_comparison.csv")
    summary = load("dual_comparison_summary.csv")
    return jsonify(cases=json_records(data.head(500)), summary=json_records(summary))


@app.get("/api/map")
def map_data():
    stops = load("stops.csv", processed=False)
    routes = load("route_performance.csv")
    if stops.empty:
        return jsonify([])
    if not routes.empty:
        route_scores = routes[["route_id", "performance_score"]].copy()
    else:
        route_scores = pd.DataFrame(columns=["route_id", "performance_score"])
    result = stops[["stop_id", "stop_name", "latitude", "longitude"]].copy()
    result["route_performance_available"] = not route_scores.empty
    return jsonify(json_records(result))


@app.get("/api/export/<name>")
def export_file(name):
    allowed = {
        "routes": "route_performance.csv",
        "flow": "stop_flow.csv",
        "delays": "delay_predictions.csv",
        "forecast": "demand_forecast_predictions.csv",
        "recommendations": "recommendations.csv",
        "comparison": "dual_comparison.csv",
        "quality": "data_quality_report.csv",
    }
    filename = allowed.get(name)
    if not filename:
        return jsonify(message="Export not available"), 404
    path = OUT / filename
    if not path.exists():
        return jsonify(message="Run the analytics pipeline first"), 404
    audit(f"export:{name}")
    from flask import send_file

    return send_file(path, as_attachment=True, download_name=filename)


@app.post("/api/what-if")
def what_if():
    data = request.json or {}
    current = float(data.get("occupancy", 0.8))
    frequency_change = float(data.get("frequency_change", 0))
    capacity_change = float(data.get("capacity_change", 0))
    demand_change = float(data.get("demand_change", 0))
    estimated = (
        current
        * (1 + demand_change / 100)
        / max((1 + frequency_change / 100) * (1 + capacity_change / 100), 0.01)
    )
    if estimated >= 1.10:
        risk = "Critical"
    elif estimated >= 0.95:
        risk = "Overcrowded"
    elif estimated >= 0.80:
        risk = "High"
    elif estimated >= 0.60:
        risk = "Moderate"
    else:
        risk = "Low"
    audit("what-if analysis")
    return jsonify(estimated_occupancy=estimated, risk=risk, is_estimate=True)


if __name__ == "__main__":
    init()
    app.run(host="127.0.0.1", port=5000, debug=True)
