"""
report_generator.py — RetrofitAI v2
Full professional PDF: Vehicle info, feasibility, physics, battery, ROI, carbon, compliance.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG     = colors.HexColor("#060B14")
C_CARD   = colors.HexColor("#0D1627")
C_ACCENT = colors.HexColor("#00E5FF")
C_GREEN  = colors.HexColor("#22C55E")
C_RED    = colors.HexColor("#EF4444")
C_AMBER  = colors.HexColor("#F59E0B")
C_PURPLE = colors.HexColor("#A855F7")
C_WHITE  = colors.white
C_DARK   = colors.HexColor("#0F172A")
C_MUTED  = colors.HexColor("#7A90B8")
C_LIGHT  = colors.HexColor("#F1F5F9")
C_BORDER = colors.HexColor("#1E3058")


def generate_report(
    output_path: str,
    vehicle_info: dict,
    feasibility: dict,
    battery: dict,
    compliance: dict,
    physics: dict = None,
    roi: dict = None,
    xai: dict = None,
) -> str:
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=1.5*cm, bottomMargin=1.8*cm,
        leftMargin=1.8*cm, rightMargin=1.8*cm
    )
    styles = getSampleStyleSheet()
    story  = []

    W = 17.4 * cm   # usable width

    def hline(col=C_BORDER, thick=0.5):
        return HRFlowable(width="100%", thickness=thick, color=col, spaceAfter=6, spaceBefore=4)

    def section(title, col=C_ACCENT):
        return Paragraph(
            f'<font color="#{col.hexval()[2:] if hasattr(col,"hexval") else "00E5FF"}">'
            f'<b>{title}</b></font>',
            ParagraphStyle("SH", parent=styles["Normal"],
                           fontSize=12, spaceBefore=14, spaceAfter=4,
                           fontName="Helvetica-Bold",
                           textColor=col)
        )

    def kv_table(rows, col_widths=None):
        """Two-column key-value table."""
        if col_widths is None:
            col_widths = [W * 0.42, W * 0.58]
        data = []
        for k, v, *rest in rows:
            val_col = rest[0] if rest else C_DARK
            data.append([
                Paragraph(f"<b>{k}</b>",
                    ParagraphStyle("k", fontSize=9, fontName="Helvetica-Bold", textColor=C_MUTED)),
                Paragraph(str(v),
                    ParagraphStyle("v", fontSize=9, fontName="Helvetica", textColor=val_col,
                                   alignment=TA_RIGHT))
            ])
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_LIGHT, C_WHITE]),
            ("GRID",          (0,0), (-1,-1), 0.3, C_BORDER),
            ("PADDING",       (0,0), (-1,-1), 5),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        return t

    def three_col_table(rows, widths=None):
        if widths is None:
            widths = [W*0.38, W*0.15, W*0.47]
        data = []
        for std, status, detail in rows:
            ok = "PASS" in str(status)
            scol = C_GREEN if ok else C_RED
            data.append([
                Paragraph(f"<b>{std}</b>",
                    ParagraphStyle("s", fontSize=8, fontName="Helvetica-Bold", textColor=C_DARK)),
                Paragraph(f"<b>{'✓ PASS' if ok else '✗ FAIL'}</b>",
                    ParagraphStyle("st", fontSize=8, fontName="Helvetica-Bold",
                                   textColor=scol, alignment=TA_CENTER)),
                Paragraph(str(detail),
                    ParagraphStyle("d", fontSize=7.5, fontName="Helvetica", textColor=C_MUTED,
                                   leading=10)),
            ])
        t = Table(data, colWidths=widths)
        t.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_LIGHT, C_WHITE]),
            ("GRID",          (0,0), (-1,-1), 0.3, C_BORDER),
            ("PADDING",       (0,0), (-1,-1), 5),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ]))
        return t

    # ════════════════════════════════════════════════════════════
    # HEADER BANNER
    # ════════════════════════════════════════════════════════════
    banner_data = [[
        Paragraph('<font color="#00E5FF"><b>⚡ RetrofitAI</b></font>',
                  ParagraphStyle("logo", fontSize=20, fontName="Helvetica-Bold",
                                 textColor=C_ACCENT)),
        Paragraph(
            f'<font color="#7A90B8">EV Retrofit Feasibility Report<br/>'
            f'Generated: {datetime.now().strftime("%d %B %Y, %I:%M %p")}</font>',
            ParagraphStyle("hdr", fontSize=9, fontName="Helvetica",
                           textColor=C_MUTED, alignment=TA_RIGHT))
    ]]
    banner = Table(banner_data, colWidths=[W*0.5, W*0.5])
    banner.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), C_BG),
        ("PADDING",     (0,0), (-1,-1), 10),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(banner)
    story.append(Spacer(1, 0.3*cm))

    # ════════════════════════════════════════════════════════════
    # SECTION 1: VEHICLE INFORMATION
    # ════════════════════════════════════════════════════════════
    story.append(section("1. Vehicle Information", C_ACCENT))
    story.append(hline(C_ACCENT, 1))
    vrows = [
        ["Vehicle Type",         vehicle_info.get("vehicle_type","—")],
        ["Engine Displacement",  f"{vehicle_info.get('engine_cc','—')} cc"],
        ["Vehicle Age",          f"{vehicle_info.get('vehicle_age_years','—')} years"],
        ["Odometer",             f"{vehicle_info.get('odometer_km',0):,} km"],
        ["Kerb Weight",          f"{vehicle_info.get('weight_kg','—')} kg"],
        ["Wheelbase",            f"{vehicle_info.get('wheelbase_mm','—')} mm"],
        ["Gearbox",              vehicle_info.get("gearbox_type","—")],
        ["Chassis Condition",    f"{vehicle_info.get('chassis_condition','—')}/10"],
        ["Electrical Condition", f"{vehicle_info.get('electrical_condition','—')}/10"],
        ["Brake Condition",      f"{vehicle_info.get('brake_condition','—')}/10"],
        ["Chassis Rust",         "Yes — Treatment Required" if vehicle_info.get("has_rust") else "No"],
        ["Mileage (Petrol)",     f"{vehicle_info.get('mileage_kmpl','—')} km/l"],
    ]
    story.append(kv_table(vrows))
    story.append(Spacer(1, 0.3*cm))

    # ════════════════════════════════════════════════════════════
    # SECTION 2: FEASIBILITY SCORE
    # ════════════════════════════════════════════════════════════
    story.append(section("2. AI Feasibility Assessment", C_GREEN))
    story.append(hline(C_GREEN, 1))

    score = feasibility.get("feasibility_score", 0)
    grade = feasibility.get("grade","—")
    rec   = feasibility.get("recommended", False)
    conf  = feasibility.get("confidence_percent", 0)
    scol  = C_GREEN if score >= 70 else (C_AMBER if score >= 50 else C_RED)

    score_data = [[
        Paragraph(f'<font color="#{("22C55E" if score>=70 else "F59E0B" if score>=50 else "EF4444")}">'
                  f'<b>{score}%</b></font>',
                  ParagraphStyle("sc", fontSize=36, fontName="Helvetica-Bold",
                                 textColor=scol, alignment=TA_CENTER)),
        Paragraph(
            f'<b>Grade: {grade}</b><br/>'
            f'<font color="{"#22C55E" if rec else "#EF4444"}"><b>'
            f'{"✅  RECOMMENDED FOR RETROFIT" if rec else "❌  NOT RECOMMENDED"}</b></font><br/>'
            f'<font color="#7A90B8">AI Model Confidence: {conf}%<br/>'
            f'Model: Random Forest + Gradient Boosting<br/>'
            f'Training: 60 records (30 real ARAI/MoRTH + 30 synthetic)</font>',
            ParagraphStyle("sd", fontSize=10, fontName="Helvetica",
                           textColor=C_DARK, leading=16))
    ]]
    score_t = Table(score_data, colWidths=[W*0.22, W*0.78])
    score_t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), C_LIGHT),
        ("GRID",        (0,0), (-1,-1), 0.5, C_BORDER),
        ("PADDING",     (0,0), (-1,-1), 12),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(score_t)

    # XAI explanation
    if xai and xai.get("explanation"):
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            f'<i><font color="#7A90B8">{xai["explanation"]}</font></i>',
            ParagraphStyle("exp", fontSize=8.5, fontName="Helvetica",
                           textColor=C_MUTED, leading=12, leftIndent=8)))

    story.append(Spacer(1, 0.3*cm))

    # ════════════════════════════════════════════════════════════
    # SECTION 3: PHYSICS ENGINE OUTPUT
    # ════════════════════════════════════════════════════════════
    if physics:
        story.append(section("3. Road-Load Physics Analysis  (SAE J1715 / IS 14665)", C_AMBER))
        story.append(hline(C_AMBER, 1))
        bd = physics.get("breakdown", {})

        # Two side-by-side mini-tables
        left = [
            ["Gross Vehicle Weight",  f"{bd.get('gross_mass_kg','—')} kg"],
            ["Rolling Resistance",    f"{physics.get('rolling_resistance_N','—')} N"],
            ["Aero Drag (80 km/h)",   f"{physics.get('aero_drag_N','—')} N"],
            ["Grade Climbing Force",  f"{physics.get('grade_force_N','—')} N ({bd.get('grade_percent',12)}%)"],
            ["Total Tractive Effort", f"{physics.get('total_peak_force_N','—')} N"],
            ["Cruise Power",          f"{physics.get('cruise_power_kw','—')} kW"],
        ]
        right = [
            ["Peak Power Required",   f"{physics.get('peak_power_kw','—')} kW"],
            ["Safety Margin",         "+20%"],
            ["Drivetrain Efficiency", "85%"],
            ["Motor Required",        f"{physics.get('recommended_motor_kw','—')} kW"],
            ["Rated Torque",          f"{physics.get('rated_torque_Nm','—')} Nm"],
            ["Wheel Torque",          f"{physics.get('wheel_torque_Nm','—')} Nm"],
        ]
        energy = [
            ["Energy Consumption",    f"{physics.get('specific_consumption_wh_km','—')} Wh/km"],
            ["India Drive Correction","+15% (stop-start traffic)"],
            ["Regen Braking Credit",  "−12%"],
            ["Pack Size (calculated)",f"{physics.get('pack_kwh_for_range','—')} kWh"],
            ["0–60 km/h (est.)",      f"{physics.get('zero_to_60_est_sec','—')} s"],
        ]

        def mini_kv(rows, w1=3.8*cm, w2=4.0*cm):
            data = [[
                Paragraph(f"<b>{k}</b>", ParagraphStyle("mk", fontSize=8, fontName="Helvetica-Bold", textColor=C_MUTED)),
                Paragraph(str(v), ParagraphStyle("mv", fontSize=8, fontName="Helvetica", textColor=C_DARK, alignment=TA_RIGHT))
            ] for k,v in rows]
            t = Table(data, colWidths=[w1, w2])
            t.setStyle(TableStyle([
                ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_LIGHT, C_WHITE]),
                ("GRID",          (0,0), (-1,-1), 0.3, C_BORDER),
                ("PADDING",       (0,0), (-1,-1), 4),
            ]))
            return t

        phys_grid = Table([[mini_kv(left), mini_kv(right)]], colWidths=[W*0.5, W*0.5])
        phys_grid.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),0)]))
        story.append(phys_grid)
        story.append(Spacer(1, 0.15*cm))
        story.append(mini_kv(energy, w1=6*cm, w2=W-6*cm))
        story.append(Paragraph(
            '<font color="#7A90B8"><i>Formula: F_total = F_rr + F_aero + F_grade  |  '
            'P = F×v / η  |  E(Wh/km) = P / v_ms / 3.6  ×  India factor  ×  regen factor</i></font>',
            ParagraphStyle("note", fontSize=7.5, fontName="Helvetica",
                           textColor=C_MUTED, leading=10, spaceBefore=4)))
        story.append(Spacer(1, 0.3*cm))

    # ════════════════════════════════════════════════════════════
    # SECTION 4: BATTERY CONFIGURATION
    # ════════════════════════════════════════════════════════════
    story.append(section("4. Recommended Battery Configuration", C_ACCENT))
    story.append(hline(C_ACCENT, 1))
    motor = battery.get("motor", {})
    brows = [
        ["Pack Capacity",       f"{battery.get('pack_capacity_kwh','—')} kWh"],
        ["Cell Chemistry",      battery.get("cell_chemistry","—")],
        ["Nominal Voltage",     f"{battery.get('voltage_v','—')} V"],
        ["Pack Weight",         f"{battery.get('pack_weight_kg','—')} kg"],
        ["Estimated Range",     f"{battery.get('estimated_range_km','—')} km"],
        ["Motor",               f"{motor.get('name','—')}"],
        ["Motor Power",         f"{motor.get('power_kw','—')} kW"],
        ["Motor Torque",        f"{motor.get('torque_nm','—')} Nm"],
        ["Charger Type",        battery.get("charger_type","—")],
        ["Charge Time (0→100%)", f"~{battery.get('charge_time_hours','—')} hrs"],
        ["Placement Zone 1",    (battery.get("placement_zones") or ["—"])[0]],
        ["Placement Zone 2",    (battery.get("placement_zones") or ["—","—"])[1] if len(battery.get("placement_zones",[]))>1 else "—"],
        ["Estimated Total Cost", f"₹{battery.get('estimated_cost_inr',0):,}"],
    ]
    story.append(kv_table(brows))
    story.append(Spacer(1, 0.3*cm))

    # ════════════════════════════════════════════════════════════
    # SECTION 5: ROI & CARBON IMPACT
    # ════════════════════════════════════════════════════════════
    if roi:
        story.append(section("5. ROI & Carbon Impact Analysis", C_GREEN))
        story.append(hline(C_GREEN, 1))

        roi_left = [
            ["Petrol Running Cost",        f"₹{roi.get('petrol_cost_per_km','—')}/km"],
            ["EV Running Cost",            f"₹{roi.get('ev_cost_per_km','—')}/km"],
            ["Saving per km",              f"₹{roi.get('saving_per_km','—')}/km"],
            ["Annual Fuel Saving",         f"₹{roi.get('annual_fuel_saving_inr',0):,}"],
            ["Annual Maint. Saving",       f"₹{roi.get('annual_maint_saving_inr',0):,}"],
            ["Total Annual Saving",        f"₹{roi.get('annual_total_saving_inr',0):,}"],
            ["Breakeven Period",           f"{roi.get('breakeven_years','—')} years"],
            ["5-Year Net Return",          f"₹{roi.get('five_year_net_inr',0):,}"],
            ["10-Year Net Return",         f"₹{roi.get('ten_year_net_inr',0):,}"],
        ]
        carbon_rows = [
            ["Petrol CO₂/year",            f"{roi.get('petrol_co2_kg_year','—')} kg"],
            ["EV Grid CO₂/year",           f"{roi.get('ev_co2_kg_year','—')} kg"],
            ["Net CO₂ Avoided/year",       f"{roi.get('co2_saved_kg_year','—')} kg"],
            ["Trees Equivalent/year",      f"{roi.get('trees_equivalent','—')} trees"],
            ["CO₂ Saved over 10 Years",    f"{roi.get('lifetime_co2_saved_tonnes','—')} tonnes"],
            ["Data Source",                "IPCC AR6 (2.31 kg CO₂/L) · CEA India 2024 (0.716 kg CO₂/kWh)"],
        ]

        roi_grid = Table([
            [kv_table(roi_left, [W*0.42, W*0.08]),
             kv_table(carbon_rows, [W*0.28, W*0.22])]
        ], colWidths=[W*0.5, W*0.5])
        roi_grid.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),0)]))
        story.append(roi_grid)

        # Yearly cashflow mini-table
        story.append(Spacer(1, 0.2*cm))
        yearly = roi.get("yearly_cashflow", [])
        if yearly:
            cf_header = [Paragraph(f"<b>Year {d['year']}</b>",
                ParagraphStyle("cfh", fontSize=7, fontName="Helvetica-Bold",
                               textColor=C_WHITE, alignment=TA_CENTER)) for d in yearly]
            cf_vals   = []
            for d in yearly:
                val = d.get("cumulative_net", 0)
                col_hex = "22C55E" if val >= 0 else "EF4444"
                cf_vals.append(Paragraph(
                    f'<font color="#{col_hex}"><b>{"+" if val>=0 else ""}₹{abs(val)//1000}k</b></font>',
                    ParagraphStyle("cfv", fontSize=7, fontName="Helvetica-Bold",
                                   alignment=TA_CENTER)))
            cw = W / len(yearly)
            cf_t = Table([[cf_header], [cf_vals]], colWidths=[cw]*len(yearly))
            cf_t.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0), C_DARK),
                ("BACKGROUND",  (0,1), (-1,1), C_LIGHT),
                ("GRID",        (0,0), (-1,-1), 0.3, C_BORDER),
                ("PADDING",     (0,0), (-1,-1), 4),
            ]))
            story.append(Paragraph("<b>10-Year Cumulative Net Return (₹)</b>",
                ParagraphStyle("cft", fontSize=8, fontName="Helvetica-Bold",
                               textColor=C_MUTED, spaceBefore=4, spaceAfter=3)))
            story.append(cf_t)
        story.append(Spacer(1, 0.3*cm))

    # ════════════════════════════════════════════════════════════
    # SECTION 6: COMPLIANCE
    # ════════════════════════════════════════════════════════════
    story.append(section("6. Preliminary Compliance Screening (AIS-038 / CMVR)", C_GREEN))
    story.append(hline(C_GREEN, 1))

    overall = compliance.get("overall_pass", False)
    ov_col  = "#22C55E" if overall else "#EF4444"
    story.append(Paragraph(
        f'<font color="{ov_col}"><b>'
        f'{"✅  Overall: PASS — Meets preliminary AIS-038 / CMVR screening" if overall else "❌  Overall: FAIL — Action required before homologation"}'
        f'</b></font>',
        ParagraphStyle("ov", fontSize=10, fontName="Helvetica-Bold",
                       textColor=C_GREEN if overall else C_RED,
                       spaceBefore=2, spaceAfter=6)))

    checks = compliance.get("checks", [])
    if checks:
        comp_rows = [(c["name"], "PASS" if c["passed"] else "FAIL", c["detail"]) for c in checks]
        story.append(three_col_table(comp_rows))

    warnings = compliance.get("warnings", [])
    if warnings:
        story.append(Spacer(1, 0.2*cm))
        for w in warnings:
            story.append(Paragraph(
                f'<font color="#F59E0B">⚠  {w}</font>',
                ParagraphStyle("w", fontSize=8.5, fontName="Helvetica",
                               textColor=C_AMBER, leftIndent=8, spaceBefore=2)))

    story.append(Spacer(1, 0.25*cm))

    # ════════════════════════════════════════════════════════════
    # SECTION 7: MANDATORY TESTS
    # ════════════════════════════════════════════════════════════
    story.append(section("7. Mandatory Tests Before Road Approval", C_AMBER))
    story.append(hline(C_AMBER, 0.5))
    tests = compliance.get("mandatory_tests", [])
    test_data = [[Paragraph(f"{i+1}. {t}",
        ParagraphStyle("ti", fontSize=8.5, fontName="Helvetica", textColor=C_DARK))]
        for i, t in enumerate(tests)]
    t = Table(test_data, colWidths=[W])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_LIGHT, C_WHITE]),
        ("GRID",          (0,0), (-1,-1), 0.3, C_BORDER),
        ("PADDING",       (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.25*cm))

    # ════════════════════════════════════════════════════════════
    # SECTION 8: RTO DOCUMENTS
    # ════════════════════════════════════════════════════════════
    story.append(section("8. Required RTO Documents", C_AMBER))
    story.append(hline(C_AMBER, 0.5))
    docs = compliance.get("rto_documents", [])
    doc_data = [[Paragraph(f"📄  {d}",
        ParagraphStyle("di", fontSize=8.5, fontName="Helvetica", textColor=C_DARK))]
        for d in docs]
    dt = Table(doc_data, colWidths=[W])
    dt.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_LIGHT, C_WHITE]),
        ("GRID",          (0,0), (-1,-1), 0.3, C_BORDER),
        ("PADDING",       (0,0), (-1,-1), 4),
    ]))
    story.append(dt)
    story.append(Spacer(1, 0.4*cm))

    # ════════════════════════════════════════════════════════════
    # FOOTER
    # ════════════════════════════════════════════════════════════
    story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER))
    story.append(Paragraph(
        "⚡ RetrofitAI  ·  India's AI-Powered EV Conversion Intelligence Platform  ·  ET AutoTech Hackathon 2026  ·  Team_24",
        ParagraphStyle("ft1", fontSize=8, fontName="Helvetica-Bold",
                       textColor=C_ACCENT, alignment=TA_CENTER, spaceBefore=4)))
    story.append(Paragraph(
        "This report is generated for advisory and decision-support purposes only. "
        "Preliminary compliance screening does not substitute for formal ARAI / iCAT / NATRIP homologation. "
        "Physics calculations follow SAE J1715 / IS 14665. Carbon data: IPCC AR6, CEA India 2024.",
        ParagraphStyle("ft2", fontSize=7, fontName="Helvetica",
                       textColor=C_MUTED, alignment=TA_CENTER, spaceBefore=2)))

    doc.build(story)
    return output_path
