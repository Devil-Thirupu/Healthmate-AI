# HEALTHMATE AI — FINAL FILE INVENTORY (PHASES 1–20)

This document provides the complete, authoritative catalog of all source code files, configurations, datasets, and test suites across the HealthMate AI project.

---

## 1. Backend Service Layer (`backend/app/services/`)

| File Path | Phase | Core Purpose & Functionality |
|---|---|---|
| `hybrid_rag_service.py` | Phase 6, 14.1 | Hybrid RAG Engine prioritizing structured patient records > document OCR chunks > medical knowledge dataset > nutrition knowledge. Implements BM25 lexical ranking, broad latest values resolution, month/date parser, and citation generator. |
| `evidence_guard_service.py` | Phase 7, 14.1 | Deterministic zero-hallucination verification. Enforces evidence states (`SUPPORTED`, `PARTIAL`, `INSUFFICIENT`), tenant isolation check, and non-causality disclaimers. |
| `health_intelligence_service.py` | Phase 5, 14, 15, 18 | Longitudinal health intelligence engine. Evaluates reference ranges, computes delta percentage changes, evaluates trends, generates "Explain My Report" summaries, and builds Doctor Visit Mode briefings. |
| `health_timeline_service.py` | Phase 14, 16 | Multi-source chronological medical history generator. Combines reports, lab tests, prescriptions, vitals, and appointments with monthly grouping and category filters. |
| `global_search_service.py` | Phase 14, 17 | Unified global health search engine across lab test names, biomarker values, medicine names, document titles, dates, months, years, and OCR text chunks with strict user isolation. |
| `reminder_service.py` | Phase 13, 19 | Safe medication reminder lifecycle service. Synchronizes reminders directly from verified prescriptions without guessing missing timings; manages status (`PENDING`, `COMPLETED`, `SNOOZED`). |
| `notification_service.py` | Phase 13, 19 | In-app patient notification management for medication reminders, report insights, and health milestones with privacy protection. |
| `multilingual_explanation_service.py` | Phase 9, 14.1 | Trilingual AI explanation generator for English, Tamil (தமிழ்), and Tanglish. Formats instructional text while strictly locking numbers, units, dates, and medicine names. |
| `nutrition_service.py` | Phase 10 | Evidence-based Nutrition Intelligence service using USDA FoodData Central Foundation Foods dataset (April 2026). Food search, nutrient profiling, comparison, and diet rules. |
| `appointment_summary_service.py` | Phase 8 | Clinical discussion question builder, appointment preparation summary generator, and ReportLab PDF compiler. |
| `prescription_model_service.py` | Phase 4 | Lightweight rule-based prescription extractor, medication catalog normalizer, and confidence score estimator. |
| `clinical_extractor.py` | Phase 3, 4 | Regex-based clinical lab test extractor, reference range parser, and medication catalog taxonomy. |
| `ocr_service.py` | Phase 2, 3 | Multi-tier OCR pipeline (PyMuPDF / pypdf / pytesseract fallback) extracting clean raw text and creating document chunks. |
| `storage_service.py` | Phase 2 | Cryptographic SHA-256 file hasher, storage manager, and duplicate document detector. |
| `audit_service.py` | Phase 11 | Tamper-evident action logging without exposing raw medical snippets or patient passwords. |

---

## 2. Backend API Layer (`backend/app/api/`)

