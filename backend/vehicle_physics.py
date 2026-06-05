"""
vehicle_physics.py
------------------
Real automotive engineering calculations for EV retrofit sizing.
Every output here can be defended to an industry judge with a formula.

References:
  - SAE J1715  (EV energy consumption)
  - IS 14665   (Indian EV road load test)
  - Larminie & Lowry, "Electric Vehicle Technology Explained"
"""

import math
from dataclasses import dataclass
from typing import Dict

# ── Physical constants ────────────────────────────────────────────────────────
g           = 9.81          # m/s²
AIR_DENSITY = 1.225         # kg/m³ (sea level, 15°C)

# ── Vehicle archetype defaults (India-specific) ───────────────────────────────
ARCHETYPES = {
    "Three-Wheeler": dict(Cd=0.55, frontal_area=1.8,  Crr=0.015, payload_kg=300,  top_speed_kmh=60,  grade_pct=8),
    "Hatchback":     dict(Cd=0.32, frontal_area=2.0,  Crr=0.010, payload_kg=300,  top_speed_kmh=120, grade_pct=12),
    "Sedan":         dict(Cd=0.29, frontal_area=2.1,  Crr=0.010, payload_kg=350,  top_speed_kmh=140, grade_pct=12),
    "SUV":           dict(Cd=0.38, frontal_area=2.6,  Crr=0.012, payload_kg=500,  top_speed_kmh=160, grade_pct=15),
    "Van":           dict(Cd=0.45, frontal_area=3.2,  Crr=0.013, payload_kg=800,  top_speed_kmh=100, grade_pct=10),
    "Pickup":        dict(Cd=0.42, frontal_area=2.8,  Crr=0.012, payload_kg=1000, top_speed_kmh=120, grade_pct=10),
}


@dataclass
class PhysicsResult:
    # Forces
    rolling_resistance_N: float
    aero_drag_N: float
    grade_force_N: float
    total_peak_force_N: float

    # Power
    cruise_power_kw: float       # power at 80 km/h cruise
    peak_power_kw: float         # power for grade + speed simultaneously
    recommended_motor_kw: float  # with 20% safety factor
    rated_torque_Nm: float       # at motor shaft (pre-gearbox)
    wheel_torque_Nm: float       # at wheel

    # Energy
    specific_consumption_wh_km: float  # Wh per km
    pack_kwh_for_range: float          # pack capacity for target range
    usable_kwh: float                  # after 15% reserve

    # Acceleration
    zero_to_60_est_sec: float

    # Explanation dict for Explainable AI
    breakdown: Dict


