/* ═══════════════════════════════════════════════════════════════════════════
   RetrofitAI v2 — script.js
   Handles: assessment, image upload, fleet, ROI chart, carbon chart,
            XAI feature bars, AI Copilot, wiring modal, result tabs
═══════════════════════════════════════════════════════════════════════════ */

const API = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") ? "http://localhost:8000" : window.location.origin;
let lastAssessment = {};

/* ── Tab switching ─────────────────────────────────────────────────────────── */
function showTab(tab) {
  document.getElementById("tab-single").classList.toggle("hidden", tab !== "single");
  document.getElementById("tab-fleet").classList.toggle("hidden", tab !== "fleet");
  document.querySelectorAll(".nav-tab").forEach((b, i) => {
    b.classList.toggle("active", (i === 0 && tab === "single") || (i === 1 && tab === "fleet"));
  });
  if (tab === "fleet") document.getElementById("fleet-section").scrollIntoView({ behavior: "smooth" });
}

/* ── Result sub-tabs ───────────────────────────────────────────────────────── */
function showResultTab(name) {
  document.querySelectorAll(".rtab-content").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".rtab").forEach(el => el.classList.remove("active"));
  document.getElementById("rtab-" + name).classList.add("active");
  const idx = ["physics","battery","roi","carbon","compliance","xai"].indexOf(name);
  document.querySelectorAll(".rtab")[idx]?.classList.add("active");
}

/* ── Rust toggle ───────────────────────────────────────────────────────────── */
document.getElementById("has_rust").addEventListener("change", function () {
  document.getElementById("rust_label").textContent = this.checked ? "⚠️ Rust Detected" : "No Rust Detected";
});

/* ── Sample vehicle ────────────────────────────────────────────────────────── */
function loadSample() {
  setVal("vehicle_type", "Hatchback");
  setVal("engine_cc", 1100); setVal("mileage_kmpl", 16);
  setVal("vehicle_age_years", 6); setVal("odometer_km", 62000);
  setVal("weight_kg", 840); setVal("wheelbase_mm", 2435);
  setVal("gearbox_type", "Manual"); setVal("annual_km", 15000);
  setSlider("chassis_condition", "chassis_val", 8);
  setSlider("electrical_condition", "elec_val", 7);
  setSlider("brake_condition", "brake_val", 8);
  setSlider("target_range_km", "range_val", 120);
  document.getElementById("has_rust").checked = false;
  document.getElementById("rust_label").textContent = "No Rust Detected";
}
function setVal(id, v) { document.getElementById(id).value = v; }
function setSlider(id, badge, v) {
  document.getElementById(id).value = v;
  document.getElementById(badge).textContent = v;
}

/* ── Build payload ─────────────────────────────────────────────────────────── */
function buildPayload() {
  return {
    vehicle_type: g("vehicle_type"), engine_cc: +g("engine_cc"),
    vehicle_age_years: +g("vehicle_age_years"), chassis_condition: +g("chassis_condition"),
    odometer_km: +g("odometer_km"), gearbox_type: g("gearbox_type"),
    weight_kg: +g("weight_kg"), wheelbase_mm: +g("wheelbase_mm"),
    has_rust: document.getElementById("has_rust").checked ? 1 : 0,
    electrical_condition: +g("electrical_condition"), brake_condition: +g("brake_condition"),
    target_range_km: +g("target_range_km"), mileage_kmpl: +g("mileage_kmpl"),
    annual_km: +g("annual_km"),
  };
}
function g(id) { return document.getElementById(id).value; }

/* ── Image upload ──────────────────────────────────────────────────────────── */
async function handleImageUpload(input) {
  if (!input.files[0]) return;
  const file = input.files[0];
  const reader = new FileReader();
  reader.onload = e => {
    document.getElementById("imagePreview").src = e.target.result;
    document.getElementById("imagePreviewWrap").classList.remove("hidden");
  };
  reader.readAsDataURL(file);

  showLoader("AI inspecting vehicle photo…");
  const form = new FormData();
  form.append("file", file);
  try {
    const res = await fetch(`${API}/api/analyse-image`, { method: "POST", body: form });
    const data = await res.json();
    hideLoader();
    applyImageResult(data);
  } catch (e) {
    hideLoader();
    document.getElementById("imageResult").innerHTML =
      `<div style="color:var(--amber);font-size:.82rem">⚠️ Image analysis unavailable — fill form manually.<br/><small>${e.message}</small></div>`;
  }
}

