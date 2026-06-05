"""
app.py  —  RetrofitAI v2.0
FastAPI backend wiring all modules:
  feasibility_model | vehicle_physics | battery_optimizer
  compliance_checker | roi_calculator | explainable_ai
  wiring_harness | image_analyzer | fleet_analyzer | report_generator
"""

import os, uuid, logging
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from feasibility_model  import load_model, predict, train_model
from battery_optimizer  import optimize, battery_config_to_dict
from compliance_checker import check_compliance, compliance_to_dict
from vehicle_physics    import calculate as physics_calc, physics_to_dict
from roi_calculator     import calculate_roi, roi_to_dict
from explainable_ai     import (compute_feature_contributions, generate_explanation,
                                 generate_improvements, copilot_answer)
from wiring_harness     import generate_wiring_svg
from fleet_analyzer     import analyse_fleet_csv
from report_generator   import generate_report

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("RetrofitAI")

BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "..", "models", "retrofit_model.pkl")
DATA_PATH  = os.path.join(BASE, "..", "data",   "sample_vehicles.csv")
REPORT_DIR = "/tmp/reports" if os.environ.get("VERCEL") else os.path.join(BASE, "..", "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

# ── Model boot ────────────────────────────────────────────────────────────────
def get_model():
    if os.path.exists(MODEL_PATH):
        try:
            b = load_model(MODEL_PATH)
            log.info("Model loaded from disk ✓")
            return b
        except Exception as e:
            log.warning(f"Model load failed ({e}) — retraining …")
            os.remove(MODEL_PATH)
    log.info("Training model …")
    return train_model(DATA_PATH, MODEL_PATH)

model_bundle = get_model()

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="RetrofitAI v2", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

FRONTEND = os.path.join(BASE, "..", "frontend")
if os.path.exists(FRONTEND):
    app.mount("/ui", StaticFiles(directory=FRONTEND, html=True), name="ui")

# ── Schema ────────────────────────────────────────────────────────────────────
class VehicleInput(BaseModel):
    vehicle_type:         str   = Field("Hatchback")
    engine_cc:            int   = Field(1000, ge=50,  le=5000)
    vehicle_age_years:    int   = Field(5,    ge=0,   le=30)
    chassis_condition:    int   = Field(7,    ge=1,   le=10)
    odometer_km:          int   = Field(50000,ge=0,   le=500000)
    gearbox_type:         str   = Field("Manual")
    weight_kg:            float = Field(900,  ge=100, le=5000)
    wheelbase_mm:         int   = Field(2400, ge=1000,le=4000)
    has_rust:             int   = Field(0,    ge=0,   le=1)
    electrical_condition: int   = Field(7,    ge=1,   le=10)
    brake_condition:      int   = Field(7,    ge=1,   le=10)
    target_range_km:      int   = Field(100,  ge=30,  le=300)
    mileage_kmpl:         float = Field(15.0, ge=3,   le=50)
    annual_km:            int   = Field(15000,ge=1000,le=100000)

class CopilotInput(BaseModel):
    question: str
    context:  dict = {}

# ── Full assessment ───────────────────────────────────────────────────────────
def _full_assess(v: VehicleInput) -> dict:
    vd = v.model_dump()

    feasibility = predict(model_bundle, vd)
    bat_cfg     = optimize(v.vehicle_type, v.weight_kg, v.target_range_km, v.wheelbase_mm)
    battery     = battery_config_to_dict(bat_cfg)
    compliance  = compliance_to_dict(check_compliance(
        v.vehicle_type, bat_cfg.voltage_v, bat_cfg.pack_capacity_kwh,
        bat_cfg.motor["power_kw"], v.vehicle_age_years,
        bool(v.has_rust), v.brake_condition, v.electrical_condition
    ))
    physics = physics_to_dict(physics_calc(v.vehicle_type, v.weight_kg, v.target_range_km))
    roi     = roi_to_dict(calculate_roi(
        v.vehicle_type, v.mileage_kmpl,
        physics["specific_consumption_wh_km"],
        battery["estimated_cost_inr"], v.annual_km
    ))
    contributions = compute_feature_contributions(model_bundle, vd)
    explanation   = generate_explanation(
        feasibility["feasibility_score"], contributions, vd, physics, roi)
    improvements  = generate_improvements(vd, feasibility["feasibility_score"])

    wiring_svg = generate_wiring_svg(
        v.vehicle_type, bat_cfg.voltage_v,
        bat_cfg.motor["power_kw"], bat_cfg.motor["name"],
        bat_cfg.cell_chemistry
    )

    return {
        "status": "success",
        "vehicle": vd,
        "feasibility": feasibility,
        "battery":     battery,
        "compliance":  compliance,
        "physics":     physics,
        "roi":         roi,
        "xai": {
            "contributions": contributions,
            "explanation":   explanation,
            "improvements":  improvements,
        },
        "wiring_svg": wiring_svg,
    }

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "RetrofitAI v2 running. /ui for app, /docs for API."}

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0"}

@app.post("/api/assess")
def assess(v: VehicleInput):
    try:
        return _full_assess(v)
    except Exception as e:
        log.error(e)
        raise HTTPException(500, str(e))

@app.post("/api/report")
def report(v: VehicleInput):
    try:
        data = _full_assess(v)
        path = os.path.join(REPORT_DIR, f"retrofit_{uuid.uuid4().hex[:8]}.pdf")
        generate_report(path, data["vehicle"], data["feasibility"],
                        data["battery"], data["compliance"],
                        physics=data.get("physics"),
                        roi=data.get("roi"),
                        xai=data.get("xai"))
        return FileResponse(path, media_type="application/pdf",
                            filename="ev_retrofit_report.pdf")
    except Exception as e:
        log.error(e)
        raise HTTPException(500, str(e))

@app.post("/api/analyse-image")
async def analyse_image(file: UploadFile = File(...)):
    try:
        from image_analyzer import analyse_image as ai_analyse
        data = await file.read()
        mime = file.content_type or "image/jpeg"
        result = await ai_analyse(data, mime)
        return result
    except Exception as e:
        log.error(e)
        raise HTTPException(500, str(e))

@app.post("/api/wiring")
def wiring(v: VehicleInput):
    try:
        bat_cfg = optimize(v.vehicle_type, v.weight_kg, v.target_range_km, v.wheelbase_mm)
        svg = generate_wiring_svg(
            v.vehicle_type, bat_cfg.voltage_v,
            bat_cfg.motor["power_kw"], bat_cfg.motor["name"],
            bat_cfg.cell_chemistry
        )
        return Response(content=svg, media_type="image/svg+xml")
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/fleet")
async def fleet(file: UploadFile = File(...)):
    try:
        data = await file.read()
        result = analyse_fleet_csv(data)
        return result
    except Exception as e:
        log.error(e)
        raise HTTPException(500, str(e))

@app.post("/api/copilot")
def copilot(body: CopilotInput):
    try:
        answer = copilot_answer(body.question, body.context)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
