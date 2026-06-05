# 🚀 RetrofitAI — GitHub + Vercel Deployment Guide

## STEP 1: Fix the frontend API URL for deployment

Open `frontend/script.js` and find line 1:
```javascript
const API = "http://localhost:8000";
```
Change it to:
```javascript
const API = window.location.origin;
```
This makes it work both locally AND on Vercel automatically.

---

## STEP 2: Push to GitHub

### First time setup (run in VS Code terminal):

```bash
# Go to project root
cd "C:\Users\laksh\OneDrive\Desktop\auto-tech hackathon\ev-retrofit-ai"

# Initialize git
git init

# Add everything
git add .

# First commit
git commit -m "RetrofitAI v2 - ET AutoTech Hackathon 2026"

# Go to github.com → New Repository
# Name: ev-retrofit-ai
# Keep it Public
# DO NOT add README or .gitignore (we have them already)
# Click Create Repository

# Then run (replace YOUR_USERNAME):
git remote add origin https://github.com/YOUR_USERNAME/ev-retrofit-ai.git
git branch -M main
git push -u origin main
```

---

## STEP 3: Deploy on Vercel

### Option A — Vercel Website (easiest):
1. Go to https://vercel.com → Sign up with GitHub
2. Click "Add New Project"
3. Import your `ev-retrofit-ai` repository
4. Framework Preset: **Other**
5. Root Directory: leave empty (use root)
6. Click **Deploy**

### Option B — Vercel CLI:
```bash
npm install -g vercel
cd "C:\Users\laksh\OneDrive\Desktop\auto-tech hackathon\ev-retrofit-ai"
vercel
# Follow prompts, link to your account
```

---

## STEP 4: Important — Vercel Limitations for FastAPI

Vercel runs Python as serverless functions which means:
- ✅ API endpoints work
- ✅ ML model runs (retrains on cold start)
- ❌ File writes (PDF) won't persist — use /tmp/

### Fix for PDF on Vercel — update app.py:

In `backend/app.py`, find the report route and change:
```python
REPORT_DIR = os.path.join(BASE, "..", "reports")
```
To:
```python
REPORT_DIR = "/tmp/reports" if os.environ.get("VERCEL") else os.path.join(BASE, "..", "reports")
```

And add this to the top of `app.py`:
```python
import tempfile
```

---

## STEP 5: After deployment

Your app will be live at:
`https://ev-retrofit-ai-USERNAME.vercel.app`

Test it:
- Open the URL
- Upload a vehicle photo
- Click Analyse Vehicle
- Check all tabs work

---

## STEP 6: Share for submission

For the hackathon submission:
- **Source Code**: https://github.com/YOUR_USERNAME/ev-retrofit-ai
- **Live Demo**: https://ev-retrofit-ai-USERNAME.vercel.app
- **ZIP file**: Upload the zip as prototype submission

---

## Local development (always works)

```bash
cd backend
python app.py
# Open frontend/index.html in browser
# OR visit http://localhost:8000/ui
```

---

## Environment Variable (optional, for Vercel)

In Vercel dashboard → Settings → Environment Variables:
- Key: `VERCEL`
- Value: `1`

This enables the /tmp fix for PDF generation.