function applyImageResult(data) {
  // Pre-fill form
  if (data.vehicle_type) setVal("vehicle_type", data.vehicle_type);
  if (data.estimated_age_years) setVal("vehicle_age_years", data.estimated_age_years);
  if (data.estimated_weight_kg) setVal("weight_kg", data.estimated_weight_kg);
  if (data.has_rust !== undefined) {
    document.getElementById("has_rust").checked = !!data.has_rust;
    document.getElementById("rust_label").textContent = data.has_rust ? "⚠️ Rust Detected" : "No Rust Detected";
  }
  if (data.chassis_condition) setSlider("chassis_condition", "chassis_val", data.chassis_condition);
  if (data.electrical_condition) setSlider("electrical_condition", "elec_val", data.electrical_condition);
  if (data.brake_condition) setSlider("brake_condition", "brake_val", data.brake_condition);

  const conf = data.confidence ? `${Math.round(data.confidence * 100)}%` : "N/A";
  const rust = data.rust_severity || (data.has_rust ? "detected" : "none");
  const irows = [
    ["Detected Type", data.vehicle_type || "—"],
    ["Rust", rust],
    ["Chassis", `${data.chassis_condition || "—"}/10`],
    ["Bay Space", `${data.engine_bay_space_rating || "—"}/10`],
    ["AI Confidence", conf],
  ];
  document.getElementById("imageResult").innerHTML =
    `<div style="color:var(--accent);font-size:.78rem;font-weight:700;margin-bottom:.5rem">
       ${data.image_analysis_success ? "✅ AI Auto-filled form" : "⚠️ Defaults used"}
     </div>` +
    irows.map(([k, v]) => `<div class="ir-row"><span class="ir-key">${k}</span><span class="ir-val">${v}</span></div>`).join("") +
    (data.ai_notes ? `<div style="margin-top:.5rem;font-size:.78rem;color:var(--muted)">${data.ai_notes}</div>` : "");
}

/* ── Run assessment ────────────────────────────────────────────────────────── */
async function runAssessment() {
  const payload = buildPayload();
  const msgs = [
    "Running road-load physics (SAE J1715)…",
    "Sizing motor from tractive effort…",
    "Calculating battery pack from Wh/km…",
    "Running ML feasibility model…",
    "Checking AIS-038 / CMVR compliance…",
    "Computing ROI and carbon impact…",
    "Running XAI feature analysis…",
    "Generating wiring harness…",
  ];
  showLoader(msgs[0]);
  let mi = 0;
  const t = setInterval(() => { mi++; if (mi < msgs.length) document.getElementById("loaderText").textContent = msgs[mi]; }, 700);

  try {
    const res = await fetch(`${API}/api/assess`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "API error"); }
    const data = await res.json();
    clearInterval(t); hideLoader();
    lastAssessment = data;
    renderResults(data);
  } catch (e) {
    clearInterval(t); hideLoader();
    alert("Error: " + e.message + "\n\nMake sure the backend is running:\ncd backend && python app.py");
  }
}

/* ── Download PDF ──────────────────────────────────────────────────────────── */
async function downloadReport() {
  showLoader("Generating PDF report…");
  try {
    const res = await fetch(`${API}/api/report`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });
    if (!res.ok) throw new Error("Failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "ev_retrofit_report.pdf"; a.click();
    URL.revokeObjectURL(url);
  } catch (e) { alert("PDF error: " + e.message); }
  finally { hideLoader(); }
}

