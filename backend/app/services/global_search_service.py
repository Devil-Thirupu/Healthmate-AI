import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from backend.app.models.document import Document
from backend.app.models.clinical import LabTest, Prescription, VitalRecord
from backend.app.models.rag import RAGChunk
from backend.app.models.appointment_summary import AppointmentSummary
from backend.app.services.evidence_guard_service import evidence_guard_service

class GlobalSearchService:
    """
    HealthMate AI Hybrid Global Search Engine (Phase 14)
    ===================================================
    Combines:
      1. Structured Database Search (Exact test names, medicine names, dates, values, document titles)
      2. Semantic & Lexical Document OCR Chunk Search (RAGChunk)
    Enforces strict user isolation.
    """

    def search_health_records(
        self,
        db: Session,
        user_id: int,
        query: str,
        limit: int = 30
    ) -> Dict[str, Any]:
        """
        Executes unified hybrid health record search strictly for user_id.
        """
        if not query or not query.strip():
            return {
                "query": "",
                "total_results": 0,
                "structured_count": 0,
                "semantic_count": 0,
                "results": []
            }

        q_clean = query.strip().lower()
        q_tokens = [w for w in re.findall(r'\w+', q_clean) if len(w) >= 2]

        results = []
        structured_count = 0
        semantic_count = 0

        # Fetch all documents for user to map titles
        docs = db.query(Document).filter(Document.user_id == user_id).all()
        doc_map = {d.id: d for d in docs}

        # 1. Search Lab Tests (Structured)
        lab_tests = db.query(LabTest).filter(LabTest.user_id == user_id).all()
        for t in lab_tests:
            t_name = t.test_name.lower()
            c_name = (t.canonical_name or "").lower()
            t_val = str(t.observed_value).lower()
            doc = doc_map.get(t.document_id)
            d_date = (t.test_date or (doc.document_date if doc else "")).lower()

            matches = any(tok in t_name or tok in c_name or tok in t_val or tok in d_date for tok in q_tokens)
            if matches or q_clean in t_name or q_clean in c_name:
                structured_count += 1
                ref_str = f" [Ref: {t.reference_range_text}]" if t.reference_range_text else ""
                results.append({
                    "result_type": "LAB_TEST",
                    "title": t.test_name,
                    "subtitle": f"Value: {t.observed_value} {t.unit or ''} (Flag: {t.flag.upper()}){ref_str}",
                    "value": f"{t.observed_value} {t.unit or ''}".strip(),
                    "date": t.test_date or (doc.document_date if doc else "Undated"),
                    "source_document_id": t.document_id,
                    "source_document_title": doc.title if doc else "Lab Report",
                    "source_page_number": 1,
                    "snippet": t.original_ocr_snippet or f"{t.test_name}: {t.observed_value} {t.unit or ''}",
                    "relevance_score": 1.5
                })

        # 2. Search Prescriptions (Structured)
        prescriptions = db.query(Prescription).filter(Prescription.user_id == user_id).all()
        for rx in prescriptions:
            m_name = rx.medication_name.lower()
            freq = (rx.frequency or "").lower()
            timing = (rx.timing_instructions or "").lower()
            doc = doc_map.get(rx.document_id)
            d_date = (rx.prescribed_date or (doc.document_date if doc else "")).lower()

            matches = any(tok in m_name or tok in freq or tok in timing or tok in d_date for tok in q_tokens)
            if matches or q_clean in m_name or "prescription" in q_clean:
                structured_count += 1
                dose_str = f" {rx.dosage}" if rx.dosage else ""
                results.append({
                    "result_type": "PRESCRIPTION",
                    "title": f"Rx {rx.medication_name}{dose_str}",
                    "subtitle": f"Frequency: {rx.frequency or 'Standard'} • Timing: {rx.timing_instructions or 'As prescribed'}",
                    "value": rx.dosage or "Prescribed",
                    "date": rx.prescribed_date or (doc.document_date if doc else "Undated"),
                    "source_document_id": rx.document_id,
                    "source_document_title": doc.title if doc else "Prescription Record",
                    "source_page_number": 1,
                    "snippet": rx.original_ocr_snippet or f"Rx: {rx.medication_name} {rx.dosage or ''}",
                    "relevance_score": 1.4
                })

        # 3. Search Documents (Structured)
        for doc in docs:
            d_title = doc.title.lower()
            d_fname = doc.original_filename.lower()
            d_cat = doc.category.lower()
            d_date = (doc.document_date or "").lower()
            d_clinic = (doc.clinic_or_lab or "").lower()
            d_doctor = (doc.doctor_name or "").lower()

            matches = any(tok in d_title or tok in d_fname or tok in d_cat or tok in d_date or tok in d_clinic or tok in d_doctor for tok in q_tokens)
            if matches or q_clean in d_title or q_clean in d_cat:
                structured_count += 1
                results.append({
                    "result_type": "DOCUMENT",
                    "title": doc.title,
                    "subtitle": f"Category: {doc.category.replace('_', ' ').title()} • Date: {doc.document_date or 'Undated'}",
                    "value": doc.category,
                    "date": doc.document_date or doc.created_at.strftime("%Y-%m-%d"),
                    "source_document_id": doc.id,
                    "source_document_title": doc.title,
                    "source_page_number": 1,
                    "snippet": doc.ocr_raw_text[:200] if doc.ocr_raw_text else doc.title,
                    "relevance_score": 1.3
                })

        # 4. Search Document OCR Semantic Chunks (RAGChunk)
        chunks = db.query(RAGChunk).filter(RAGChunk.user_id == user_id).all()
        for c in chunks:
            c_text = c.content.lower()
            matches_count = sum(1 for tok in q_tokens if tok in c_text)
            if matches_count > 0:
                semantic_count += 1
                doc = doc_map.get(c.document_id)
                results.append({
                    "result_type": "DOCUMENT_CHUNK",
                    "title": f"Report Content — {doc.title if doc else 'Document'}",
                    "subtitle": f"Page {c.page_number or 1} Match ({matches_count} matching terms)",
                    "value": None,
                    "date": doc.document_date if doc else None,
                    "source_document_id": c.document_id,
                    "source_document_title": doc.title if doc else "Uploaded Report",
                    "source_page_number": c.page_number or 1,
                    "snippet": c.content.strip()[:250],
                    "relevance_score": 1.0 + (matches_count * 0.1)
                })

        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        results = results[:limit]

        return {
            "query": query,
            "total_results": len(results),
            "structured_count": structured_count,
            "semantic_count": semantic_count,
            "results": results
        }

global_search_service = GlobalSearchService()
