"""
fleet_analyzer.py
-----------------
Processes a fleet CSV (multiple vehicles at once) and returns:
  - Per-vehicle assessments
  - Fleet-level summary (how many viable, total ROI, total CO2)
  - Priority ranking (best candidates first)
"""

import io
import csv
from typing import List, Dict

from feasibility_model  import load_model, predict, train_model
from battery_optimizer  import optimize, battery_config_to_dict
from compliance_checker import check_compliance, compliance_to_dict
from vehicle_physics    import calculate as physics_calc, physics_to_dict
from roi_calculator     import calculate_roi, roi_to_dict

import os

BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "..", "models", "retrofit_model.pkl")
DATA_PATH  = os.path.join(BASE, "..", "data", "sample_vehicles.csv")


REQUIRED_COLUMNS = [
    "vehicle_id", "vehicle_type", "engine_cc", "vehicle_age_years",
    "chassis_condition", "odometer_km", "gearbox_type", "weight_kg",
    "wheelbase_mm", "has_rust", "electrical_condition", "brake_condition",
    "mileage_kmpl"
]

OPTIONAL_DEFAULTS = {
    "target_range_km": 100,
}


def _get_bundle():
    if not os.path.exists(MODEL_PATH):
        train_model(DATA_PATH, MODEL_PATH)
    return load_model(MODEL_PATH)


def analyse_fleet_csv(csv_bytes: bytes) -> Dict:
    """
    Parse CSV bytes, run full assessment on each vehicle, return fleet summary.
    """
    bundle = _get_bundle()
    text   = csv_bytes.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    vehicles   = []
    errors     = []
    row_num    = 1

    for row in reader:
        row_num += 1
        vid = row.get("vehicle_id", f"V{row_num:03d}")
        try:
            vd = _parse_row(row)
        except Exception as e:
            errors.append({"vehicle_id": vid, "row": row_num, "error": str(e)})
            continue

        try:
            feasibility = predict(bundle, vd)
            bat_cfg     = optimize(vd["vehicle_type"], vd["weight_kg"],
                                   vd.get("target_range_km", 100), vd["wheelbase_mm"])
            battery     = battery_config_to_dict(bat_cfg)
            comp        = compliance_to_dict(check_compliance(
                vd["vehicle_type"], bat_cfg.voltage_v, bat_cfg.pack_capacity_kwh,
                bat_cfg.motor["power_kw"], vd["vehicle_age_years"],
                bool(vd["has_rust"]), vd["brake_condition"], vd["electrical_condition"]
            ))
            phys        = physics_to_dict(physics_calc(
                vd["vehicle_type"], vd["weight_kg"],
                vd.get("target_range_km", 100)
            ))
            roi         = roi_to_dict(calculate_roi(
                vd["vehicle_type"], vd.get("mileage_kmpl", 15),
                phys["specific_consumption_wh_km"], battery["estimated_cost_inr"]
            ))

            vehicles.append({
                "vehicle_id":      vid,
                "vehicle_type":    vd["vehicle_type"],
                "feasibility":     feasibility,
                "battery":         battery,
                "compliance":      comp,
                "physics":         phys,
                "roi":             roi,
                "recommended":     feasibility["recommended"],
                "score":           feasibility["feasibility_score"],
            })

        except Exception as e:
            errors.append({"vehicle_id": vid, "row": row_num, "error": f"Assessment failed: {e}"})

    # ── Fleet summary ─────────────────────────────────────────────────────────
    recommended = [v for v in vehicles if v["recommended"]]
    not_recommended = [v for v in vehicles if not v["recommended"]]

    total_co2_saved     = sum(v["roi"]["co2_saved_kg_year"]     for v in recommended)
    total_annual_saving = sum(v["roi"]["annual_total_saving_inr"] for v in recommended)
    total_retrofit_cost = sum(v["battery"]["estimated_cost_inr"]  for v in recommended)
    avg_breakeven       = (sum(v["roi"]["breakeven_years"] for v in recommended) /
                           len(recommended)) if recommended else 0

    # Sort by score descending for priority ranking
    vehicles_sorted = sorted(vehicles, key=lambda x: x["score"], reverse=True)

    return {
        "summary": {
            "total_vehicles":       len(vehicles),
            "recommended_count":    len(recommended),
            "not_recommended_count":len(not_recommended),
            "parse_errors":         len(errors),
            "total_annual_co2_saved_kg":    round(total_co2_saved),
            "total_annual_fuel_saving_inr": round(total_annual_saving),
            "total_retrofit_investment_inr":round(total_retrofit_cost),
            "average_breakeven_years":      round(avg_breakeven, 1),
            "trees_equivalent_per_year":    int(total_co2_saved / 22),
        },
        "vehicles": vehicles_sorted,
        "errors":   errors,
    }


def _parse_row(row: dict) -> dict:
    def i(k, default=None):
        v = row.get(k, "").strip()
        if not v and default is not None:
            return default
        try:
            return int(float(v))
        except:
            raise ValueError(f"Column '{k}' has invalid integer value: '{v}'")

    def f(k, default=None):
        v = row.get(k, "").strip()
        if not v and default is not None:
            return default
        try:
            return float(v)
        except:
            raise ValueError(f"Column '{k}' has invalid float value: '{v}'")

    return {
        "vehicle_type":         row.get("vehicle_type", "Hatchback").strip(),
        "engine_cc":            i("engine_cc", 1000),
        "vehicle_age_years":    i("vehicle_age_years", 5),
        "chassis_condition":    i("chassis_condition", 7),
        "odometer_km":          i("odometer_km", 50000),
        "gearbox_type":         row.get("gearbox_type", "Manual").strip(),
        "weight_kg":            f("weight_kg", 900),
        "wheelbase_mm":         i("wheelbase_mm", 2400),
        "has_rust":             i("has_rust", 0),
        "electrical_condition": i("electrical_condition", 7),
        "brake_condition":      i("brake_condition", 7),
        "mileage_kmpl":         f("mileage_kmpl", 15),
        "target_range_km":      i("target_range_km", 100),
    }
