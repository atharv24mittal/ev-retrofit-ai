# ⚡ RetrofitAI — AI-Powered EV Conversion Intelligence System

> ET AutoTech Hackathon 2026 | Theme 2: AI for EV Retrofit & Conversion Ecosystem
<img width="910" height="452" alt="image" src="https://github.com/user-attachments/assets/c32eaa3b-63ae-47cc-a91a-4ebdd455c77e" />
<img width="377" height="305" alt="Screenshot 2026-06-05 121423" src="https://github.com/user-attachments/assets/371cc85a-cc11-4a76-9b12-4decab6c1d16" />
<img width="678" height="340" alt="Screenshot 2026-06-05 121450" src="https://github.com/user-attachments/assets/756d98f9-691b-4141-b342-2374c7c57928" />
<img width="649" height="448" alt="Screenshot 2026-06-05 121506" src="https://github.com/user-attachments/assets/526dab37-ce5e-424d-8dec-d34925fbe1a7" />
<img width="529" height="377" alt="Screenshot 2026-06-05 121522" src="https://github.com/user-attachments/assets/1d6b0b20-be0e-486f-bf35-eee29f1c22a4" />
<img width="646" height="287" alt="Screenshot 2026-06-05 121606" src="https://github.com/user-attachments/assets/3fd6d179-52d2-4c23-8b17-8d901123b33d" />
<img width="635" height="355" alt="Screenshot 2026-06-05 121620" src="https://github.com/user-attachments/assets/435134e5-6502-4c71-9a1d-d58b9faca079" />
<img width="642" height="393" alt="Screenshot 2026-06-05 121634" src="https://github.com/user-attachments/assets/53d43f0a-8a7e-48a7-a070-de37cc18a21d" />
<img width="646" height="455" alt="Screenshot 2026-06-05 121648" src="https://github.com/user-attachments/assets/44ec0585-a3b4-464d-9749-3d2f06a90d00" />
<img width="647" height="307" alt="Screenshot 2026-06-05 121900" src="https://github.com/user-attachments/assets/efac22ee-ac3d-4afb-baaa-feea67298d1c" />
<img width="559" height="412" alt="image" src="https://github.com/user-attachments/assets/93ef37bd-df19-405a-b295-a5a9e9789d3d" />



---

## 🗂️ Project Structure

```
ev-retrofit-ai/
├── backend/
│   ├── app.py                 # FastAPI server (main entry point)
│   ├── feasibility_model.py   # ML model: Random Forest + Gradient Boosting
│   ├── battery_optimizer.py   # Battery pack & motor recommendation engine
│   ├── compliance_checker.py  # AIS-038 / CMVR / RTO compliance validator
│   ├── report_generator.py    # PDF report generator (ReportLab)
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── index.html             # Main UI
│   ├── style.css              # Dark futuristic styling
│   └── script.js              # API calls & result rendering
├── models/
│   └── retrofit_model.pkl     # Trained ML model (auto-generated on first run)
├── data/
│   └── sample_vehicles.csv    # Training dataset (30 vehicles)
├── reports/                   # PDF reports saved here
└── README.md
```

---

## 🚀 Quick Start (Step-by-Step)

### Prerequisites
- Python 3.10+
- VS Code (recommended)
- Node.js (not needed — no Node frontend)

---

### Step 1 — Open the project in VS Code
```bash
# Unzip the downloaded file, then:
cd ev-retrofit-ai
code .
```

---

### Step 2 — Create a virtual environment
```bash
# In VS Code terminal (Ctrl+`)
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

---

### Step 3 — Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

---

### Step 4 — Start the backend server
```bash
# From the backend/ folder:
python app.py
# OR:
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The first run will **automatically train the ML model** and save it to `models/retrofit_model.pkl`.

You'll see:
```
INFO: Model loaded ✓
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

### Step 5 — Open the frontend
Open `frontend/index.html` in your browser.

**For best experience, use VS Code Live Server extension:**
1. Install "Live Server" extension in VS Code
2. Right-click `frontend/index.html` → "Open with Live Server"

---

### Step 6 — Use the app
1. Fill in vehicle details (or click **Load Sample Vehicle**)
2. Click **Analyse Vehicle**
3. View feasibility score, battery config, compliance results
4. Click **Download PDF Report** to get a professional report

---

## 🔌 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Health check |
| GET | `/api/health` | Model status |
| POST | `/api/assess` | Full vehicle assessment |
| POST | `/api/report` | Download PDF report |
| GET | `/docs` | Interactive API docs (Swagger) |
| GET | `/ui` | Frontend (served by FastAPI) |

### Example API call (Python)
```python
import requests

payload = {
    "vehicle_type": "Hatchback",
    "engine_cc": 1000,
    "vehicle_age_years": 5,
    "chassis_condition": 8,
    "odometer_km": 50000,
    "gearbox_type": "Manual",
    "weight_kg": 850,
    "wheelbase_mm": 2400,
    "has_rust": 0,
    "electrical_condition": 7,
    "brake_condition": 8,
    "target_range_km": 100
}

response = requests.post("http://localhost:8000/api/assess", json=payload)
print(response.json())
```

---

## 🧠 AI/ML Architecture

### Feasibility Model
- **Algorithm**: Random Forest Regressor (score 0–100) + Gradient Boosting Classifier (go/no-go)
- **Features**: vehicle type, age, engine CC, chassis condition, odometer, weight, rust, electrical & brake health
- **Training data**: 30 synthetic vehicle records across 6 vehicle types
- **Output**: Feasibility score (%), grade (A–F), confidence %, recommendation

### Battery Optimizer
- **Rule-based + physics model**
- Calculates required kWh from target range, load factor per vehicle type
- Selects LFP/NMC chemistry based on pack size
- Recommends motor from catalogue based on vehicle weight
- Estimates cost, charge time, placement zones

### Compliance Checker
- **Rule engine** based on:
  - AIS-038 Rev.2 (Electric Power Train Safety)
  - AIS-156 (Battery Pack Safety)
  - CMVR Part-IV (Homologation)
  - IS-16046 (EMC)
- Generates mandatory test list and RTO document checklist

---

## 📊 Judging Criteria Alignment

| Criterion | How We Address It |
|-----------|-------------------|
| Depth of Problem Insight | Indian-specific: AIS-038, CMVR, RTO, Indian road conditions |
| Innovation & Creativity | Full-stack AI: ML + Physics + Rule Engine + PDF generation |
| Intelligence Architecture | 3-layer AI: ML model → optimizer → compliance engine |
| Feasibility & Technical Soundness | Production-ready FastAPI, real ML, downloadable PDF |
| Impact & Scalability | REST API — integrable into any EV workshop or OEM portal |
| Clarity of Presentation | Professional UI + PDF report auto-generation |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| ML/AI | scikit-learn (Random Forest, Gradient Boosting) |
| Backend | FastAPI + Uvicorn |
| Data | Pandas, NumPy |
| PDF | ReportLab |
| Frontend | Vanilla HTML/CSS/JS (no framework needed) |
| Fonts | Syne + DM Sans (Google Fonts) |

---

## 📄 License
Built for ET AutoTech Hackathon 2026. Educational and competition use only.