def calculate(vehicle_type: str, kerb_mass_kg: float,
              target_range_km: int = 100,
              target_speed_kmh: float = 80.0) -> PhysicsResult:
    """
    Full road-load analysis following SAE J1715 / IS 14665.
    Returns every intermediate value so the UI can show 'why'.
    """
    arch = ARCHETYPES.get(vehicle_type, ARCHETYPES["Hatchback"])

    gross_mass   = kerb_mass_kg + arch["payload_kg"]   # GVW kg — for peak motor sizing
    energy_mass  = kerb_mass_kg + arch["payload_kg"] * 0.35  # typical occupant load for range
    Cd           = arch["Cd"]
    A            = arch["frontal_area"]                 # m²
    Crr          = arch["Crr"]
    grade        = arch["grade_pct"] / 100.0            # fraction
    v_ms         = target_speed_kmh / 3.6               # m/s
    v_top_ms     = arch["top_speed_kmh"] / 3.6

    # ── 1. Rolling resistance (peak GVW for motor sizing) ───────────────────
    F_rr = Crr * gross_mass * g                         # N

    # ── 2. Aerodynamic drag at cruise ────────────────────────────────────────
    F_aero = 0.5 * AIR_DENSITY * Cd * A * v_ms**2      # N

    # ── 3. Grade climbing force ──────────────────────────────────────────────
    F_grade = gross_mass * g * grade                    # N

    # ── 4. Total tractive effort ─────────────────────────────────────────────
    F_total = F_rr + F_aero + F_grade                  # N

    # ── 5. Cruise power ──────────────────────────────────────────────────────
    P_cruise_w = (F_rr + F_aero) * v_ms                # W  (flat road)

    # ── 6. Peak power: aero at top speed + grade at cruise (not simultaneous peak)
    F_peak_aero = 0.5 * AIR_DENSITY * Cd * A * v_top_ms**2
    F_peak_grade = gross_mass * g * grade              # grade at cruise speed
    F_peak      = F_rr + F_peak_aero + F_peak_grade * 0.6  # 60% grade factor (not full grade at top speed)
    P_peak_w    = F_peak * v_ms                        # W at cruise speed for grade scenario

    # ── 7. Motor sizing (20% safety margin, η=0.85) ──────────────────────────
    drivetrain_eta = 0.85
    P_motor_w      = (P_peak_w / drivetrain_eta) * 1.20
    P_motor_kw     = P_motor_w / 1000.0

    # ── 8. Torque ─────────────────────────────────────────────────────────────
    wheel_radius_m  = 0.29
    gear_ratio      = 8.0
    motor_rpm_max   = 5000
    omega_motor     = motor_rpm_max * 2 * math.pi / 60
    rated_torque_Nm = P_motor_w / omega_motor
    wheel_torque_Nm = rated_torque_Nm * gear_ratio * drivetrain_eta

    # ── 9. Specific energy consumption (Wh/km) — typical load, not GVW ─────
    # Wh/km = Power(W) / speed(m/s) / 3.6  [dimensional analysis: W/(m/s)/3.6 = Wh/km]
    F_rr_e   = Crr * energy_mass * g
    F_aero_e = 0.5 * AIR_DENSITY * Cd * A * v_ms**2
    P_e      = (F_rr_e + F_aero_e) * v_ms
    base_consumption = P_e / v_ms / 3.6              # Wh/km (correct formula)
    india_factor     = 1.15   # Indian stop-start + AC load
    regen_factor     = 0.88   # 12% regen braking recovery
    specific_wh_km   = base_consumption * india_factor * regen_factor

    # ── 10. Battery pack sizing ───────────────────────────────────────────────
    # 15% DoD reserve (SoC window 15%–100%)
    usable_fraction  = 0.85
    pack_kwh         = (specific_wh_km * target_range_km) / (1000 * usable_fraction)
    usable_kwh       = pack_kwh * usable_fraction

    # ── 11. 0–60 km/h estimate (simplified inertia model) ────────────────────
    # F_net = F_motor - F_rr  (aero negligible at low speed)
    F_net_low_speed = wheel_torque_Nm / wheel_radius_m - F_rr
    if F_net_low_speed > 0:
        accel_avg    = F_net_low_speed / gross_mass        # m/s²
        t_0_60       = (60 / 3.6) / accel_avg             # seconds
    else:
        t_0_60 = 99.0

    breakdown = {
        "gross_mass_kg":          round(gross_mass),
        "rolling_resistance_N":   round(F_rr, 1),
        "aero_drag_N_80kmh":      round(F_aero, 1),
        "grade_force_N":          round(F_grade, 1),
        "total_tractive_effort_N":round(F_total, 1),
        "cruise_power_kw":        round(P_cruise_w / 1000, 2),
        "peak_power_kw_required": round(P_peak_w / 1000, 2),
        "motor_kw_with_margin":   round(P_motor_kw, 2),
        "rated_torque_Nm":        round(rated_torque_Nm, 1),
        "wheel_torque_Nm":        round(wheel_torque_Nm, 1),
        "specific_Wh_km":         round(specific_wh_km, 1),
        "pack_kwh":               round(pack_kwh, 2),
        "india_drive_factor":     india_factor,
        "regen_braking_factor":   regen_factor,
        "drivetrain_efficiency":  drivetrain_eta,
        "grade_percent":          arch["grade_pct"],
        "Cd":                     Cd,
        "frontal_area_m2":        A,
        "Crr":                    Crr,
    }

    return PhysicsResult(
        rolling_resistance_N    = round(F_rr, 1),
        aero_drag_N             = round(F_aero, 1),
        grade_force_N           = round(F_grade, 1),
        total_peak_force_N      = round(F_total, 1),
        cruise_power_kw         = round(P_cruise_w / 1000, 2),
        peak_power_kw           = round(P_peak_w / 1000, 2),
        recommended_motor_kw    = round(P_motor_kw, 2),
        rated_torque_Nm         = round(rated_torque_Nm, 1),
        wheel_torque_Nm         = round(wheel_torque_Nm, 1),
        specific_consumption_wh_km = round(specific_wh_km, 1),
        pack_kwh_for_range      = round(pack_kwh, 2),
        usable_kwh              = round(usable_kwh, 2),
        zero_to_60_est_sec      = round(min(t_0_60, 99), 1),
        breakdown               = breakdown,
    )


def physics_to_dict(r: PhysicsResult) -> dict:
    return {k: getattr(r, k) for k in r.__dataclass_fields__}


if __name__ == "__main__":
    r = calculate("Hatchback", 840, target_range_km=120)
    print(f"Motor required : {r.recommended_motor_kw:.1f} kW")
    print(f"Torque (motor) : {r.rated_torque_Nm:.1f} Nm")
    print(f"Torque (wheel) : {r.wheel_torque_Nm:.1f} Nm")
    print(f"Pack size      : {r.pack_kwh_for_range:.1f} kWh")
    print(f"Wh/km          : {r.specific_consumption_wh_km:.1f}")
    print(f"0-60 km/h      : {r.zero_to_60_est_sec:.1f} s")