| File Path | Phase | Core Purpose & Functionality |
|---|---|---|
| `api_router.py` | Phase 1–20 | Master FastAPI APIRouter registering all sub-routers with standard `/api/v1` prefixes. |
| `assistant.py` | Phase 6, 14.1 | AI Assistant chat endpoints (`/assistant/chat`, `/assistant/knowledge-sources`) executing grounded Hybrid RAG queries with Evidence Guard. |
| `timeline_search.py` | Phase 14, 15, 16, 17, 18 | Endpoints for Health Timeline (`/health-timeline`), Global Search (`/health-search`), Doctor Visit Mode (`/doctor-visit`), and Explain Report (`/reports/{id}/explain`). |
| `reminders.py` | Phase 13, 19 | Medication reminder endpoints (`/reminders/today`, `/reminders/schedule`, `/reminders/sync`, `/reminders/{id}/complete`, `/reminders/{id}/snooze`). |
| `notifications.py` | Phase 13, 19 | In-app notification endpoints (`/notifications`, `/notifications/{id}/read`, `/notifications/read-all`). |
| `health_intelligence.py` | Phase 5 | Health intelligence summary and biomarker longitudinal trends endpoints (`/health-intelligence/summary`, `/health-intelligence/trends/{canonical_name}`). |
| `nutrition.py` | Phase 10 | Nutrition search, food comparison, nutrient profiling, and dietary recommendations endpoints (`/nutrition/search`, `/nutrition/compare`, `/nutrition/recommendations`). |
| `appointment_summary.py` | Phase 8 | Appointment preparation summary generation, viewing, and PDF download endpoints (`/appointment-summary/generate`, `/appointment-summary/{id}/pdf`). |
| `sharing.py` | Phase 11 | Patient-controlled record sharing endpoints (`/sharing/links`, `/sharing/access/{token}`, `/sharing/links/{id}/revoke`). |
| `audit.py` | Phase 11 | Audit log viewing endpoints strictly for the authenticated patient (`/audit/logs`). |
| `documents.py` | Phase 2 | Medical document upload, listing, details, raw text, and deletion endpoints (`/documents/upload`, `/documents`, `/documents/{id}`). |
| `auth.py` | Phase 1, 11 | User authentication, registration, login, profile management, and password change endpoints (`/auth/register`, `/auth/login`, `/auth/me`). |
| `deps.py` | Phase 1 | Dependency injection utilities (`get_current_user`, `get_client_ip`, `get_db`). |

---

## 3. Backend Database Models (`backend/app/models/`)

| File Path | Tables Defined | Purpose |
|---|---|---|
| `user.py` | `users` | User credentials, roles, language preferences, and profile fields. |
| `document.py` | `documents` | Uploaded document metadata, SHA-256 hash, category, OCR text, and processing status. |
| `clinical.py` | `lab_tests`, `prescriptions`, `vital_records` | Structured clinical measurements, extracted prescriptions, and vital records. |
| `rag.py` | `rag_chunks`, `medical_knowledge_chunks` | Document text chunks and curated Medical QA dataset. |
| `nutrition.py` | `nutrition_food_items` | USDA Foundation Foods dataset items and nutrient JSON profiles. |
| `reminder.py` | `medication_reminders`, `notifications` | Medication schedules and user notifications. |
| `sharing.py` | `shared_links` | Cryptographic time-limited record sharing tokens. |
| `audit.py` | `audit_logs` | Audit trail events with IP addresses and user actions. |
| `appointment_summary.py` | `appointment_summaries` | Generated doctor appointment preparation summaries. |
| `prescription_extraction.py` | `prescription_extractions` | Detailed OCR extraction audit data with bounding boxes and confidence. |

---

## 4. Frontend Application (`frontend/src/`)

