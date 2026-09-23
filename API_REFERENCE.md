# HEALTHMATE AI — API REFERENCE & INTEGRATION SPECIFICATION (PHASES 1–20)

This reference documents every REST API endpoint in the HealthMate AI backend. All endpoints are rooted under the `/api/v1` namespace.

---

## 1. Authentication & User Profile (`/api/v1/auth`)

| Method | Endpoint | Auth | Request Payload | Response | Description |
|---|---|---|---|---|---|
| `POST` | `/auth/register` | None | `{email, password, full_name, mobile_number, language_preference, role}` | `UserOut` | Register new user account with hashed password. |
| `POST` | `/auth/login` | None | `OAuth2PasswordRequestForm` (`username`, `password`) | `{access_token, token_type, user}` | Authenticate via email/password and obtain JWT access token. |
| `POST` | `/auth/login/mobile` | None | `{mobile_number, password}` | `{access_token, token_type, user}` | Authenticate via mobile number and password. |
| `GET` | `/auth/me` | Bearer JWT | None | `UserOut` | Retrieve authenticated user profile and settings. |
| `PUT` | `/auth/profile` | Bearer JWT | `{full_name, mobile_number, language_preference}` | `UserOut` | Update user personal details and language preference. |
| `POST` | `/auth/change-password` | Bearer JWT | `{current_password, new_password}` | `{message}` | Change account password. |

---

## 2. Document Vault & Upload (`/api/v1/documents`)

| Method | Endpoint | Auth | Request Payload | Response | Description |
|---|---|---|---|---|---|
| `POST` | `/documents/upload` | Bearer JWT | `multipart/form-data` (`file`, `category`, `document_date`) | `DocumentUploadResponse` | Upload medical PDF/image, compute SHA-256, execute multi-tier OCR, and extract clinical entities. |
| `GET` | `/documents` | Bearer JWT | Query params: `category`, `skip`, `limit` | `List[DocumentOut]` | List patient's uploaded documents with processing status. |
| `GET` | `/documents/{id}` | Bearer JWT | None | `DocumentDetailOut` | Retrieve document details, extracted lab tests, and prescriptions. |
| `GET` | `/documents/{id}/download`| Bearer JWT | None | File Stream (`PDF/Image`) | Securely stream the original uploaded document. |
| `DELETE`| `/documents/{id}` | Bearer JWT | None | `{message}` | Delete document and cascade delete associated tests, prescriptions, and chunks. |

---

## 3. Grounded AI Assistant & Hybrid RAG (`/api/v1/assistant`)

| Method | Endpoint | Auth | Request Payload | Response | Description |
|---|---|---|---|---|---|
| `POST` | `/assistant/chat` | Bearer JWT | `{query: str, language: "en" \| "ta" \| "tanglish"}` | `ChatQueryResponse` | Grounded clinical chat executing Hybrid RAG across user records and reference datasets with Evidence Guard. |
| `GET` | `/assistant/knowledge-sources`| Bearer JWT| None | `List[KnowledgeSourceInfo]` | Retrieve metadata, licensing, and record counts for active knowledge collections. |

---

## 4. Health Timeline, Search & Doctor Visit Mode (`/api/v1`)

| Method | Endpoint | Auth | Request Payload | Response | Description |
|---|---|---|---|---|---|
| `GET` | `/health-timeline` | Bearer JWT | Query params: `category`, `date_range`, `q` | `TimelineResponse` | Comprehensive chronological multi-source health history grouped by month. |
| `GET` | `/health-search` | Bearer JWT | Query params: `q` (search term), `limit` | `GlobalSearchResponse` | Unified hybrid search across biomarkers, medicines, documents, and OCR text. |
| `GET` | `/doctor-visit` | Bearer JWT | None | `DoctorVisitSummaryResponse` | Clinical consultation briefing with recent reports, active medicines, trends, and questions. |
| `POST` | `/reports/{id}/explain` | Bearer JWT | `{language: "en" \| "ta" \| "tanglish"}` | `ExplainReportResponse` | Grounded explanation of an uploaded report with findings, changes, reference ranges, and source snippets. |

---

## 5. Medication Reminders & Daily Schedule (`/api/v1/reminders`)