/* ── Wiring modal ──────────────────────────────────────────────────────────── */
function showWiring() {
  const svg = lastAssessment.wiring_svg;
  if (!svg) { alert("Run an assessment first."); return; }
  document.getElementById("wiringSvgContainer").innerHTML = svg;
  document.getElementById("wiringModal").classList.remove("hidden");
}
function closeWiring() { document.getElementById("wiringModal").classList.add("hidden"); }

/* ── Render all results ────────────────────────────────────────────────────── */
function renderResults(data) {
  const { feasibility, battery, compliance, physics, roi, xai } = data;
  document.getElementById("results").classList.remove("hidden");
  document.getElementById("results").scrollIntoView({ behavior: "smooth" });
  showResultTab("physics");

  // ── Score ring ──────────────────────────────────────────────────────────
  const score = feasibility.feasibility_score;
  const ringColor = score >= 70 ? "#22C55E" : score >= 50 ? "#F59E0B" : "#EF4444";
  const ring = document.getElementById("ringFill");
  ring.style.stroke = ringColor;
  ring.style.strokeDashoffset = 327 - (score / 100) * 327;
  document.getElementById("scoreNum").textContent = score + "%";
  document.getElementById("scoreGrade").textContent = feasibility.grade;
  document.getElementById("scoreVerdict").textContent = feasibility.recommended ? "✅ RECOMMENDED FOR RETROFIT" : "❌ NOT RECOMMENDED";
  document.getElementById("scoreVerdict").style.color = ringColor;
  document.getElementById("scoreConf").textContent = `AI confidence: ${feasibility.confidence_percent}%`;
  document.getElementById("aiExplanation").textContent = xai.explanation;

  // ── Physics tab ─────────────────────────────────────────────────────────
  const bd = physics.breakdown || {};
  document.getElementById("physicsForces").innerHTML = rows([
    ["Gross Vehicle Weight",  `${bd.gross_mass_kg || "—"} kg`],
    ["Rolling Resistance",    `${physics.rolling_resistance_N} N`],
    ["Aero Drag (80 km/h)",   `${physics.aero_drag_N} N`],
    ["Grade Climbing Force",  `${physics.grade_force_N} N (${bd.grade_percent || 12}%)`],
    ["Total Tractive Effort", `${physics.total_peak_force_N} N`],
  ]);
  document.getElementById("physicsPower").innerHTML = rows([
    ["Cruise Power (80 km/h)", `${physics.cruise_power_kw} kW`],
    ["Peak Power Required",    `${physics.peak_power_kw} kW`],
    ["Safety Margin",          "+20%"],
    ["Drivetrain Efficiency",  "85%"],
    ["Motor Power Required",   `${physics.recommended_motor_kw} kW`],
  ]);
  document.getElementById("physicsMotor").innerHTML = rows([
    ["Motor Power",          `${physics.recommended_motor_kw} kW`],
    ["Rated Torque",         `${physics.rated_torque_Nm} Nm`],
    ["Wheel Torque",         `${physics.wheel_torque_Nm} Nm`],
    ["Energy Consumption",   `${physics.specific_consumption_wh_km} Wh/km`],
    ["0–60 km/h (est.)",     `${physics.zero_to_60_est_sec} s`],
  ]);
  document.getElementById("gradeVal").textContent = bd.grade_percent || 12;

  // ── Battery tab ─────────────────────────────────────────────────────────
  document.getElementById("batterySpec").innerHTML = rows([
    ["Pack Capacity",    `${battery.pack_capacity_kwh} kWh`],
    ["Chemistry",        battery.cell_chemistry],
    ["Nominal Voltage",  `${battery.voltage_v} V`],
    ["Pack Weight",      `${battery.pack_weight_kg} kg`],
    ["Est. Range",       `${battery.estimated_range_km} km`],
  ]);
  const zones = battery.placement_zones || [];
  document.getElementById("batteryPlacement").innerHTML = rows(
    zones.map((z, i) => [`Zone ${i + 1}`, z])
      .concat([["Motor", battery.motor?.name || "—"], ["Motor Power", `${battery.motor?.power_kw} kW`], ["Torque", `${battery.motor?.torque_nm} Nm`]])
  );
  document.getElementById("batteryCharging").innerHTML = rows([
    ["Charger Type",    battery.charger_type],
    ["Charge Time",     `~${battery.charge_time_hours} hrs`],
    ["Est. Total Cost", `₹${(battery.estimated_cost_inr || 0).toLocaleString("en-IN")}`],
  ]);

  // ── ROI tab ─────────────────────────────────────────────────────────────
  document.getElementById("roiSaving").textContent  = `₹${(roi.annual_total_saving_inr || 0).toLocaleString("en-IN")}`;
  document.getElementById("roiBreakeven").textContent = `${roi.breakeven_years} yrs`;
  document.getElementById("roi10yr").textContent = `₹${(roi.ten_year_net_inr || 0).toLocaleString("en-IN")}`;
  document.getElementById("roiCost").innerHTML = rows([
    ["Petrol Cost",          `₹${roi.petrol_cost_per_km}/km`],
    ["EV Cost",              `₹${roi.ev_cost_per_km}/km`],
    ["Saving per km",        `₹${roi.saving_per_km}/km`],
    ["Annual Fuel Saving",   `₹${(roi.annual_fuel_saving_inr || 0).toLocaleString("en-IN")}`],
    ["Annual Maint. Saving", `₹${(roi.annual_maint_saving_inr || 0).toLocaleString("en-IN")}`],
    ["5-Year Net",           `₹${(roi.five_year_net_inr || 0).toLocaleString("en-IN")}`],
  ]);
  renderCashflowChart(roi.yearly_cashflow || [], "cashflowChart", "cumulative_net", "#22C55E", "#EF4444");

  // ── Carbon tab ──────────────────────────────────────────────────────────
  document.getElementById("co2Saved").textContent   = roi.co2_saved_kg_year;
  document.getElementById("treesEq").textContent    = roi.trees_equivalent;
  document.getElementById("lifetimeCo2").textContent = roi.lifetime_co2_saved_tonnes;
  document.getElementById("carbonDetail").innerHTML = rows([
    ["Petrol CO₂/year",  `${roi.petrol_co2_kg_year} kg`],
    ["EV Grid CO₂/year", `${roi.ev_co2_kg_year} kg`],
    ["CO₂ Saved/year",   `${roi.co2_saved_kg_year} kg`],
    ["Trees Equivalent", `${roi.trees_equivalent} trees/yr`],
    ["10-Year Total",    `${roi.lifetime_co2_saved_tonnes} tonnes`],
  ]);
  renderCashflowChart(roi.yearly_cashflow || [], "carbonChart", "co2_saved_kg", "#22C55E", "#22C55E");

  // ── Compliance tab ──────────────────────────────────────────────────────
  const overall = compliance.overall_pass;
  const co = document.getElementById("complianceOverall");
  co.className = "compliance-overall " + (overall ? "pass" : "fail");
  co.textContent = overall ? "✅ Overall Compliance: PASS — Vehicle meets all AIS-038 / CMVR requirements"
                           : "❌ Overall Compliance: FAIL — Action required before submission for homologation";

  let tbl = `<div class="comp-header"><div>Standard</div><div>Status</div><div>Finding</div></div>`;
  (compliance.checks || []).forEach(c => {
    tbl += `<div class="comp-row">
      <div class="comp-name">${c.name}</div>
      <div class="${c.passed ? "comp-pass" : "comp-fail"}">${c.passed ? "✅ PASS" : "❌ FAIL"}</div>
      <div class="comp-detail">${c.detail}</div>
    </div>`;
  });
  (compliance.warnings || []).forEach(w => {
    tbl += `<div class="warning-strip">⚠️ ${w}</div>`;
  });
  document.getElementById("complianceTable").innerHTML = tbl;

  const docs = compliance.rto_documents || [];
  document.getElementById("complianceDocs").innerHTML =
    `<h4>Required RTO Documents (${docs.length})</h4><ul>` +
    docs.map(d => `<li>📄 ${d}</li>`).join("") + `</ul>`;

  // ── XAI tab ─────────────────────────────────────────────────────────────
  const contribs = xai.contributions || [];
  const maxAbs = Math.max(...contribs.map(c => Math.abs(c.contribution)), 1);
  document.getElementById("featureChart").innerHTML = contribs.slice(0, 8).map(c => {
    const pct = Math.round((Math.abs(c.contribution) / maxAbs) * 100);
    const col = c.contribution >= 0 ? "#22C55E" : "#EF4444";
    const sign = c.contribution >= 0 ? "+" : "";
    return `<div class="feat-row">
      <div class="feat-name">${c.display_name}</div>
      <div class="feat-bar-wrap">
        <div class="feat-bar" style="width:${pct}%;background:${col}"></div>
      </div>
      <div class="feat-val" style="color:${col}">${sign}${c.contribution.toFixed(1)}</div>
    </div>`;
  }).join("");

  const imps = xai.improvements || [];
  document.getElementById("improvementsBox").innerHTML = imps.length === 0
    ? `<h4 style="color:var(--green)">✅ No major improvements needed</h4>`
    : `<h4>🔧 How to Improve Your Score</h4>` +
      imps.map(imp => `<div class="imp-item">
        <div><strong>${imp.field.replace(/_/g," ")}</strong>
          <span class="imp-priority ${imp.priority}">${imp.priority}</span>
        </div>
        <div class="imp-advice">${imp.advice}</div>
      </div>`).join("");
}

