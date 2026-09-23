# HEALTHMATE AI — DATABASE CHANGE & INTEGRITY REPORT (PHASES 1–20)

This report documents the relational schema, tables, columns, indexes, foreign key relationships, cross-user isolation rules, and data integrity verification results.

---

## 1. Relational Database Schema Overview

- **Engine**: SQLite 3 / SQLAlchemy ORM
- **Migration Strategy**: Additive non-destructive schema evolution with automatic SQLite column reflection.
- **Foreign Key Enforcement**: Enabled with `CASCADE` and `SET NULL` integrity rules.
- **Total Tables**: 12 active relational entities.

---

## 2. Table Specifications

### 1. `users` (Authentication & Profile)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique user identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | Primary login email |
| `hashed_password` | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| `full_name` | VARCHAR(255) | NOT NULL | Patient legal name |
| `mobile_number` | VARCHAR(50) | NULLABLE | Secondary authentication mobile number |
| `language_preference` | VARCHAR(10) | DEFAULT 'en' | Preferred language (`en`, `ta`, `tanglish`) |
| `role` | VARCHAR(50) | DEFAULT 'patient' | Authorization role (`patient`, `doctor`, `admin`) |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account active status |
| `created_at` | DATETIME | NOT NULL | Account creation timestamp (UTC) |

### 2. `documents` (Uploaded Medical Document Vault)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Document identifier |
| `user_id` | INTEGER | FOREIGN KEY (`users.id`), NOT NULL, INDEX | Owner patient identifier |
| `original_filename` | VARCHAR(255) | NOT NULL | Original uploaded filename |
| `stored_filename` | VARCHAR(255) | NOT NULL | Internal sanitized filename |
| `file_path` | VARCHAR(500) | NOT NULL | Relative disk storage path |
| `file_size_bytes` | INTEGER | NOT NULL | Document file size |
| `mime_type` | VARCHAR(100) | NOT NULL | Content MIME type (`application/pdf`, `image/png`, etc.) |
| `file_hash_sha256` | VARCHAR(64) | NOT NULL, INDEX | SHA-256 cryptographic content hash |
| `category` | VARCHAR(50) | NOT NULL, INDEX | Document category (`lab_report`, `prescription`, etc.) |
| `title` | VARCHAR(255) | NOT NULL | Clean clinical title |
| `document_date` | VARCHAR(50) | NULLABLE, INDEX | Extracted clinical document date |
| `ocr_status` | VARCHAR(50) | DEFAULT 'pending' | Processing state (`pending`, `completed`, `failed`) |
| `ocr_raw_text` | TEXT | NULLABLE | Full OCR raw text |
| `created_at` | DATETIME | NOT NULL | Upload timestamp |

### 3. `lab_tests` (Structured Laboratory Measurements)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Lab test identifier |
| `document_id` | INTEGER | FOREIGN KEY (`documents.id`), NULLABLE, INDEX | Originating document |
| `user_id` | INTEGER | FOREIGN KEY (`users.id`), NOT NULL, INDEX | Owner patient identifier |
| `test_name` | VARCHAR(255) | NOT NULL, INDEX | Raw extracted test name |
| `canonical_name` | VARCHAR(100) | NULLABLE, INDEX | Normalized biomarker name (`glucose`, `hba1c`, etc.) |
| `test_category` | VARCHAR(100) | NULLABLE | Panel category (`metabolic`, `lipid`, `cbc`, etc.) |
| `observed_value` | VARCHAR(50) | NOT NULL | Original observed value string |
| `numeric_value` | FLOAT | NULLABLE, INDEX | Normalized numeric value for trend analysis |
| `unit` | VARCHAR(50) | NULLABLE | Measurement unit (`mg/dL`, `%`, `g/dL`, etc.) |
| `flag` | VARCHAR(50) | DEFAULT 'normal', INDEX | Clinical flag (`normal`, `high`, `low`, `critical`) |
| `reference_range_text` | VARCHAR(100) | NULLABLE | Source reference range string |
| `test_date` | VARCHAR(50) | NULLABLE, INDEX | Measured date |
| `created_at` | DATETIME | NOT NULL | Extraction timestamp |