| Method | Endpoint | Auth | Request Payload | Response | Description |
|---|---|---|---|---|---|
| `GET` | `/reminders/today` | Bearer JWT | None | `List[MedicationReminderOut]` | Retrieve today's medication reminders for the patient. |
| `GET` | `/reminders/upcoming` | Bearer JWT | None | `List[MedicationReminderOut]` | Retrieve all active upcoming medication reminders. |
| `GET` | `/reminders/schedule` | Bearer JWT | None | `MedicationScheduleOut` | Categorized daily schedule (Morning, Afternoon, Night) with status. |
| `POST` | `/reminders/sync` | Bearer JWT | None | `List[MedicationReminderOut]` | Synchronize reminders from user's verified extracted prescription records. |
| `POST` | `/reminders` | Bearer JWT | `MedicationReminderCreate` | `MedicationReminderOut` | Manually create a medication reminder. |
| `POST` | `/reminders/{id}/complete`| Bearer JWT| None | `MedicationReminderOut` | Mark a reminder dose as completed for today. |
| `POST` | `/reminders/{id}/snooze` | Bearer JWT | `{minutes: int}` | `MedicationReminderOut` | Snooze a reminder for specified minutes. |

---

## 6. In-App Notifications (`/api/v1/notifications`)

| Method | Endpoint | Auth | Request Payload | Response | Description |
|---|---|---|---|---|---|
| `GET` | `/notifications` | Bearer JWT | None | `NotificationSummaryOut` | Retrieve unread count and list of in-app notifications. |
| `POST` | `/notifications/{id}/read`| Bearer JWT| None | `NotificationOut` | Mark specific notification as read. |
| `POST` | `/notifications/read-all`| Bearer JWT| None | `{message}` | Mark all notifications as read. |

---

## 7. Health Intelligence & Biomarker Trends (`/api/v1/health-intelligence`)

| Method | Endpoint | Auth | Request Payload | Response | Description |
|---|---|---|---|---|---|
| `GET` | `/health-intelligence/summary` | Bearer JWT | None | `HealthIntelligenceSummaryOut` | Longitudinal summary with latest values, abnormal flags, and report-to-report deltas. |
| `GET` | `/health-intelligence/trends/{canonical_name}` | Bearer JWT | None | `BiomarkerTrendOut` | Multi-point historical trend values, percentage change, and trajectory for a biomarker. |

---

## 8. Nutrition Intelligence (`/api/v1/nutrition`)

| Method | Endpoint | Auth | Request Payload | Response | Description |
|---|---|---|---|---|---|
| `GET` | `/nutrition/search` | Bearer JWT | Query params: `q`, `category`, `limit` | `List[NutritionFoodItemOut]` | Search USDA Foundation Foods dataset by food name or category. |
| `GET` | `/nutrition/food/{fdc_id}` | Bearer JWT | None | `NutritionFoodDetailOut` | Detailed nutrient breakdown for a specific food item. |
| `POST` | `/nutrition/compare` | Bearer JWT | `{fdc_ids: List[int]}` | `NutritionComparisonOut` | Side-by-side macronutrient and micronutrient comparison. |
| `GET` | `/nutrition/recommendations` | Bearer JWT | None | `DietaryGuidanceOut` | General dietary suggestions derived from user's active biomarker profile. |

---

## 9. Appointment Preparation & ReportLab PDF (`/api/v1/appointment-summary`)

| Method | Endpoint | Auth | Request Payload | Response | Description |
|---|---|---|---|---|---|
| `POST` | `/appointment-summary/generate`| Bearer JWT | `{title: str, reason_for_visit: str}` | `AppointmentSummaryOut` | Compile structured clinical appointment summary. |
| `GET` | `/appointment-summary` | Bearer JWT | None | `List[AppointmentSummaryOut]` | List patient's saved appointment preparation summaries. |
| `GET` | `/appointment-summary/{id}` | Bearer JWT | None | `AppointmentSummaryOut` | Retrieve specific appointment preparation summary. |
| `GET` | `/appointment-summary/{id}/pdf` | Bearer JWT | None | File Stream (`PDF`) | Download clean, professional ReportLab PDF summary for physician consultation. |

---

## 10. Patient-Controlled Secure Record Sharing (`/api/v1/sharing`)

| Method | Endpoint | Auth | Request Payload | Response | Description |
|---|---|---|---|---|---|
| `POST` | `/sharing/links` | Bearer JWT | `{recipient_name, document_ids, expiry_hours, pin}` | `ShareLinkOut` | Generate time-limited, password-protected share token for doctors. |
| `GET` | `/sharing/links` | Bearer JWT | None | `List[ShareLinkOut]` | List all active and past shared links. |
| `POST` | `/sharing/links/{id}/revoke`| Bearer JWT| None | `{message}` | Immediately revoke doctor access for a link. |
| `POST` | `/sharing/access/{token}` | None | `{pin: Optional[str]}` | `PublicSharedRecordsOut` | Public read-only endpoint for clinicians viewing permitted documents. |

---

## 11. Security Audit Trail (`/api/v1/audit`)

| Method | Endpoint | Auth | Request Payload | Response | Description |
|---|---|---|---|---|---|
| `GET` | `/audit/logs` | Bearer JWT | Query params: `limit` | `List[AuditLogOut]` | Retrieve immutable audit trail of logins, uploads, views, sharing, and AI queries. |
