# HEALTHMATE AI — LOCAL RUN GUIDE & DEPLOYMENT MANUAL

Follow this guide to run HealthMate AI on your local development machine or deploy it to production.

---

## 1. Prerequisites

- **Python**: Python 3.10, 3.11, or 3.12 installed.
- **Node.js**: Node.js v18+ and npm installed.
- **Operating System**: Windows, Linux, or macOS.

---

## 2. Backend Setup & Local Run

### Step 1: Navigate to Project Directory
```bash
cd "D:\Healthmate AI"
```

### Step 2: Set Up Virtual Environment (Optional / Recommended)
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
*(Default settings work out of the box with SQLite and local development fallback).*

### Step 5: Start the Backend Server
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend is now live at:
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

---

## 3. Frontend Setup & Local Run

### Step 1: Open a Second Terminal
```bash
cd "D:\Healthmate AI\frontend"
```

### Step 2: Install Node Dependencies
```bash
npm install
```

### Step 3: Start the Vite Development Server
```bash
npm run dev
```

The frontend application is now live at:
- **Frontend URL**: `http://localhost:5173`

---

## 4. Running the Complete Automated Test Suite

To run all 138 backend tests:
```bash
cd "D:\Healthmate AI"
python -m pytest backend/tests -v
```

To run the frontend production build validation:
```bash
cd "D:\Healthmate AI\frontend"
npm.cmd run build
```

---

## 5. Production Deployment Instructions

### Backend (Gunicorn / Uvicorn Behind Nginx)
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend (Static Asset Serving)
```bash
cd frontend
npm run build
# Serve dist/ using Nginx, Caddy, Cloudflare Pages, or AWS S3/CloudFront.
```
