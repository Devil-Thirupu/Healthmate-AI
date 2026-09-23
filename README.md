# HealthMate AI — Intelligent Personal Health Record & Medical Document Assistant

**HealthMate AI** is a privacy-first, evidence-grounded intelligent personal health record (PHR) and clinical document assistant. It combines multi-tier OCR, zero-hallucination structured extraction, Hybrid RAG with Evidence Guard, Nutrition Intelligence (USDA Foundation Foods), Appointment Preparation with ReportLab PDF export, trilingual AI explanations (English, Tamil, Tanglish), granular patient-controlled record sharing, and zero-exposure audit logging.

---

## Key Capabilities (Phases 1–12)

1. **Intelligent Document Vault & Multi-Tier OCR**: Secure ingestion for PDFs, medical reports, prescriptions, and radiology images with OCR confidence scoring and human-in-the-loop manual corrections.
2. **Clinical Health Intelligence**: Automated extraction for lab biomarkers and prescriptions, longitudinal trend calculations (`% change`, direction, and reference range alerts) without unauthorized diagnoses.
3. **Hybrid RAG & Evidence Guard**: Evidence Priority Hierarchy:
   $$\text{User Structured Records} > \text{User Document Chunks} > \text{General Medical Knowledge} > \text{General Nutrition Knowledge}$$
   Strictly rejects estimating missing patient values.
4. **Appointment Preparation & Health Summary PDF**: Reviewable consultation summaries with printable ReportLab 5.0.1 PDFs.
5. **Trilingual AI Explanations**: English, Tamil (`ta`), and Tanglish (`tanglish`) AI explanations that strictly preserve 100% of numerical values, units, medicine names, and dates.
6. **Nutrition Intelligence (USDA Foundation Foods)**: Food & fruit exploration, macronutrient & micronutrient breakdowns per 100g, and side-by-side food comparisons.
7. **Secure Sharing & Access Control**: Time-limited, patient-controlled sharing with optional PIN protection and instant revocation.
8. **Audit Dashboard**: Tamper-evident, zero-exposure activity logging categorized by Login, Documents, AI, and Sharing.

---

## Quickstart & Local Execution

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 2. Backend Setup
```powershell
# Navigate to project root
cd "D:\Healthmate AI"

# Install Python dependencies
pip install fastapi uvicorn sqlalchemy pydantic reportlab pymupdf rapidfuzz pytest

# Run Backend Server (FastAPI on Port 8000)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger API docs available at: `http://localhost:8000/docs`

### 3. Frontend Setup
```powershell
# In a new terminal window
cd "D:\Healthmate AI\frontend"

# Install dependencies (if first time)
npm install

# Start Vite Development Server (Port 5173)
npm run dev
```
Web application UI opens at: `http://localhost:5173`

---

## Running the Automated Test Suite

```powershell
cd "D:\Healthmate AI"
$env:PYTHONPATH="."
python -m pytest backend/tests -v
```

---

## Environment Variables (.env)

Refer to [.env.example](.env.example):
```env
PROJECT_NAME=HEALTHMATE AI
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
GOOGLE_CLIENT_ID=your_google_client_id_placeholder.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret_placeholder
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```
*Note: If Google OAuth credentials are not configured, the application starts normally in development mode and provides full access through Mobile Number + Password and Email + Password authentication.*
