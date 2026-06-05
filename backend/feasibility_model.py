import logging
log = logging.getLogger("RetrofitAI")
"""
feasibility_model.py
--------------------
Trains a Random Forest model to predict EV retrofit feasibility score (0-100)
and saves it as models/retrofit_model.pkl
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, accuracy_score
import pickle
import os

# ─── Encode vehicle types ─────────────────────────────────────────────────────
VEHICLE_TYPE_MAP = {
    "Hatchback": 0,
    "Sedan": 1,
    "SUV": 2,
    "Three-Wheeler": 3,
    "Pickup": 4,
    "Van": 5
}

GEARBOX_MAP = {
    "Manual": 0,
    "Automatic": 1
}

def load_and_prepare_data(csv_path: str):
    df = pd.read_csv(csv_path)
    df["vehicle_type_enc"] = df["vehicle_type"].map(VEHICLE_TYPE_MAP).fillna(0)
    df["gearbox_enc"] = df["gearbox_type"].map(GEARBOX_MAP).fillna(0)
    features = [
        "vehicle_type_enc", "engine_cc", "vehicle_age_years",
        "chassis_condition", "odometer_km", "gearbox_enc",
        "weight_kg", "wheelbase_mm", "has_rust",
        "electrical_condition", "brake_condition"
    ]
    X = df[features]
    y_score = df["feasibility_score"]
    y_class = df["recommended"]
    return X, y_score, y_class, features


def train_model(csv_path: str, model_out_path: str):
    """
    Trains on combined dataset:
    - sample_vehicles.csv (30 synthetic, AIS-038/CMVR derived)
    - real_retrofit_cases.csv (30 real public cases: ARAI, MoRTH, iCAT, OEM)
    Total: 60 training records.
    """
    import os
    data_dir = os.path.dirname(csv_path)
    real_path = os.path.join(data_dir, "real_retrofit_cases.csv")

    X_s, ys_s, yc_s, features = load_and_prepare_data(csv_path)

    if os.path.exists(real_path):
        X_r, ys_r, yc_r, _ = load_and_prepare_data(real_path)
        X       = pd.concat([X_s, X_r], ignore_index=True)
        y_score = pd.concat([ys_s, ys_r], ignore_index=True)
        y_class = pd.concat([yc_s, yc_r], ignore_index=True)
    else:
        X, y_score, y_class = X_s, ys_s, yc_s

    # Drop any rows where score or class is NaN (failed vehicles may have empty scores)
    valid = y_score.notna() & y_class.notna()
    X       = X[valid].reset_index(drop=True)
    y_score = y_score[valid].reset_index(drop=True).astype(float)
    y_class = y_class[valid].reset_index(drop=True).astype(int)
    log.info(f"Training on {len(X)} valid records (dropped {(~valid).sum()} rows with NaN)")

    # Split
    X_train, X_test, ys_train, ys_test, yc_train, yc_test = train_test_split(
        X, y_score, y_class, test_size=0.2, random_state=42
    )

    # Regression model → feasibility score
    reg = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)
    reg.fit(X_train, ys_train)
    pred_score = reg.predict(X_test)
    mae = mean_absolute_error(ys_test, pred_score)
    print(f"[Regression] MAE on test set: {mae:.2f} points")

    # Classification model → go/no-go
    clf = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42)
    clf.fit(X_train, yc_train)
    pred_class = clf.predict(X_test)
    acc = accuracy_score(yc_test, pred_class)
    print(f"[Classifier] Accuracy on test set: {acc*100:.1f}%")

    bundle = {
        "regressor": reg,
        "classifier": clf,
        "features": features,
        "vehicle_type_map": VEHICLE_TYPE_MAP,
        "gearbox_map": GEARBOX_MAP
    }

    os.makedirs(os.path.dirname(model_out_path), exist_ok=True)
    with open(model_out_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"Model saved to {model_out_path}")
    return bundle


def load_model(model_path: str):
    with open(model_path, "rb") as f:
        return pickle.load(f)


def predict(bundle: dict, vehicle_data: dict) -> dict:
    """
    vehicle_data keys:
        vehicle_type, engine_cc, vehicle_age_years, chassis_condition (1-10),
        odometer_km, gearbox_type, weight_kg, wheelbase_mm, has_rust (0/1),
        electrical_condition (1-10), brake_condition (1-10)
    """
    vtype = bundle["vehicle_type_map"].get(vehicle_data.get("vehicle_type", "Hatchback"), 0)
    gbox  = bundle["gearbox_map"].get(vehicle_data.get("gearbox_type", "Manual"), 0)

    row = pd.DataFrame([{
        "vehicle_type_enc":     vtype,
        "engine_cc":            vehicle_data.get("engine_cc", 1000),
        "vehicle_age_years":    vehicle_data.get("vehicle_age_years", 5),
        "chassis_condition":    vehicle_data.get("chassis_condition", 7),
        "odometer_km":          vehicle_data.get("odometer_km", 50000),
        "gearbox_enc":          gbox,
        "weight_kg":            vehicle_data.get("weight_kg", 900),
        "wheelbase_mm":         vehicle_data.get("wheelbase_mm", 2400),
        "has_rust":             vehicle_data.get("has_rust", 0),
        "electrical_condition": vehicle_data.get("electrical_condition", 7),
        "brake_condition":      vehicle_data.get("brake_condition", 7)
    }])

    score     = float(np.clip(bundle["regressor"].predict(row)[0], 0, 100))
    go_no_go  = bool(bundle["classifier"].predict(row)[0])
    proba     = bundle["classifier"].predict_proba(row)[0]

    return {
        "feasibility_score": round(score, 1),
        "recommended": go_no_go,
        "confidence_percent": round(float(max(proba)) * 100, 1),
        "grade": _grade(score)
    }


def _grade(score: float) -> str:
    if score >= 85: return "A – Excellent"
    if score >= 70: return "B – Good"
    if score >= 55: return "C – Moderate"
    if score >= 40: return "D – Poor"
    return "F – Not Recommended"


if __name__ == "__main__":
    BASE = os.path.dirname(os.path.abspath(__file__))
    csv_path   = os.path.join(BASE, "..", "data", "sample_vehicles.csv")
    model_path = os.path.join(BASE, "..", "models", "retrofit_model.pkl")
    train_model(csv_path, model_path)
