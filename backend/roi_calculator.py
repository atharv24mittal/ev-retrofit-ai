"""
roi_calculator.py
-----------------
Calculates retrofit ROI, fuel savings, and carbon impact.
All figures use India-specific data (CERC, MoRTH, IPCC AR6).
"""

from dataclasses import dataclass
from typing import Dict, List

# ── India-specific constants (2025) ──────────────────────────────────────────
PETROL_PRICE_INR_L   = 103.0     # ₹/litre (Delhi avg 2025)
ELECTRICITY_INR_KWH  = 8.5      # ₹/kWh (commercial tariff avg)
CO2_PETROL_KG_L      = 2.31     # kg CO2 per litre petrol (IPCC AR6)
CO2_GRID_KG_KWH      = 0.716    # kg CO2 per kWh (India grid 2024, CEA)
TREE_CO2_KG_YEAR     = 22.0     # kg CO2 absorbed per tree per year
ANNUAL_KM_DEFAULT    = 15000    # typical Indian commuter
MAINTENANCE_SAVING_INR_KM = 1.20  # EV saves ~₹1.20/km on maintenance (oil, clutch etc.)

@dataclass
class ROIResult:
    # Running costs
    petrol_cost_per_km:    float   # ₹/km before conversion
    ev_cost_per_km:        float   # ₹/km after conversion
    saving_per_km:         float   # ₹/km saved
    annual_km:             int

    # Annual financials
    annual_fuel_saving_inr:  float
    annual_maint_saving_inr: float
    annual_total_saving_inr: float

    # Retrofit investment
    retrofit_cost_inr:     int
    breakeven_years:       float
    five_year_net_inr:     float
    ten_year_net_inr:      float

    # Carbon
    petrol_co2_kg_year:    float
    ev_co2_kg_year:        float
    co2_saved_kg_year:     float
    trees_equivalent:      int
    lifetime_co2_saved_tonnes: float   # 10-year vehicle life

    # Yearly cash flow for chart
    yearly_cashflow: List[Dict]


def calculate_roi(
    vehicle_type:       str,
    mileage_kmpl:       float,      # original petrol mileage
    specific_wh_km:     float,      # from physics engine
    retrofit_cost_inr:  int,
    annual_km:          int = ANNUAL_KM_DEFAULT
) -> ROIResult:

    # ── Cost per km ───────────────────────────────────────────────────────────
    petrol_per_km  = PETROL_PRICE_INR_L / mileage_kmpl          # ₹/km
    ev_per_km      = (specific_wh_km / 1000) * ELECTRICITY_INR_KWH  # ₹/km
    saving_per_km  = petrol_per_km - ev_per_km

    # ── Annual savings ────────────────────────────────────────────────────────
    fuel_saving_yr  = saving_per_km * annual_km
    maint_saving_yr = MAINTENANCE_SAVING_INR_KM * annual_km
    total_saving_yr = fuel_saving_yr + maint_saving_yr

    # ── Breakeven ─────────────────────────────────────────────────────────────
    breakeven = retrofit_cost_inr / total_saving_yr if total_saving_yr > 0 else 999

    five_year_net  = (total_saving_yr * 5)  - retrofit_cost_inr
    ten_year_net   = (total_saving_yr * 10) - retrofit_cost_inr

    # ── Carbon impact ─────────────────────────────────────────────────────────
    litres_per_year    = annual_km / mileage_kmpl
    petrol_co2_yr      = litres_per_year * CO2_PETROL_KG_L
    kwh_per_year       = (specific_wh_km / 1000) * annual_km
    ev_co2_yr          = kwh_per_year * CO2_GRID_KG_KWH
    co2_saved_yr       = petrol_co2_yr - ev_co2_yr
    trees_eq           = int(co2_saved_yr / TREE_CO2_KG_YEAR)
    lifetime_saved_t   = (co2_saved_yr * 10) / 1000  # 10-year life

    # ── Yearly cash flow for chart ────────────────────────────────────────────
    yearly = []
    cumulative = -retrofit_cost_inr
    for yr in range(1, 11):
        cumulative += total_saving_yr
        yearly.append({
            "year": yr,
            "annual_saving": round(total_saving_yr),
            "cumulative_net": round(cumulative),
            "co2_saved_kg": round(co2_saved_yr * yr)
        })

    return ROIResult(
        petrol_cost_per_km    = round(petrol_per_km, 2),
        ev_cost_per_km        = round(ev_per_km, 2),
        saving_per_km         = round(saving_per_km, 2),
        annual_km             = annual_km,
        annual_fuel_saving_inr  = round(fuel_saving_yr),
        annual_maint_saving_inr = round(maint_saving_yr),
        annual_total_saving_inr = round(total_saving_yr),
        retrofit_cost_inr     = retrofit_cost_inr,
        breakeven_years       = round(breakeven, 1),
        five_year_net_inr     = round(five_year_net),
        ten_year_net_inr      = round(ten_year_net),
        petrol_co2_kg_year    = round(petrol_co2_yr, 1),
        ev_co2_kg_year        = round(ev_co2_yr, 1),
        co2_saved_kg_year     = round(co2_saved_yr, 1),
        trees_equivalent      = trees_eq,
        lifetime_co2_saved_tonnes = round(lifetime_saved_t, 2),
        yearly_cashflow       = yearly,
    )


def roi_to_dict(r: ROIResult) -> dict:
    return {k: getattr(r, k) for k in r.__dataclass_fields__}


if __name__ == "__main__":
    r = calculate_roi("Hatchback", mileage_kmpl=15, specific_wh_km=210,
                      retrofit_cost_inr=476600)
    print(f"Petrol cost   : ₹{r.petrol_cost_per_km}/km")
    print(f"EV cost       : ₹{r.ev_cost_per_km}/km")
    print(f"Annual saving : ₹{r.annual_total_saving_inr:,}")
    print(f"Breakeven     : {r.breakeven_years} years")
    print(f"10-yr net     : ₹{r.ten_year_net_inr:,}")
    print(f"CO2 saved/yr  : {r.co2_saved_kg_year} kg")
    print(f"Trees equiv   : {r.trees_equivalent}")