### 4. `prescriptions` (Structured Medication Records)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Prescription item identifier |
| `document_id` | INTEGER | FOREIGN KEY (`documents.id`), NULLABLE, INDEX | Originating document |
| `user_id` | INTEGER | FOREIGN KEY (`users.id`), NOT NULL, INDEX | Owner patient identifier |
| `medication_name` | VARCHAR(255) | NOT NULL, INDEX | Medication / drug name |
| `dosage` | VARCHAR(100) | NULLABLE | Prescribed dosage (e.g. `500mg`) |
| `frequency` | VARCHAR(100) | NULLABLE | Dosage frequency (e.g. `Twice daily`, `1-0-1`) |
| `timing_instructions` | VARCHAR(255) | NULLABLE | Timing relation to food (e.g. `After food`) |
| `duration` | VARCHAR(100) | NULLABLE | Prescription duration (e.g. `7 days`) |
| `doctor_name` | VARCHAR(255) | NULLABLE | Prescribing physician |
| `prescribed_date` | VARCHAR(50) | NULLABLE, INDEX | Prescription date |
| `created_at` | DATETIME | NOT NULL | Record creation timestamp |

### 5. `vital_records` (Patient Vital Signs)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Vital record identifier |
| `user_id` | INTEGER | FOREIGN KEY (`users.id`), NOT NULL, INDEX | Owner patient identifier |
| `record_date` | VARCHAR(50) | NOT NULL, INDEX | Measurement date |
| `blood_pressure_systolic` | INTEGER | NULLABLE | Systolic BP (mmHg) |
| `blood_pressure_diastolic` | INTEGER | NULLABLE | Diastolic BP (mmHg) |
| `heart_rate` | INTEGER | NULLABLE | Heart rate (bpm) |
| `blood_glucose_fasting` | FLOAT | NULLABLE | Fasting glucose (mg/dL) |
| `blood_glucose_postprandial` | FLOAT | NULLABLE | Postprandial glucose (mg/dL) |
| `hba1c` | FLOAT | NULLABLE | Glycated hemoglobin (%) |
| `weight_kg` | FLOAT | NULLABLE | Body weight (kg) |
| `height_cm` | FLOAT | NULLABLE | Height (cm) |
| `bmi` | FLOAT | NULLABLE | Body Mass Index |
| `oxygen_saturation_spo2` | FLOAT | NULLABLE | Oxygen saturation (%) |
| `temperature_c` | FLOAT | NULLABLE | Body temperature (°C) |

### 6. `medication_reminders` (Medication Reminders)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Reminder identifier |
| `user_id` | INTEGER | FOREIGN KEY (`users.id`), NOT NULL, INDEX | Owner patient identifier |
| `prescription_id` | INTEGER | FOREIGN KEY (`prescriptions.id`), NULLABLE | Originating prescription |
| `document_id` | INTEGER | FOREIGN KEY (`documents.id`), NULLABLE | Originating document |
| `medicine_name` | VARCHAR(255) | NOT NULL, INDEX | Drug name |
| `dosage` | VARCHAR(100) | NULLABLE | Dosage string |
| `frequency` | VARCHAR(100) | NULLABLE | Frequency |
| `timing` | VARCHAR(255) | NULLABLE | Timing (Morning, Afternoon, Night) |
| `scheduled_time` | VARCHAR(50) | NULLABLE | Time string (e.g. `8:00 AM`) |
| `status` | VARCHAR(50) | DEFAULT 'PENDING', INDEX | State (`PENDING`, `COMPLETED`, `SNOOZED`) |
| `enabled` | BOOLEAN | DEFAULT TRUE | Active toggle |

### 7. `notifications` (In-App Notifications)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Notification identifier |
| `user_id` | INTEGER | FOREIGN KEY (`users.id`), NOT NULL, INDEX | Recipient patient identifier |
| `type` | VARCHAR(50) | NOT NULL, INDEX | Notification category |
| `title` | VARCHAR(255) | NOT NULL | Notification title |
| `message` | TEXT | NOT NULL | Privacy-safe notification body |
| `is_read` | BOOLEAN | DEFAULT FALSE, INDEX | Read status flag |
| `created_at` | DATETIME | NOT NULL, INDEX | Notification timestamp |