/* ── Charts ─────────────────────────────────────────────────────────────────── */
function renderCashflowChart(data, containerId, key, posColor, negColor) {
  const container = document.getElementById(containerId);
  if (!data.length) { container.innerHTML = "<p style='color:var(--muted);font-size:.8rem'>No data</p>"; return; }
  const vals = data.map(d => d[key]);
  const max = Math.max(...vals.map(Math.abs), 1);

  container.innerHTML = data.map(d => {
    const val = d[key];
    const pct = Math.round((Math.abs(val) / max) * 100);
    const color = val >= 0 ? posColor : negColor;
    const label = typeof val === "number" && Math.abs(val) >= 1000
      ? (val >= 0 ? "+" : "") + (val / 1000).toFixed(1) + "k"
      : (val >= 0 ? "+" : "") + val;
    return `<div class="cf-bar-wrap">
      <div class="cf-val" style="color:${color};font-size:.65rem">${label}</div>
      <div class="cf-bar" style="height:${Math.max(pct, 4)}%;background:${color};opacity:.85"></div>
      <div class="cf-label">Yr ${d.year}</div>
    </div>`;
  }).join("");
}

/* ── AI Copilot ──────────────────────────────────────────────────────────────── */
async function sendCopilot() {
  const input = document.getElementById("copilotInput");
  const q = input.value.trim();
  if (!q) return;
  input.value = "";

  const msgs = document.getElementById("copilotMessages");
  msgs.innerHTML += `<div class="msg-user">${q}</div>`;
  msgs.scrollTop = msgs.scrollHeight;

  try {
    const res = await fetch(`${API}/api/copilot`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q, context: lastAssessment }),
    });
    const data = await res.json();
    msgs.innerHTML += `<div class="msg-bot">🤖 ${data.answer}</div>`;
  } catch (e) {
    msgs.innerHTML += `<div class="msg-bot" style="color:var(--amber)">⚠️ Backend unavailable — start the server and try again.</div>`;
  }
  msgs.scrollTop = msgs.scrollHeight;
}