| File Path | Phase | Core Purpose & Functionality |
|---|---|---|
| `pages/AIAssistantPage.jsx` | Phase 14.1, 20 | Conversational AI Chatbot interface with dual-bubble stream, structured value cards, collapsible citations, trilingual toggle (EN, Tamil, Tanglish), and contextual prompt chips. |
| `pages/DashboardPage.jsx` | Phase 1–20 | Central patient dashboard integrating Daily Health card, Medication schedule, Health Timeline view, and Quick Actions. |
| `pages/ReportsPage.jsx` | Phase 2, 15 | Document vault interface with category filtering, document upload modal, DocumentDetailModal, and "Explain My Report" triggers. |
| `pages/PrescriptionsPage.jsx` | Phase 3, 4, 19 | Prescription management view displaying extracted medicines, dosages, timings, reminders, and manual correction tools. |
| `pages/AppointmentPreparationPage.jsx` | Phase 8, 18 | Clinical appointment prep workspace, discussion questions, Doctor Visit Mode modal, and ReportLab PDF download. |
| `pages/NutritionPage.jsx` | Phase 10 | Nutrition Intelligence dashboard with USDA food search, nutrient comparison charts, and dietary guidance. |
| `pages/SharingPage.jsx` | Phase 11 | Granular record sharing dashboard for creating, monitoring, and revoking time-limited doctor links. |
| `pages/AuditPage.jsx` | Phase 11 | Security audit trail dashboard showing login, upload, view, sharing, and AI assistant events. |
| `pages/PublicShareViewPage.jsx` | Phase 11 | Read-only public portal for doctors accessing shared records via secure PIN tokens. |
| `components/common/GlobalSearchBar.jsx` | Phase 14, 17 | Universal search bar in Navbar querying biomarkers, medicines, documents, and OCR text with live dropdown results. |
| `components/common/HealthTimelineView.jsx` | Phase 14, 16 | Interactive chronological timeline grouping records by month/year with category filters. |
| `components/common/ExplainReportModal.jsx` | Phase 14, 15 | Modal explaining uploaded reports with structured findings, changes, reference ranges, and source snippets. |
| `components/common/DoctorVisitModal.jsx` | Phase 14, 18 | Professional physician consultation briefing modal summarizing recent reports, active drugs, trends, and questions. |
| `components/common/MedicationScheduleCard.jsx` | Phase 13, 19 | Dashboard card grouping today's medications into Morning, Afternoon, and Night slots with completion checkboxes. |
| `components/common/NotificationCenter.jsx` | Phase 13, 19 | Notification bell dropdown with unread badge counter, notification categorization, and mark-as-read actions. |
| `components/common/DailyHealthCard.jsx` | Phase 13 | Patient daily health summary highlighting pending medications, latest lab alerts, and nutrition guidance. |
| `components/common/DocumentDetailModal.jsx` | Phase 2, 7 | Complete document viewer displaying extracted measurements, prescriptions, raw OCR text, and Evidence Guard highlighting. |

---

## 5. Automated Test Suite (`backend/tests/`)

| Test File | Phase Covered | Tests Count | Status |
|---|---|---|---|
| `test_auth.py` | Phase 1, 11 | 7 | **PASSED** |
| `test_storage.py` | Phase 2 | 3 | **PASSED** |
| `test_documents.py` | Phase 2 | 1 | **PASSED** |
| `test_ocr_extraction.py` | Phase 3 | 5 | **PASSED** |
| `test_prescription_extraction_lightweight.py` | Phase 3, 4 | 13 | **PASSED** |
| `test_prescription_model.py` | Phase 4 | 6 | **PASSED** |
| `test_health_intelligence.py` | Phase 5 | 8 | **PASSED** |
| `test_hybrid_rag.py` | Phase 6 | 14 | **PASSED** |
| `test_evidence_guard.py` | Phase 7 | 10 | **PASSED** |
| `test_appointment_summary.py` | Phase 8 | 8 | **PASSED** |
| `test_multilingual_explanation.py` | Phase 9 | 19 | **PASSED** |
| `test_nutrition.py` | Phase 10 | 24 | **PASSED** |
| `test_secure_sharing.py` | Phase 11 | 31 | **PASSED** |
| `test_sharing.py` | Phase 11 | 1 | **PASSED** |
| `test_dataset_pipeline.py` | Phase 12 | 5 | **PASSED** |
| `test_reminders_and_notifications.py` | Phase 13, 19 | 9 | **PASSED** |
| `test_phase14_timeline_search_doctor_visit.py` | Phase 14, 15, 16, 17, 18 | 11 | **PASSED** |
| `test_phase14_1_assistant_rag_correction.py` | Phase 14.1 | 9 | **PASSED** |
| `test_phase15_to_20_comprehensive_validation.py` | Phase 15, 16, 17, 18, 19, 20 | 6 | **PASSED** |
| **TOTAL** | **Phases 1–20** | **138** | **100% PASSED** |
