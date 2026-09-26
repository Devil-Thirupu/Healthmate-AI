-- ==============================================================================
-- HEALTHMATE AI — Row Level Security (RLS) Policies
-- ==============================================================================
-- Run this SQL in: Supabase Dashboard → SQL Editor
--
-- Architecture note:
--   FastAPI backend uses the service_role key which BYPASSES RLS.
--   These policies protect against:
--     1. Direct table access from the frontend (anon/authenticated Supabase tokens)
--     2. Any accidental public exposure of medical data
--     3. Cross-user data leakage if a Supabase token is used directly
--
-- Since FastAPI manages its own JWT auth and user_id filtering in queries,
-- the RLS policies here are a defence-in-depth layer.
-- ==============================================================================

-- Enable RLS on all user-owned tables
ALTER TABLE users                   ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents               ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescriptions           ENABLE ROW LEVEL SECURITY;
ALTER TABLE lab_tests               ENABLE ROW LEVEL SECURITY;
ALTER TABLE vital_records           ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_chunks              ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_knowledge_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescription_extractions ENABLE ROW LEVEL SECURITY;
ALTER TABLE extraction_corrections  ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointment_summaries   ENABLE ROW LEVEL SECURITY;
ALTER TABLE nutrition_foods         ENABLE ROW LEVEL SECURITY;
ALTER TABLE medication_reminders    ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications           ENABLE ROW LEVEL SECURITY;
ALTER TABLE shared_links            ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs              ENABLE ROW LEVEL SECURITY;

-- ==============================================================================
-- users: only the user themselves can see/update their own row
-- ==============================================================================
CREATE POLICY "users_select_own" ON users
  FOR SELECT USING (id::text = auth.uid()::text);

CREATE POLICY "users_update_own" ON users
  FOR UPDATE USING (id::text = auth.uid()::text);

-- ==============================================================================
-- documents: user can only access their own documents
-- ==============================================================================
CREATE POLICY "documents_select_own" ON documents
  FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "documents_insert_own" ON documents
  FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY "documents_update_own" ON documents
  FOR UPDATE USING (user_id::text = auth.uid()::text);

CREATE POLICY "documents_delete_own" ON documents
  FOR DELETE USING (user_id::text = auth.uid()::text);

-- ==============================================================================
-- prescriptions
-- ==============================================================================
CREATE POLICY "prescriptions_select_own" ON prescriptions
  FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "prescriptions_insert_own" ON prescriptions
  FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY "prescriptions_update_own" ON prescriptions
  FOR UPDATE USING (user_id::text = auth.uid()::text);

CREATE POLICY "prescriptions_delete_own" ON prescriptions
  FOR DELETE USING (user_id::text = auth.uid()::text);

-- ==============================================================================
-- lab_tests
-- ==============================================================================
CREATE POLICY "lab_tests_select_own" ON lab_tests
  FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "lab_tests_insert_own" ON lab_tests
  FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY "lab_tests_update_own" ON lab_tests
  FOR UPDATE USING (user_id::text = auth.uid()::text);

CREATE POLICY "lab_tests_delete_own" ON lab_tests
  FOR DELETE USING (user_id::text = auth.uid()::text);

-- ==============================================================================
-- vital_records
-- ==============================================================================
CREATE POLICY "vitals_select_own" ON vital_records
  FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "vitals_insert_own" ON vital_records
  FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY "vitals_update_own" ON vital_records
  FOR UPDATE USING (user_id::text = auth.uid()::text);

CREATE POLICY "vitals_delete_own" ON vital_records
  FOR DELETE USING (user_id::text = auth.uid()::text);

-- ==============================================================================
-- rag_chunks (user-document embeddings)
-- ==============================================================================
CREATE POLICY "rag_chunks_select_own" ON rag_chunks
  FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "rag_chunks_insert_own" ON rag_chunks
  FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY "rag_chunks_delete_own" ON rag_chunks
  FOR DELETE USING (user_id::text = auth.uid()::text);

-- ==============================================================================
-- medical_knowledge_chunks (global read-only reference data)
-- ==============================================================================
CREATE POLICY "knowledge_select_all_authenticated" ON medical_knowledge_chunks
  FOR SELECT USING (auth.role() = 'authenticated');

-- ==============================================================================
-- prescription_extractions
-- ==============================================================================
CREATE POLICY "extractions_select_own" ON prescription_extractions
  FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "extractions_insert_own" ON prescription_extractions
  FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY "extractions_update_own" ON prescription_extractions
  FOR UPDATE USING (user_id::text = auth.uid()::text);

-- ==============================================================================
-- extraction_corrections
-- ==============================================================================
CREATE POLICY "corrections_select_own" ON extraction_corrections
  FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "corrections_insert_own" ON extraction_corrections
  FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

-- ==============================================================================
-- appointment_summaries
-- ==============================================================================
CREATE POLICY "appt_summaries_select_own" ON appointment_summaries
  FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "appt_summaries_insert_own" ON appointment_summaries
  FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY "appt_summaries_update_own" ON appointment_summaries
  FOR UPDATE USING (user_id::text = auth.uid()::text);