/* ── Fleet ───────────────────────────────────────────────────────────────────── */
async function handleFleetUpload(input) {
  if (!input.files[0]) return;
  showLoader("Analysing fleet — running AI on each vehicle…");
  const form = new FormData();
  form.append("file", input.files[0]);
  try {
    const res = await fetch(`${API}/api/fleet`, { method: "POST", body: form });
    if (!res.ok) throw new Error("Fleet API error");
    const data = await res.json();
    hideLoader();
    renderFleet(data);
  } catch (e) {
    hideLoader();
    alert("Fleet error: " + e.message);
  }
}

function renderFleet(data) {
  document.getElementById("fleetResults").classList.remove("hidden");
  const s = data.summary;

  const cards = [
    ["Total Vehicles",           s.total_vehicles,                             "var(--accent)"],
    ["Retrofit Ready",           s.recommended_count,                          "var(--green)"],
    ["Not Feasible",             s.not_recommended_count,                      "var(--red)"],
    ["Annual CO₂ Saved (kg)",    (s.total_annual_co2_saved_kg||0).toLocaleString("en-IN"), "var(--green)"],
    ["Trees Equivalent",         s.trees_equivalent_per_year,                  "var(--green)"],
    ["Annual Fleet Saving (₹)",  (s.total_annual_fuel_saving_inr||0).toLocaleString("en-IN"), "var(--amber)"],
    ["Total Investment (₹)",     (s.total_retrofit_investment_inr||0).toLocaleString("en-IN"), "var(--muted)"],
    ["Avg Breakeven (yrs)",      s.average_breakeven_years,                    "var(--accent)"],
  ];

  document.getElementById("fleetSummary").innerHTML = cards.map(([label, val, col]) =>
    `<div class="fs-card">
       <span style="color:${col}">${val}</span>
       <small>${label}</small>
     </div>`
  ).join("");

  let tbl = `<div class="ft-header">
    <div>ID</div><div>Type</div><div>Score</div><div>Range</div>
    <div>Motor</div><div>Cost</div><div>Breakeven</div>
  </div>`;

  (data.vehicles || []).forEach(v => {
    const sc = v.score;
    const grade = sc >= 85 ? "a" : sc >= 70 ? "b" : sc >= 55 ? "c" : sc >= 40 ? "d" : "f";
    tbl += `<div class="ft-row">
      <div>${v.vehicle_id}</div>
      <div>${v.vehicle_type}</div>
      <div><span class="score-pill ${grade}">${sc}%</span></div>
      <div>${v.battery?.estimated_range_km || "—"} km</div>
      <div>${v.battery?.motor?.power_kw || "—"} kW</div>
      <div>₹${((v.battery?.estimated_cost_inr||0)/1000).toFixed(0)}k</div>
      <div>${v.roi?.breakeven_years || "—"} yr</div>
    </div>`;
  });

  document.getElementById("fleetTable").innerHTML = tbl;
  document.getElementById("fleetResults").scrollIntoView({ behavior: "smooth" });
}