### 8. `shared_links` (Secure Record Sharing)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Share link identifier |
| `user_id` | INTEGER | FOREIGN KEY (`users.id`), NOT NULL, INDEX | Owner patient identifier |
| `share_token` | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | Cryptographically secure token |
| `recipient_name` | VARCHAR(255) | NULLABLE | Intended doctor/clinician name |
| `access_level` | VARCHAR(50) | DEFAULT 'read_only' | Access scope |
| `document_ids_json` | JSON | NOT NULL | Array of explicitly permitted document IDs |
| `pin_hash` | VARCHAR(255) | NULLABLE | Optional Bcrypt-hashed access PIN |
| `expires_at` | DATETIME | NOT NULL, INDEX | Token expiration timestamp (UTC) |
| `is_revoked` | BOOLEAN | DEFAULT FALSE, INDEX | Immediate revocation toggle |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |

### 9. `audit_logs` (Security & Privacy Audit Trail)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Log entry identifier |
| `user_id` | INTEGER | FOREIGN KEY (`users.id`), NULLABLE, INDEX | Acting user identifier |
| `action` | VARCHAR(100) | NOT NULL, INDEX | Action performed (`LOGIN`, `UPLOAD`, `AI_QUERY`, etc.) |
| `resource_type` | VARCHAR(100) | NOT NULL | Targeted resource |
| `resource_id` | VARCHAR(100) | NULLABLE | Resource identifier |
| `ip_address` | VARCHAR(50) | NULLABLE | Client IP address |
| `user_agent` | VARCHAR(255) | NULLABLE | Client User-Agent string |
| `details` | JSON | NULLABLE | Non-PII event metadata |
| `timestamp` | DATETIME | NOT NULL, INDEX | Audit timestamp (UTC) |

### 10. `rag_chunks` (User Document Text Chunks)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Chunk identifier |
| `document_id` | INTEGER | FOREIGN KEY (`documents.id`), NOT NULL, INDEX | Source document |
| `user_id` | INTEGER | FOREIGN KEY (`users.id`), NOT NULL, INDEX | Owner patient identifier |
| `chunk_index` | INTEGER | NOT NULL | Chunk sequence index |
| `page_number` | INTEGER | DEFAULT 1 | Originating PDF page number |
| `content` | TEXT | NOT NULL | Clean OCR text segment |

### 11. `medical_knowledge_chunks` (Curated Medical QA Dataset)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Chunk identifier |
| `dataset_name` | VARCHAR(255) | NOT NULL, INDEX | Source dataset (`Malikeh1375/...`) |
| `license` | VARCHAR(100) | NOT NULL | License (`MIT`) |
| `input_question` | TEXT | NOT NULL | Clinical medical inquiry |
| `output_answer` | TEXT | NOT NULL | Curated clinical definition answer |
| `content` | TEXT | NOT NULL | Searchable Q&A text |

### 12. `nutrition_food_items` (USDA Foundation Foods Dataset)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Food item identifier |
| `fdc_id` | INTEGER | UNIQUE, NOT NULL, INDEX | USDA FoodData Central FDC ID |
| `food_name` | VARCHAR(255) | NOT NULL, INDEX | Scientific food name |
| `common_name` | VARCHAR(255) | NULLABLE, INDEX | Accessible common food name |
| `food_category` | VARCHAR(100) | NOT NULL, INDEX | Food group category |
| `serving_size` | FLOAT | DEFAULT 100.0 | Standard reference portion |
| `serving_unit` | VARCHAR(20) | DEFAULT 'g' | Reference portion unit |
| `nutrients` | JSON | NOT NULL | Complete macro/micronutrient breakdown |
| `license` | VARCHAR(100) | DEFAULT 'Public Domain / CC0-1.0' | Open data license |

---

## 3. Data Integrity & Cross-User Isolation Guarantees

1. **Foreign Key Integrity**: All documents, tests, prescriptions, reminders, and audit records link to `users.id` with strict database-level constraints.
2. **Deterministic Filter Isolation**: Every database query in all services (`hybrid_rag_service`, `health_timeline_service`, `global_search_service`, `reminder_service`, `notification_service`, `health_intelligence_service`) strictly injects `filter(Model.user_id == current_user.id)`.
3. **SHA-256 Vault Deduplication**: Uploaded documents are fingerprinted with SHA-256 to prevent duplicate file uploads and maintain data provenance.
4. **Audit Immutability**: Audit log records are append-only. No raw medical text, passwords, or PII are written to the audit log table.
