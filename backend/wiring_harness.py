"""
wiring_harness.py
-----------------
Generates an SVG wiring harness diagram for the EV retrofit.
Shows: Battery Pack → BMS → Controller → Motor, Charger → BMS,
DC-DC Converter, and safety interlock lines.
"""

def generate_wiring_svg(vehicle_type: str, voltage_v: int, motor_kw: float,
                         motor_name: str, chemistry: str) -> str:
    cable_color = "#00E5FF" if voltage_v < 60 else "#FF4444"
    lv_color    = "#22C55E"
    sig_color   = "#F59E0B"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 560" font-family="DM Sans,sans-serif">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="{cable_color}"/>
    </marker>
    <marker id="arr_lv" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="{lv_color}"/>
    </marker>
    <marker id="arr_sig" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="{sig_color}"/>
    </marker>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="900" height="560" fill="#0D1627" rx="12"/>
  <text x="450" y="34" fill="#E2EAF8" font-size="16" font-weight="700"
        text-anchor="middle">EV Retrofit Wiring Harness — {vehicle_type} | {voltage_v}V | {motor_kw}kW</text>

  <!-- Legend -->
  <g transform="translate(30,50)">
    <line x1="0" y1="8" x2="30" y2="8" stroke="{cable_color}" stroke-width="3"/>
    <text x="36" y="13" fill="#7A90B8" font-size="11">HV Power ({voltage_v}V DC)</text>
    <line x1="0" y1="28" x2="30" y2="28" stroke="{lv_color}" stroke-width="2"/>
    <text x="36" y="33" fill="#7A90B8" font-size="11">LV (12V)</text>
    <line x1="0" y1="48" x2="30" y2="48" stroke="{sig_color}" stroke-width="1.5" stroke-dasharray="5,3"/>
    <text x="36" y="53" fill="#7A90B8" font-size="11">CAN / Signal</text>
  </g>

  <!-- ── BATTERY PACK ── -->
  <g transform="translate(60,120)">
    <rect width="150" height="90" rx="8" fill="#1E3058" stroke="{cable_color}" stroke-width="2" filter="url(#glow)"/>
    <text x="75" y="28" fill="{cable_color}" font-size="13" font-weight="700" text-anchor="middle">🔋 BATTERY PACK</text>
    <text x="75" y="48" fill="#E2EAF8" font-size="11" text-anchor="middle">{chemistry[:12]}</text>
    <text x="75" y="65" fill="#E2EAF8" font-size="11" text-anchor="middle">{voltage_v}V Nominal</text>
    <text x="75" y="82" fill="#7A90B8" font-size="10" text-anchor="middle">Cells in Series/Parallel</text>
  </g>

  <!-- ── BMS ── -->
  <g transform="translate(60,280)">
    <rect width="150" height="80" rx="8" fill="#1E3058" stroke="{sig_color}" stroke-width="2"/>
    <text x="75" y="26" fill="{sig_color}" font-size="13" font-weight="700" text-anchor="middle">🧠 BMS</text>
    <text x="75" y="44" fill="#E2EAF8" font-size="11" text-anchor="middle">Battery Mgmt System</text>
    <text x="75" y="60" fill="#7A90B8" font-size="10" text-anchor="middle">Cell balancing, SOC, SOH</text>
    <text x="75" y="75" fill="#7A90B8" font-size="10" text-anchor="middle">Thermal management</text>
  </g>

  <!-- ── MOTOR CONTROLLER ── -->
  <g transform="translate(370,180)">
    <rect width="160" height="90" rx="8" fill="#1E3058" stroke="{cable_color}" stroke-width="2" filter="url(#glow)"/>
    <text x="80" y="26" fill="{cable_color}" font-size="13" font-weight="700" text-anchor="middle">⚡ CONTROLLER</text>
    <text x="80" y="44" fill="#E2EAF8" font-size="11" text-anchor="middle">VFD / Inverter</text>
    <text x="80" y="60" fill="#E2EAF8" font-size="11" text-anchor="middle">{int(motor_kw * 1.2)} kW Peak</text>
    <text x="80" y="76" fill="#7A90B8" font-size="10" text-anchor="middle">PWM + Regen Braking</text>
  </g>

  <!-- ── MOTOR ── -->
  <g transform="translate(680,180)">
    <rect width="155" height="90" rx="8" fill="#1E3058" stroke="{cable_color}" stroke-width="2" filter="url(#glow)"/>
    <text x="77" y="26" fill="{cable_color}" font-size="13" font-weight="700" text-anchor="middle">🔧 MOTOR</text>
    <text x="77" y="44" fill="#E2EAF8" font-size="11" text-anchor="middle">{motor_name[:22]}</text>
    <text x="77" y="60" fill="#E2EAF8" font-size="11" text-anchor="middle">{motor_kw} kW</text>
    <text x="77" y="76" fill="#7A90B8" font-size="10" text-anchor="middle">3-Phase AC Output</text>
  </g>

  <!-- ── CHARGER ── -->
  <g transform="translate(370,390)">
    <rect width="160" height="80" rx="8" fill="#1E3058" stroke="{lv_color}" stroke-width="2"/>
    <text x="80" y="26" fill="{lv_color}" font-size="13" font-weight="700" text-anchor="middle">🔌 OBC</text>
    <text x="80" y="44" fill="#E2EAF8" font-size="11" text-anchor="middle">On-Board Charger</text>
    <text x="80" y="60" fill="#7A90B8" font-size="10" text-anchor="middle">AC → DC Conversion</text>
    <text x="80" y="75" fill="#7A90B8" font-size="10" text-anchor="middle">CCS2 / Type-2 Socket</text>
  </g>

  <!-- ── DC-DC ── -->
  <g transform="translate(680,390)">
    <rect width="155" height="80" rx="8" fill="#1E3058" stroke="{lv_color}" stroke-width="2"/>
    <text x="77" y="26" fill="{lv_color}" font-size="13" font-weight="700" text-anchor="middle">🔄 DC-DC</text>
    <text x="77" y="44" fill="#E2EAF8" font-size="11" text-anchor="middle">HV → 12V Converter</text>
    <text x="77" y="60" fill="#7A90B8" font-size="10" text-anchor="middle">Accessories / ECU</text>
    <text x="77" y="75" fill="#7A90B8" font-size="10" text-anchor="middle">Aux battery charging</text>
  </g>

  <!-- ── SAFETY INTERLOCK ── -->
  <g transform="translate(240,460)">
    <rect width="130" height="60" rx="8" fill="#2A1200" stroke="#F59E0B" stroke-width="1.5" stroke-dasharray="4,2"/>
    <text x="65" y="22" fill="{sig_color}" font-size="11" font-weight="700" text-anchor="middle">🛡️ SAFETY</text>
    <text x="65" y="38" fill="#E2EAF8" font-size="10" text-anchor="middle">HV Interlock Loop</text>
    <text x="65" y="52" fill="#7A90B8" font-size="9" text-anchor="middle">Manual Service Plug</text>
  </g>

  <!-- ════ HV POWER LINES ════ -->
  <!-- Battery → Controller -->
  <line x1="210" y1="165" x2="370" y2="225" stroke="{cable_color}" stroke-width="3"
        marker-end="url(#arr)" filter="url(#glow)"/>
  <text x="278" y="182" fill="{cable_color}" font-size="10" transform="rotate(-20,278,182)">HV+ / HV−</text>

  <!-- Controller → Motor -->
  <line x1="530" y1="225" x2="680" y2="225" stroke="{cable_color}" stroke-width="3"
        marker-end="url(#arr)" filter="url(#glow)"/>
  <text x="590" y="218" fill="{cable_color}" font-size="10">3-Phase AC</text>

  <!-- Motor → Controller (Regen) -->
  <line x1="680" y1="242" x2="530" y2="242" stroke="{cable_color}" stroke-width="1.5"
        stroke-dasharray="6,3" marker-end="url(#arr)"/>
  <text x="575" y="258" fill="#7A90B8" font-size="9">Regen</text>

  <!-- Charger → BMS -->
  <line x1="370" y1="430" x2="210" y2="320" stroke="{lv_color}" stroke-width="2"
        marker-end="url(#arr_lv)"/>

  <!-- DC-DC → accessories line -->
  <line x1="757" y1="470" x2="835" y2="470" stroke="{lv_color}" stroke-width="2"
        marker-end="url(#arr_lv)"/>
  <text x="840" y="475" fill="{lv_color}" font-size="10">12V</text>

  <!-- ════ CAN SIGNAL LINES ════ -->
  <!-- BMS → Controller -->
  <line x1="210" y1="310" x2="370" y2="250" stroke="{sig_color}" stroke-width="1.5"
        stroke-dasharray="5,3" marker-end="url(#arr_sig)"/>
  <text x="270" y="268" fill="{sig_color}" font-size="9" transform="rotate(-30,270,268)">CAN Bus</text>

  <!-- BMS → Charger -->
  <line x1="135" y1="360" x2="370" y2="410" stroke="{sig_color}" stroke-width="1.5"
        stroke-dasharray="5,3" marker-end="url(#arr_sig)"/>
  <text x="220" y="410" fill="{sig_color}" font-size="9">Charge control</text>

  <!-- Controller → DC-DC -->
  <line x1="530" y1="260" x2="680" y2="390" stroke="{lv_color}" stroke-width="1.5"
        marker-end="url(#arr_lv)"/>

  <!-- Safety interlock to Battery -->
  <line x1="305" y1="460" x2="135" y2="210" stroke="{sig_color}" stroke-width="1"
        stroke-dasharray="3,4" marker-end="url(#arr_sig)"/>

  <!-- AIS-038 label -->
  <rect x="30" y="510" width="340" height="28" rx="4" fill="#0A1525"/>
  <text x="200" y="529" fill="#7A90B8" font-size="10" text-anchor="middle">
    Compliant: AIS-038 Rev.2 | AIS-156 | IS-16046 EMC | CMVR Part-IV
  </text>

  <!-- Voltage class badge -->
  <rect x="700" y="510" width="170" height="28" rx="4"
        fill="{('#0A2A0A' if voltage_v < 60 else '#2A0A0A')}"/>
  <text x="785" y="529" fill="{('#22C55E' if voltage_v < 60 else '#EF4444')}"
        font-size="10" text-anchor="middle" font-weight="700">
    {'Class-A Safe (&lt;60V)' if voltage_v < 60 else f'Class-B HV ({voltage_v}V) — IMD Required'}
  </text>
</svg>"""
    return svg
