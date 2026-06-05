"""
battery_optimizer.py
--------------------
Calculates optimal battery pack size, placement strategy,
motor recommendation, and estimated EV range for a retrofit vehicle.
"""

from dataclasses import dataclass
from typing import List, Dict

# ─── Constants ────────────────────────────────────────────────────────────────
ENERGY_PER_KM = 0.15          # kWh per km (average EV consumption)
SAFETY_MARGIN  = 0.85         # usable SoC window
BATTERY_DENSITY_KWH_PER_KG = 0.16   # typical LFP pack

# Motor options catalogue
MOTOR_CATALOGUE = [
    {"name": "BLDC 3kW Hub Motor",     "power_kw": 3,   "torque_nm": 15,  "suitable_for": ["Three-Wheeler"]},
    {"name": "BLDC 7.5kW Mid-Drive",   "power_kw": 7.5, "torque_nm": 35,  "suitable_for": ["Hatchback", "Three-Wheeler"]},
    {"name": "PMSM 15kW",              "power_kw": 15,  "torque_nm": 80,  "suitable_for": ["Hatchback", "Sedan"]},
    {"name": "PMSM 30kW",              "power_kw": 30,  "torque_nm": 150, "suitable_for": ["Sedan", "Van", "Pickup"]},
    {"name": "PMSM 50kW Dual",         "power_kw": 50,  "torque_nm": 250, "suitable_for": ["SUV", "Van", "Pickup"]},
]

# Battery placement strategies per vehicle type
PLACEMENT_STRATEGIES = {
    "Three-Wheeler": [
        "Rear cargo bay (primary pack)",
        "Under-seat secondary pack (optional)"
    ],
    "Hatchback": [
        "Under-floor (spare tyre well)",
        "Boot floor slab pack",
        "Rear seat underframe extension"
    ],
    "Sedan": [
        "Under-floor tunnel pack",
        "Boot floor primary pack",
        "Rear seat underframe module"
    ],
    "SUV": [
        "Flat floor skateboard pack (primary)",
        "Subframe-integrated side packs",
        "Roof-mounted auxiliary pack (last resort)"
    ],
    "Van": [
        "Underbody longitudinal packs (left & right rails)",
        "Partition wall-mounted auxiliary pack"
    ],
    "Pickup": [
        "Under-bed cross-member mounted pack",
        "Frame-rail integrated modules"
    ]
}


@dataclass
class BatteryConfig:
    pack_capacity_kwh: float
    voltage_v: int
    cell_chemistry: str
    estimated_range_km: float
    pack_weight_kg: float
    placement_zones: List[str]
    motor: Dict
    charger_type: str
    charge_time_hours: float
    estimated_cost_inr: int


def optimize(vehicle_type: str, weight_kg: float, target_range_km: int = 100,
             wheelbase_mm: int = 2400) -> BatteryConfig:
    """
    Returns an optimised battery configuration for the given vehicle.
    target_range_km: desired EV range in km (default 100)
    """
    # Required gross energy
    load_factor = _load_factor(vehicle_type)
    gross_kwh   = (target_range_km * ENERGY_PER_KM * load_factor) / SAFETY_MARGIN
    gross_kwh   = round(gross_kwh, 1)

    # Choose chemistry based on size
    if gross_kwh <= 10:
        chemistry, voltage = "LFP (Lithium Iron Phosphate)", 48
    elif gross_kwh <= 25:
        chemistry, voltage = "LFP (Lithium Iron Phosphate)", 72
    else:
        chemistry, voltage = "NMC (Nickel Manganese Cobalt)", 96

    pack_weight = round(gross_kwh / BATTERY_DENSITY_KWH_PER_KG, 1)
    actual_range = round((gross_kwh * SAFETY_MARGIN) / (ENERGY_PER_KM * load_factor))

    # Motor selection
    motor = _select_motor(vehicle_type, weight_kg)

    # Placement
    placements = PLACEMENT_STRATEGIES.get(vehicle_type, ["Under-floor primary pack"])

    # Charger
    if gross_kwh <= 10:
        charger = "Standard AC 3.3kW (domestic socket)"
        charge_h = round(gross_kwh / 3.3, 1)
    elif gross_kwh <= 25:
        charger = "AC 7.4kW Wallbox"
        charge_h = round(gross_kwh / 7.4, 1)
    else:
        charger = "AC 11kW Wallbox / DC 22kW Fast Charger"
        charge_h = round(gross_kwh / 11, 1)

    # Cost estimate (INR) — rough BOM
    cost_inr = int(gross_kwh * 18000 + motor["power_kw"] * 4000 + 35000)

    return BatteryConfig(
        pack_capacity_kwh=gross_kwh,
        voltage_v=voltage,
        cell_chemistry=chemistry,
        estimated_range_km=actual_range,
        pack_weight_kg=pack_weight,
        placement_zones=placements[:2],
        motor=motor,
        charger_type=charger,
        charge_time_hours=charge_h,
        estimated_cost_inr=cost_inr
    )


def _load_factor(vehicle_type: str) -> float:
    """Heavier / higher-drag vehicles consume more energy per km."""
    return {
        "Three-Wheeler": 0.7,
        "Hatchback":     1.0,
        "Sedan":         1.15,
        "SUV":           1.45,
        "Van":           1.60,
        "Pickup":        1.55
    }.get(vehicle_type, 1.0)


def _select_motor(vehicle_type: str, weight_kg: float) -> Dict:
    candidates = [m for m in MOTOR_CATALOGUE if vehicle_type in m["suitable_for"]]
    if not candidates:
        candidates = MOTOR_CATALOGUE   # fallback — all motors
    # Pick motor whose power is sufficient for weight
    required_kw = weight_kg * 0.025   # rule of thumb: 25W per kg
    for motor in sorted(candidates, key=lambda x: x["power_kw"]):
        if motor["power_kw"] >= required_kw:
            return motor
    return candidates[-1]   # most powerful available


def battery_config_to_dict(cfg: BatteryConfig) -> dict:
    return {
        "pack_capacity_kwh":  cfg.pack_capacity_kwh,
        "voltage_v":          cfg.voltage_v,
        "cell_chemistry":     cfg.cell_chemistry,
        "estimated_range_km": cfg.estimated_range_km,
        "pack_weight_kg":     cfg.pack_weight_kg,
        "placement_zones":    cfg.placement_zones,
        "motor":              cfg.motor,
        "charger_type":       cfg.charger_type,
        "charge_time_hours":  cfg.charge_time_hours,
        "estimated_cost_inr": cfg.estimated_cost_inr
    }