function downloadSampleCSV() {
  const url = `${API.replace("8000","8000")}/` ;
  // Inline sample CSV
  const csv = `vehicle_id,vehicle_type,engine_cc,vehicle_age_years,chassis_condition,odometer_km,gearbox_type,weight_kg,wheelbase_mm,has_rust,electrical_condition,brake_condition,mileage_kmpl,target_range_km
V001,Hatchback,1100,5,8,52000,Manual,840,2435,0,8,8,16,120
V002,Three-Wheeler,650,4,9,35000,Manual,410,1800,0,9,9,32,80
V003,Sedan,1600,9,4,130000,Automatic,1180,2600,1,5,5,12,100
V004,Hatchback,800,3,9,22000,Manual,790,2380,0,10,9,19,100
V005,SUV,2000,7,6,90000,Automatic,1490,2710,0,7,7,12,150`;
  const blob = new Blob([csv], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "sample_fleet.csv";
  a.click();
}

/* ── Helpers ─────────────────────────────────────────────────────────────────── */
function rows(pairs) {
  return pairs.map(([k, v]) =>
    `<div class="info-row"><span class="info-key">${k}</span><span class="info-val">${v}</span></div>`
  ).join("");
}
function showLoader(msg) {
  document.getElementById("loaderText").textContent = msg;
  document.getElementById("loader").classList.remove("hidden");
}
function hideLoader() { document.getElementById("loader").classList.add("hidden"); }
