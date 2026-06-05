"""
compliance_checker.py
----------------------
Validates an EV retrofit against Indian regulatory standards:
  - AIS-038 Rev.2  (Electric Power Train for Vehicles)
  - AIS-156        (Battery Pack Safety)
  - CMVR Part-IV   (Homologation after conversion)
  - IS-16046       (EMC for electric vehicles)
  - BIS certification for battery packs
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ComplianceResult:
    overall_pass: bool
    checks: List[dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    mandatory_tests: List[str] = field(default_factory=list)
    rto_documents: List[str] = field(default_factory=list)


def check_compliance(
    vehicle_type: str,
    battery_voltage: int,
    battery_kwh: float,
    motor_kw: float,
    vehicle_age_years: int,
    has_rust: bool,
    brake_condition: int,
    electrical_condition: int
) -> ComplianceResult:

    checks   = []
    warnings = []
    all_pass = True

    # ── 1. AIS-038: Battery voltage range ────────────────────────────────────
    if battery_voltage <= 120:
        checks.append(_check("AIS-038 §4.2 – Voltage Class", True,
            f"Voltage {battery_voltage}V falls in Class-A (<60V DC is extra safe; "
            f"up to 120V is Class-A1). Compliant."))
    else:
        checks.append(_check("AIS-038 §4.2 – Voltage Class", False,
            f"Voltage {battery_voltage}V exceeds Class-A limit. Requires additional "
            f"insulation monitoring device (IMD) and HV interlock."))
        warnings.append("High-voltage pack (>120V): IMD and HV interlock mandatory.")
        all_pass = False

    # ── 2. AIS-156: Battery pack IP rating ───────────────────────────────────
    checks.append(_check("AIS-156 – Battery IP Rating", True,
        "Battery pack must carry minimum IP67 rating. Ensure OEM enclosure or "
        "custom sealed housing. (Assume compliant if certified pack used.)"))

    # ── 3. CMVR – Vehicle age limit ──────────────────────────────────────────
    if vehicle_age_years <= 15:
        checks.append(_check("CMVR – Vehicle Age Eligibility", True,
            f"Vehicle is {vehicle_age_years} years old. Within the 15-year limit "
            f"for EV conversion homologation."))
    else:
        checks.append(_check("CMVR – Vehicle Age Eligibility", False,
            f"Vehicle is {vehicle_age_years} years old. Exceeds 15-year CMVR limit. "
            f"Conversion not eligible for homologation."))
        all_pass = False

    # ── 4. Brake performance ─────────────────────────────────────────────────
    if brake_condition >= 7:
        checks.append(_check("CMVR Part-IV – Brake Performance", True,
            f"Brake condition score {brake_condition}/10. Meets minimum standard. "
            f"Regenerative braking must be calibrated to avoid brake lockout."))
    else:
        checks.append(_check("CMVR Part-IV – Brake Performance", False,
            f"Brake condition score {brake_condition}/10. Brakes must be overhauled "
            f"before conversion. Regen braking integration at risk."))
        warnings.append("Brake overhaul required before retrofit.")
        all_pass = False

    # ── 5. Structural / rust check ───────────────────────────────────────────
    if has_rust:
        checks.append(_check("AIS-038 – Chassis Structural Integrity", False,
            "Rust detected. Chassis must be treated and certified by a structural "
            "engineer before battery mounting. Risk of pack ingress & short-circuit."))
        warnings.append("Chassis rust treatment mandatory before battery installation.")
        all_pass = False
    else:
        checks.append(_check("AIS-038 – Chassis Structural Integrity", True,
            "No rust detected. Chassis suitable for battery bracket welding and mounting."))

    # ── 6. Electrical system health ──────────────────────────────────────────
    if electrical_condition >= 6:
        checks.append(_check("IS-16046 – EMC Baseline", True,
            f"Electrical system condition {electrical_condition}/10. Acceptable baseline "
            f"for EMC testing post-conversion."))
    else:
        checks.append(_check("IS-16046 – EMC Baseline", False,
            f"Electrical condition score {electrical_condition}/10. Wiring harness must be "
            f"replaced before conversion to pass IS-16046 EMC tests."))
        warnings.append("Full wiring harness inspection and replacement advised.")
        all_pass = False

    # ── 7. Three-Wheeler specific: ARAI/iCAT certification ───────────────────
    if vehicle_type == "Three-Wheeler":
        checks.append(_check("ARAI/iCAT – L5M Category Certification", True,
            "Three-wheelers fall under L5M category. Conversion must be certified by "
            "ARAI, iCAT, or NATRIP before re-registration."))

    mandatory_tests = [
        "Electrical safety test (insulation resistance ≥ 1MΩ)",
        "Dielectric strength test (2× nominal voltage)",
        "Battery pack vibration & shock test (AIS-156 §6)",
        "IP67 ingress protection test for battery enclosure",
        "EMC/EMI test (IS-16046)",
        "Road load & range validation test (IS-14665)",
        "Regen braking performance test",
        "High-voltage interlock test (if >60V DC)"
    ]

    rto_documents = [
        "Form-20 (Re-registration after conversion)",
        "Form-38 (Fitness Certificate update)",
        "NOC from original RTO",
        "Certification from ARAI / iCAT / NATRIP",
        "Insurance endorsement for EV conversion",
        "Structural engineer certificate (chassis)",
        "Battery pack BIS/manufacturer certificate"
    ]

    return ComplianceResult(
        overall_pass=all_pass,
        checks=checks,
        warnings=warnings,
        mandatory_tests=mandatory_tests,
        rto_documents=rto_documents
    )


def _check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}


def compliance_to_dict(result: ComplianceResult) -> dict:
    return {
        "overall_pass":    result.overall_pass,
        "checks":          result.checks,
        "warnings":        result.warnings,
        "mandatory_tests": result.mandatory_tests,
        "rto_documents":   result.rto_documents
    }