CREATE POLICY "appt_summaries_delete_own" ON appointment_summaries
  FOR DELETE USING (user_id::text = auth.uid()::text);

-- ==============================================================================
-- nutrition_foods (global, read-only reference data)
-- ==============================================================================
CREATE POLICY "nutrition_select_all_authenticated" ON nutrition_foods
  FOR SELECT USING (auth.role() = 'authenticated');

-- ==============================================================================
-- medication_reminders
-- ==============================================================================
CREATE POLICY "reminders_select_own" ON medication_reminders
  FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "reminders_insert_own" ON medication_reminders
  FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY "reminders_update_own" ON medication_reminders
  FOR UPDATE USING (user_id::text = auth.uid()::text);

CREATE POLICY "reminders_delete_own" ON medication_reminders
  FOR DELETE USING (user_id::text = auth.uid()::text);

-- ==============================================================================
-- notifications
-- ==============================================================================
CREATE POLICY "notifications_select_own" ON notifications
  FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "notifications_update_own" ON notifications
  FOR UPDATE USING (user_id::text = auth.uid()::text);

-- ==============================================================================
-- shared_links
-- Owners can manage their own links.
-- Public access to a share is checked at the app layer (token + expiry + PIN).
-- No policy allows arbitrary authenticated users to read all shared_links.
-- ==============================================================================
CREATE POLICY "shared_links_select_own" ON shared_links
  FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "shared_links_insert_own" ON shared_links
  FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY "shared_links_update_own" ON shared_links
  FOR UPDATE USING (user_id::text = auth.uid()::text);

CREATE POLICY "shared_links_delete_own" ON shared_links
  FOR DELETE USING (user_id::text = auth.uid()::text);

-- ==============================================================================
-- audit_logs (append-only; users can read own logs, no update/delete)
-- ==============================================================================
CREATE POLICY "audit_logs_select_own" ON audit_logs
  FOR SELECT USING (user_id::text = auth.uid()::text);

-- ==============================================================================
-- Supabase Storage bucket policies (run in Dashboard → Storage → Policies)
-- OR apply via this SQL:
-- ==============================================================================

-- medical-documents: only the file owner (path prefix user_{id}/) can access
-- (These policies reference storage.objects table)

-- Insert (upload)
CREATE POLICY "medical_docs_insert_own" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'medical-documents'
    AND (storage.foldername(name))[1] = 'user_' || auth.uid()::text
  );

-- Select (download/preview — backend issues signed URLs instead)
CREATE POLICY "medical_docs_select_own" ON storage.objects
  FOR SELECT USING (
    bucket_id = 'medical-documents'
    AND (storage.foldername(name))[1] = 'user_' || auth.uid()::text
  );

-- Delete
CREATE POLICY "medical_docs_delete_own" ON storage.objects
  FOR DELETE USING (
    bucket_id = 'medical-documents'
    AND (storage.foldername(name))[1] = 'user_' || auth.uid()::text
  );

-- Repeat for prescriptions bucket
CREATE POLICY "prescriptions_bucket_insert_own" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'prescriptions'
    AND (storage.foldername(name))[1] = 'user_' || auth.uid()::text
  );

CREATE POLICY "prescriptions_bucket_select_own" ON storage.objects
  FOR SELECT USING (
    bucket_id = 'prescriptions'
    AND (storage.foldername(name))[1] = 'user_' || auth.uid()::text
  );

CREATE POLICY "prescriptions_bucket_delete_own" ON storage.objects
  FOR DELETE USING (
    bucket_id = 'prescriptions'
    AND (storage.foldername(name))[1] = 'user_' || auth.uid()::text
  );

-- medical-images bucket
CREATE POLICY "medical_images_insert_own" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'medical-images'
    AND (storage.foldername(name))[1] = 'user_' || auth.uid()::text
  );

CREATE POLICY "medical_images_select_own" ON storage.objects
  FOR SELECT USING (
    bucket_id = 'medical-images'
    AND (storage.foldername(name))[1] = 'user_' || auth.uid()::text
  );

CREATE POLICY "medical_images_delete_own" ON storage.objects
  FOR DELETE USING (
    bucket_id = 'medical-images'
    AND (storage.foldername(name))[1] = 'user_' || auth.uid()::text
  );

-- appointment-pdfs bucket
CREATE POLICY "appt_pdfs_insert_own" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'appointment-pdfs'
    AND (storage.foldername(name))[1] = 'user_' || auth.uid()::text
  );

CREATE POLICY "appt_pdfs_select_own" ON storage.objects
  FOR SELECT USING (
    bucket_id = 'appointment-pdfs'
    AND (storage.foldername(name))[1] = 'user_' || auth.uid()::text
  );

CREATE POLICY "appt_pdfs_delete_own" ON storage.objects
  FOR DELETE USING (
    bucket_id = 'appointment-pdfs'
    AND (storage.foldername(name))[1] = 'user_' || auth.uid()::text
  );
