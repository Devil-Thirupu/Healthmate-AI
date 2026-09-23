import re
import math
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_

from backend.app.models.clinical import LabTest, Prescription, VitalRecord
from backend.app.models.document import Document
from backend.app.models.rag import RAGChunk, MedicalKnowledgeChunk
from backend.app.schemas.assistant import CitationItem, ChatQueryResponse, KnowledgeSourceInfo
from backend.app.services.evidence_guard_service import evidence_guard_service
from backend.app.services.multilingual_explanation_service import multilingual_explanation_service
from backend.app.services.health_intelligence_service import health_intelligence_service
from backend.app.core.logging import logger

class HybridRAGService:
    """
    HealthMate AI Hybrid RAG Engine (Phase 14.1 Grounded Clinical Assistant)
    ========================================================================
    Evidence Priority:
      USER STRUCTURED RECORDS > USER DOCUMENT CHUNKS > GENERAL MEDICAL KNOWLEDGE > GENERAL NUTRITION KNOWLEDGE.

    Strict Safety & Retrieval Rules:
      1. Patient queries prioritize verified user database records (LabTest, Prescription, VitalRecord, Document).
      2. Broad queries ("What are my latest values?") return actual stored latest values grouped by biomarker.
      3. Date and month queries ("What was my glucose in March?") filter records by date/month and do NOT guess.
      4. General medical knowledge (Medical QA) is queried ONLY for general or hybrid conceptual questions.
      5. Irrelevant RAG chunks are rejected. Missing patient records produce standard insufficient evidence responses.
      6. Zero AI hallucination, zero personal causality claims, zero invented values.
    """

    MONTH_NAMES = {
        "january": 1, "jan": 1, "01": 1,
        "february": 2, "feb": 2, "02": 2,
        "march": 3, "mar": 3, "03": 3,
        "april": 4, "apr": 4, "04": 4,
        "may": 5, "05": 5,
        "june": 6, "jun": 6, "06": 6,
        "july": 7, "jul": 7, "07": 7,
        "august": 8, "aug": 8, "08": 8,
        "september": 9, "sep": 9, "sept": 9, "09": 9,
        "october": 10, "oct": 10, "10": 10,
        "november": 11, "nov": 11, "11": 11,
        "december": 12, "dec": 12, "12": 12
    }

    def parse_date_query_filter(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Parses date, month name, or year patterns from query text:
        e.g. 'March', 'in March', 'Jan 2026', '2026-03', '20 March 2026', '20/03/2026'
        """
        q_lower = query.lower()
        
        # Check for year
        year_match = re.search(r'\b(202[0-9])\b', q_lower)
        year_str = year_match.group(1) if year_match else None

        # Check for month
        detected_month_num = None
        detected_month_name = None
        for m_name, m_num in self.MONTH_NAMES.items():
            if re.search(rf'\b{m_name}\b', q_lower):
                detected_month_num = m_num
                detected_month_name = m_name.capitalize()
                break

        # Check for ISO or numeric date (e.g. 2026-03, 20/03/2026, 20-03-2026)
        iso_match = re.search(r'\b(202[0-9])[-/](0[1-9]|1[0-2])(?:[-/](0[1-9]|[12][0-9]|3[01]))?\b', q_lower)
        if iso_match:
            year_str = iso_match.group(1)
            detected_month_num = int(iso_match.group(2))

        dmy_match = re.search(r'\b(0[1-9]|[12][0-9]|3[01])[-/](0[1-9]|1[0-2])[-/](202[0-9])\b', q_lower)
        if dmy_match:
            detected_month_num = int(dmy_match.group(2))
            year_str = dmy_match.group(3)

        if detected_month_num or year_str:
            return {
                "month_num": detected_month_num,
                "month_name": detected_month_name,
                "year": year_str
            }
        return None

    def classify_query(self, query: str) -> str:
        """
        Classifies query intent into:
        - 'PATIENT_FACTUAL' (e.g. "What are my latest values?", "What was my glucose in March?")
        - 'PATIENT_MEDICATIONS' (e.g. "What medicines am I taking?", "Show my prescriptions")
        - 'PATIENT_CHANGES' (e.g. "What changed?", "What changed from my previous report?")
        - 'DOCUMENT_SEARCH' (e.g. "What is in my latest report?", "Explain my report")
        - 'GENERAL_MEDICAL_KNOWLEDGE' (e.g. "What is glucose?", "What does HbA1c measure?")
        - 'HYBRID' (e.g. "My glucose changed from 100 to 105. What does that mean?")
        """
        q_lower = query.lower().strip()

        # Pure General Definition / Knowledge Patterns (No patient pronouns/markers)
        pure_general_patterns = [
            r'^(what is|what does|define|explain what|how does|what are normal ranges for)\s+(glucose|sugar|hba1c|cholesterol|blood pressure|creatinine|hemoglobin|thyroid|tsh|lipid|wbc|platelets|diabetes|hypertension|vitamin)\b',
            r'^what (is|does)\s+[\w\s]+\s+(mean|measure|signify)\??$'
        ]
        is_pure_general = any(bool(re.search(pat, q_lower)) for pat in pure_general_patterns) and not bool(re.search(r'\b(my|mine|me|our|for me|my latest|in my report)\b', q_lower))
        if is_pure_general:
            return "GENERAL_MEDICAL_KNOWLEDGE"

        # Check for explicit patient markers
        has_patient_marker = bool(re.search(r'\b(my|mine|me|for me|my\s+latest|my\s+previous|my\s+active|this\s+report|in\s+report|in\s+my\s+report|what\s+changed|medicines\s+are\s+listed|show\s+my|history|latest\s+values|latest\s+results|my\s+results|my\s+numbers|my\s+tests|blood\s+test\s+results)\b', q_lower))
        has_explanatory_marker = bool(re.search(r'\b(why|how\s+come|what\s+does\s+that\s+mean|what\s+does\s+this\s+mean|explain\s+the\s+change|reason\s+for|changes\s+in)\b', q_lower))
        has_nutrition_marker = bool(re.search(r'\b(nutrition|food|diet|eat|calories|fruit|vegetable)\b', q_lower))
        has_doc_marker = bool(re.search(r'\b(uploaded\s+report|report\s+says|document|pdf|file\s+says|in\s+my\s+report|what\s+is\s+in\s+my\s+report|explain\s+my\s+report|explain\s+this\s+report|show\s+my\s+latest\s+report)\b', q_lower))
        has_med_marker = bool(re.search(r'\b(medicine|medicines|prescription|prescriptions|prescribed|tablet|tablets|drug|drugs|dosage|dose|amoxicillin|metformin|aspirin|paracetamol|statin)\b', q_lower))
        has_change_marker = bool(re.search(r'\b(what\s+changed|changes|compared|previous\s+value|previous\s+glucose|trend|increased|decreased|difference)\b', q_lower))

        if has_patient_marker and has_explanatory_marker:
            return "HYBRID"
        elif has_patient_marker and has_nutrition_marker:
            return "HYBRID"
        elif has_med_marker and (has_patient_marker or "what" in q_lower or "show" in q_lower or "list" in q_lower):
            return "PATIENT_MEDICATIONS"
        elif has_change_marker and (has_patient_marker or "what" in q_lower or "from" in q_lower):
            return "PATIENT_CHANGES"
        elif has_doc_marker:
            return "DOCUMENT_SEARCH"
        elif has_patient_marker:
            return "PATIENT_FACTUAL"
        elif has_nutrition_marker:
            return "GENERAL_MEDICAL_KNOWLEDGE"
        elif q_lower.startswith(("what is", "what are", "define", "explain what", "how does", "why is", "symptoms of", "causes of", "treatment for", "normal range")):
            return "GENERAL_MEDICAL_KNOWLEDGE"
        else:
            return "PATIENT_FACTUAL"

    def compute_lexical_score(self, query_tokens: List[str], text: str) -> float:
        """Lightweight lexical relevance score with length and frequency weighting."""
        if not text or not query_tokens:
            return 0.0
        text_lower = text.lower()
        score = 0.0
        for token in query_tokens:
            if len(token) < 3:
                continue
            count = text_lower.count(token)
            if count > 0:
                score += (1.0 + math.log(count)) * (1.0 + len(token) / 10.0)
        return round(score, 3)

    def _matches_date_filter(self, record_date: Optional[str], date_filter: Optional[Dict[str, Any]]) -> bool:
        """Checks if a record's date string matches the query's month/year constraints."""
        if not date_filter or not record_date:
            return True
        r_lower = record_date.lower()

        # Check year if specified
        if date_filter.get("year"):
            if date_filter["year"] not in r_lower:
                return False

        # Check month if specified
        month_num = date_filter.get("month_num")
        if month_num:
            month_name = date_filter.get("month_name", "").lower()
            m_padded = f"-{month_num:02d}-"
            m_slash = f"/{month_num:02d}/"
            m_dmy_dash = f"-{month_num:02d}"
            m_dmy_slash = f"/{month_num:02d}"
            
            has_month = (
                (month_name and month_name in r_lower) or
                m_padded in r_lower or
                m_slash in r_lower or
                r_lower.endswith(m_dmy_dash) or
                r_lower.endswith(m_dmy_slash) or
                f"-{month_num:02d}" in r_lower or
                f"/{month_num:02d}" in r_lower
            )
            if not has_month:
                return False
        return True

    def retrieve_user_structured(self, db: Session, user_id: int, query: str, query_type: str) -> List[Dict[str, Any]]:
        """
        Retrieves verified structured measurements, prescriptions, or changes strictly for user_id.
        """
        q_lower = query.lower()
        results = []
        date_filter = self.parse_date_query_filter(query)

        # 1. Handle Changes Query ("What changed from my previous report?")
        if query_type == "PATIENT_CHANGES" or "what changed" in q_lower:
            summary = health_intelligence_service.get_user_health_intelligence_summary(db, user_id)
            recent_changes = summary.get("recent_changes", [])
            for c in recent_changes:
                doc = db.query(Document).filter(Document.id == c.get("latest_doc_id")).first() if c.get("latest_doc_id") else None
                doc_title = doc.title if doc else "Diagnostic Report"
                date_str = c.get("latest_date") or (doc.document_date if doc else "Recent")
                
                snippet = f"{c['test_name']}: {c.get('previous_value')} {c.get('unit','')} \u2192 {c.get('latest_value')} {c.get('unit','')} ({c.get('percentage_change')}) [{c.get('trend_direction')}]"
                results.append({
                    "source_type": "USER_STRUCTURED_RECORD",
                    "source_name": doc_title,
                    "record_id": f"change_{c.get('canonical_name', c['test_name'])}",
                    "user_id": user_id,
                    "document_id": c.get("latest_doc_id"),
                    "page_number": 1,
                    "text_snippet": snippet,
                    "relevance_score": 1.5,
                    "data": {
                        "type": "change",
                        "test_name": c["test_name"],
                        "previous_value": c.get("previous_value"),
                        "latest_value": c.get("latest_value"),
                        "unit": c.get("unit"),
                        "percentage_change": c.get("percentage_change"),
                        "trend_direction": c.get("trend_direction"),
                        "date": date_str
                    }
                })

        # 2. Search Prescriptions if query mentions medication / prescription or is broad
        is_med_query = query_type == "PATIENT_MEDICATIONS" or any(w in q_lower for w in ["medicine", "prescription", "prescribed", "tablet", "dosage", "drug", "dose"])
        if is_med_query or query_type == "PATIENT_FACTUAL":
            rxs = db.query(Prescription).filter(Prescription.user_id == user_id).order_by(desc(Prescription.prescribed_date), desc(Prescription.created_at)).all()
            for rx in rxs:
                m_name = rx.medication_name.lower()
                matches_rx = is_med_query or m_name in q_lower

                if matches_rx:
                    doc = db.query(Document).filter(Document.id == rx.document_id).first() if rx.document_id else None
                    date_str = rx.prescribed_date or (doc.document_date if doc else "Undated")
                    
                    if date_filter and not self._matches_date_filter(date_str, date_filter):
                        continue

                    doc_title = doc.title if doc else "Prescription Record"
                    snippet = f"Rx: {rx.medication_name} {rx.dosage or ''} — Frequency: {rx.frequency or 'Standard'}, Timing: {rx.timing_instructions or 'As directed'}, Duration: {rx.duration or 'Standard'}"
                    
                    results.append({
                        "source_type": "USER_STRUCTURED_RECORD",
                        "source_name": doc_title,
                        "record_id": f"prescription_{rx.id}",
                        "user_id": user_id,
                        "document_id": rx.document_id,
                        "page_number": 1,
                        "text_snippet": snippet,
                        "relevance_score": 1.4,
                        "data": {
                            "type": "prescription",
                            "medication_name": rx.medication_name,
                            "dosage": rx.dosage or "Not available in the record",
                            "frequency": rx.frequency or "Standard frequency",
                            "timing": rx.timing_instructions or "As prescribed",
                            "duration": rx.duration or "As prescribed",
                            "doctor": rx.doctor_name,
                            "date": date_str
                        }
                    })

        # 3. Canonical metric mapping for specific clinical tests
        metric_keywords = {
            "glucose": ["glucose", "sugar", "fbs", "rbs", "ppbs", "fasting blood glucose", "fasting blood sugar"],
            "hba1c": ["hba1c", "glycated hemoglobin", "a1c"],
            "cholesterol": ["cholesterol", "total cholesterol", "lipid", "ldl", "hdl", "triglycerides", "vldl"],
            "creatinine": ["creatinine", "kidney", "renal"],
            "urea": ["urea", "bun"],
            "hemoglobin": ["hemoglobin", "hb", "cbc"],
            "wbc": ["wbc", "white blood", "leukocyte"],
            "platelet": ["platelet", "thrombocyte"],
            "thyroid": ["thyroid", "tsh", "t3", "t4"],
            "tsh": ["tsh", "thyroid stimulating hormone"]
        }

        requested_metrics = set()
        for metric, aliases in metric_keywords.items():
            if any(re.search(rf'\b{re.escape(alias)}\b', q_lower) for alias in aliases):
                requested_metrics.add(metric)

        is_broad_latest_query = bool(re.search(r'\b(latest\s+values|latest\s+results|all\s+values|latest\s+tests|blood\s+tests|my\s+results|my\s+numbers|my\s+tests|what\s+are\s+my\s+values)\b', q_lower)) or (not requested_metrics and query_type == "PATIENT_FACTUAL" and not is_med_query)

        # Fetch all lab tests for user ordered chronologically (newest first)
        tests = db.query(LabTest).filter(LabTest.user_id == user_id).order_by(desc(LabTest.test_date), desc(LabTest.created_at)).all()

        if is_broad_latest_query and not date_filter:
            # Dedup by test name, retaining latest measurement for each test
            seen_tests = set()
            for t in tests:
                key = (t.canonical_name or t.test_name).lower()
                if key in seen_tests:
                    continue
                seen_tests.add(key)

                doc = db.query(Document).filter(Document.id == t.document_id).first() if t.document_id else None
                doc_title = doc.title if doc else "Diagnostic Report"
                date_str = t.test_date or (doc.document_date if doc else "Recent")
                ref_str = f" [Ref: {t.reference_range_text}]" if t.reference_range_text else ""
                snippet = f"{t.test_name}: {t.observed_value} {t.unit or ''} (Date: {date_str}, Flag: {t.flag}){ref_str}"

                results.append({
                    "source_type": "USER_STRUCTURED_RECORD",
                    "source_name": doc_title,
                    "record_id": f"lab_test_{t.id}",
                    "user_id": user_id,
                    "document_id": t.document_id,
                    "page_number": 1,
                    "text_snippet": snippet,
                    "relevance_score": 1.5,
                    "data": {
                        "type": "lab_test",
                        "test_name": t.test_name,
                        "value": t.observed_value,
                        "unit": t.unit,
                        "date": date_str,
                        "flag": t.flag,
                        "ref_range": t.reference_range_text
                    }
                })

            # Also add latest vitals if available
            vitals = db.query(VitalRecord).filter(VitalRecord.user_id == user_id).order_by(desc(VitalRecord.record_date), desc(VitalRecord.created_at)).first()
            if vitals and vitals.blood_pressure_systolic:
                results.append({
                    "source_type": "USER_STRUCTURED_RECORD",
                    "source_name": "Vital Log Record",
                    "record_id": f"vital_{vitals.id}",
                    "user_id": user_id,
                    "document_id": None,
                    "page_number": 1,
                    "text_snippet": f"Blood Pressure: {vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic} mmHg (Date: {vitals.record_date})",
                    "relevance_score": 1.4,
                    "data": {
                        "type": "vital_record",
                        "test_name": "Blood Pressure",
                        "value": f"{vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic}",
                        "unit": "mmHg",
                        "date": vitals.record_date,
                        "flag": "normal"
                    }
                })
            return results

        # Specific metric inquiry with optional date/month filter
        if requested_metrics or not is_med_query:
            for t in tests:
                c_name = (t.canonical_name or "").lower()
                t_name = t.test_name.lower()
                combined_test_str = f"{c_name} {t_name}"

                matches_metric = False
                if requested_metrics:
                    for req in requested_metrics:
                        aliases = metric_keywords[req]
                        if any(alias in combined_test_str for alias in aliases):
                            matches_metric = True
                            break
                else:
                    matches_metric = any(w in combined_test_str for w in re.findall(r'\w+', q_lower) if len(w) >= 3)

                if matches_metric:
                    doc = db.query(Document).filter(Document.id == t.document_id).first() if t.document_id else None
                    date_str = t.test_date or (doc.document_date if doc else "Undated")

                    # Apply date/month filter if requested
                    if date_filter and not self._matches_date_filter(date_str, date_filter):
                        continue

                    doc_title = doc.title if doc else "Diagnostic Report"
                    ref_str = f" [Ref: {t.reference_range_text}]" if t.reference_range_text else ""
                    snippet = f"{t.test_name}: {t.observed_value} {t.unit or ''} (Date: {date_str}, Flag: {t.flag}){ref_str}"
                    
                    results.append({
                        "source_type": "USER_STRUCTURED_RECORD",
                        "source_name": doc_title,
                        "record_id": f"lab_test_{t.id}",
                        "user_id": user_id,
                        "document_id": t.document_id,
                        "page_number": 1,
                        "text_snippet": snippet,
                        "relevance_score": 1.2,
                        "data": {
                            "type": "lab_test",
                            "test_name": t.test_name,
                            "value": t.observed_value,
                            "unit": t.unit,
                            "date": date_str,
                            "flag": t.flag,
                            "ref_range": t.reference_range_text
                        }
                    })

        return results

    def retrieve_user_document_chunks(self, db: Session, user_id: int, query: str, query_type: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Retrieves relevant OCR text chunks from user's uploaded medical documents strictly for user_id."""
        q_tokens = [w for w in re.findall(r'\w+', query.lower()) if len(w) >= 3]
        if not q_tokens:
            return []

        # If it's a document search query (e.g. "What is in my latest report?"), target latest document
        if query_type == "DOCUMENT_SEARCH":
            doc = db.query(Document).filter(Document.user_id == user_id).order_by(desc(Document.created_at)).first()
            if doc:
                chunks = db.query(RAGChunk).filter(RAGChunk.document_id == doc.id, RAGChunk.user_id == user_id).all()
                if chunks:
                    return [{
                        "source_type": "USER_DOCUMENT_CHUNK",
                        "source_name": doc.title,
                        "record_id": f"rag_chunk_{c.id}",
                        "user_id": user_id,
                        "document_id": doc.id,
                        "page_number": c.page_number or 1,
                        "text_snippet": c.content.strip(),
                        "relevance_score": 1.5
                    } for c in chunks[:top_k]]

        chunks = db.query(RAGChunk).filter(RAGChunk.user_id == user_id).all()
        scored_chunks = []

        for c in chunks:
            score = self.compute_lexical_score(q_tokens, c.content)
            # Require minimum relevance score and token match
            if score >= 1.0:
                doc = db.query(Document).filter(Document.id == c.document_id).first() if c.document_id else None
                scored_chunks.append({
                    "source_type": "USER_DOCUMENT_CHUNK",
                    "source_name": doc.title if doc else "Uploaded Document",
                    "record_id": f"rag_chunk_{c.id}",
                    "user_id": user_id,
                    "document_id": c.document_id,
                    "page_number": c.page_number or 1,
                    "text_snippet": c.content.strip(),
                    "relevance_score": score
                })

        scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_chunks[:top_k]

    def retrieve_general_knowledge(self, db: Session, query: str, query_type: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves general medical knowledge Q&A from MedicalKnowledgeChunk collection.
        ONLY executed for GENERAL_MEDICAL_KNOWLEDGE and HYBRID query types.
        """
        if query_type not in {"GENERAL_MEDICAL_KNOWLEDGE", "HYBRID"}:
            return []

        q_tokens = [w for w in re.findall(r'\w+', query.lower()) if len(w) >= 3]
        if not q_tokens:
            return []

        knowledge_records = db.query(MedicalKnowledgeChunk).all()
        scored_records = []

        for rec in knowledge_records:
            score = self.compute_lexical_score(q_tokens, rec.input_question) * 1.5 + self.compute_lexical_score(q_tokens, rec.output_answer)
            # Relevance threshold to prevent incidental noise
            if score >= 1.5:
                scored_records.append({
                    "source_type": "GENERAL_MEDICAL_KNOWLEDGE",
                    "source_name": rec.dataset_name,
                    "record_id": f"med_qa_{rec.id}",
                    "document_id": None,
                    "page_number": None,
                    "text_snippet": f"Q: {rec.input_question}\nA: {rec.output_answer[:400]}...",
                    "relevance_score": score,
                    "license": rec.license,
                    "data": {
                        "question": rec.input_question,
                        "answer": rec.output_answer
                    }
                })

        scored_records.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_records[:top_k]

    def retrieve_nutrition_knowledge(self, db: Session, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves nutritional profiles from USDA FoodData Central Foundation Foods collection."""
        from backend.app.services.nutrition_service import nutrition_service
        q_tokens = [w for w in re.findall(r'\w+', query.lower()) if len(w) >= 3]
        if not q_tokens:
            return []

        foods = nutrition_service.search_food(db=db, query=query, limit=top_k)
        if not foods and any(w in query.lower() for w in ["fiber", "protein", "potassium", "vitamin", "calcium", "iron"]):
            for n_key in ["fiber_g", "protein_g", "potassium_mg", "vitamin_c_mg", "calcium_mg", "iron_mg"]:
                if n_key.split("_")[0] in query.lower():
                    foods = nutrition_service.search_by_nutrient(db=db, nutrient_key=n_key, limit=top_k)
                    break

        scored_records = []
        for f in foods:
            explanation = nutrition_service.generate_nutrition_explanation(food=f, language="en")
            scored_records.append({
                "source_type": "GENERAL_NUTRITION_KNOWLEDGE",
                "source_name": f"USDA FoodData Central — {f.common_name or f.food_name}",
                "record_id": f"fdc_{f.fdc_id}",
                "document_id": None,
                "page_number": None,
                "text_snippet": explanation[:350],
                "relevance_score": 1.2,
                "license": f.license,
                "data": {
                    "fdc_id": f.fdc_id,
                    "food_name": f.food_name,
                    "common_name": f.common_name,
                    "food": f
                }
            })
        return scored_records

    def generate_grounded_response(
        self,
        query: str,
        query_type: str,
        user_structured: List[Dict[str, Any]],
        user_doc_chunks: List[Dict[str, Any]],
        general_knowledge: List[Dict[str, Any]],
        nutrition_knowledge: List[Dict[str, Any]] = None,
        language: str = "en"
    ) -> Tuple[str, List[CitationItem], str, List[Dict[str, Any]], List[str]]:
        """
        Synthesizes a strictly grounded response adhering to Evidence Priority:
        USER STRUCTURED RECORDS > USER DOCUMENT CHUNKS > GENERAL MEDICAL KNOWLEDGE.
        Returns (answer_text, citations, priority_applied, structured_cards, follow_up_suggestions).
        """
        citations: List[CitationItem] = []
        structured_cards: List[Dict[str, Any]] = []
        follow_ups: List[str] = []
        q_lower = query.lower()
        is_cause_inquiry = bool(re.search(r'\b(why|how come|explain the change|reason for|changes in)\b', q_lower))

        # CASE 1: Patient-Specific Factual Query
        if query_type in {"PATIENT_FACTUAL", "PATIENT_MEDICATIONS", "PATIENT_CHANGES"}:
            if not user_structured and not user_doc_chunks:
                msg = evidence_guard_service.get_insufficient_evidence_message(language)
                return msg, [], "USER_RECORDS_MANDATORY_MISSING", [], ["Upload Medical Report", "What is glucose?", "What are normal reference ranges?"]

            lines = [multilingual_explanation_service.format_patient_records_header(language)]

            # A. Lab Tests
            lab_items = [item for item in user_structured if item.get("data", {}).get("type") in {"lab_test", "vital_record"}]
            for item in lab_items:
                d = item["data"]
                lines.append(multilingual_explanation_service.format_lab_item(
                    test_name=d['test_name'],
                    value=d['value'],
                    unit=d.get('unit'),
                    date=d.get('date', 'Recent'),
                    flag=d.get('flag', 'normal'),
                    language=language
                ))
                citations.append(CitationItem(
                    source_type=item["source_type"],
                    source_name=item["source_name"],
                    record_id=item["record_id"],
                    document_id=item.get("document_id"),
                    page_number=item.get("page_number", 1),
                    text_snippet=item["text_snippet"],
                    relevance_score=item["relevance_score"]
                ))
                structured_cards.append({
                    "card_type": "VALUE_CARD",
                    "title": d['test_name'],
                    "value": str(d['value']),
                    "unit": d.get('unit') or '',
                    "date": d.get('date', 'Recent'),
                    "flag": d.get('flag', 'normal'),
                    "source": item["source_name"],
                    "document_id": item.get("document_id")
                })

            # B. Prescriptions
            rx_items = [item for item in user_structured if item.get("data", {}).get("type") == "prescription"]
            for item in rx_items:
                d = item["data"]
                lines.append(multilingual_explanation_service.format_prescription_item(
                    medication_name=d['medication_name'],
                    dosage=d['dosage'],
                    frequency=d['frequency'],
                    timing=d['timing'],
                    duration=d['duration'],
                    language=language
                ))
                citations.append(CitationItem(
                    source_type=item["source_type"],
                    source_name=item["source_name"],
                    record_id=item["record_id"],
                    document_id=item.get("document_id"),
                    page_number=item.get("page_number", 1),
                    text_snippet=item["text_snippet"],
                    relevance_score=item["relevance_score"]
                ))
                structured_cards.append({
                    "card_type": "PRESCRIPTION_CARD",
                    "title": d['medication_name'],
                    "dosage": d['dosage'],
                    "frequency": d['frequency'],
                    "timing": d['timing'],
                    "date": d.get('date', 'Recent'),
                    "source": item["source_name"],
                    "document_id": item.get("document_id")
                })

            # C. Changes
            change_items = [item for item in user_structured if item.get("data", {}).get("type") == "change"]
            for item in change_items:
                d = item["data"]
                lines.append(f"• {d['test_name']}: {d['previous_value']} {d.get('unit','')} \u2192 {d['latest_value']} {d.get('unit','')} ({d['percentage_change']}) [{d['trend_direction']}]")
                citations.append(CitationItem(
                    source_type=item["source_type"],
                    source_name=item["source_name"],
                    record_id=item["record_id"],
                    document_id=item.get("document_id"),
                    page_number=item.get("page_number", 1),
                    text_snippet=item["text_snippet"],
                    relevance_score=item["relevance_score"]
                ))
                structured_cards.append({
                    "card_type": "TREND_CARD",
                    "title": d['test_name'],
                    "previous_value": str(d['previous_value']),
                    "latest_value": str(d['latest_value']),
                    "unit": d.get('unit') or '',
                    "percentage_change": d['percentage_change'],
                    "trend_direction": d['trend_direction'],
                    "source": item["source_name"],
                    "document_id": item.get("document_id")
                })

            if user_doc_chunks and not user_structured:
                for c in user_doc_chunks[:2]:
                    lines.append(f"• {c['text_snippet']}")
                    citations.append(CitationItem(
                        source_type=c["source_type"],
                        source_name=c["source_name"],
                        record_id=c["record_id"],
                        document_id=c.get("document_id"),
                        page_number=c.get("page_number", 1),
                        text_snippet=c["text_snippet"][:150],
                        relevance_score=c["relevance_score"]
                    ))

            ans = "\n".join(lines)
            ans = evidence_guard_service.sanitize_and_guard_response(
                answer=ans,
                query_type=query_type,
                has_patient_records=bool(user_structured or user_doc_chunks),
                is_cause_inquiry=is_cause_inquiry,
                language=language
            )

            # Contextual Follow-up Suggestions
            if lab_items:
                first_test = lab_items[0]["data"]["test_name"]
                follow_ups = [f"What does {first_test} generally measure?", "What changed from my previous report?", "What medicines are listed?"]
            elif rx_items:
                follow_ups = ["What are my latest values?", "What changed from my previous report?", "Explain my latest report"]
            elif change_items:
                follow_ups = ["What does glucose measure?", "What medicines are listed?", "Show my health history"]

            return ans, citations, "USER_RECORDS_PRIMARY", structured_cards, follow_ups

        # CASE 2: General Medical / Nutrition Knowledge Query
        elif query_type == "GENERAL_MEDICAL_KNOWLEDGE":
            if nutrition_knowledge:
                top_nut = nutrition_knowledge[0]
                food_obj = top_nut["data"]["food"]
                from backend.app.services.nutrition_service import nutrition_service
                explanation = nutrition_service.generate_nutrition_explanation(food=food_obj, language=language)
                
                for nk in nutrition_knowledge:
                    citations.append(CitationItem(
                        source_type=nk["source_type"],
                        source_name=nk["source_name"],
                        record_id=nk["record_id"],
                        text_snippet=nk["text_snippet"],
                        relevance_score=nk["relevance_score"],
                        license=nk.get("license", "Public Domain / CC0-1.0")
                    ))
                return explanation, citations, "GENERAL_NUTRITION_KNOWLEDGE_PRIMARY", [], ["What are my latest values?", "Show my blood test results", "What medicines are listed?"]

            if not general_knowledge:
                msg = "No general medical knowledge records matched your query."
                if language == "ta":
                    msg = "பொது மருத்துவ வினா-விடை தரவுத்தளத்தில் பொருந்தக்கூடிய தகவல் கிடைக்கவில்லை."
                elif language == "tanglish":
                    msg = "General medical knowledge database-il matching information kidaikkavillai."
                return msg, [], "GENERAL_KNOWLEDGE_NO_MATCH", [], ["What are my latest values?", "Show my blood test results"]

            top_rec = general_knowledge[0]
            ans_text = top_rec["data"]["answer"]

            for gk in general_knowledge:
                citations.append(CitationItem(
                    source_type=gk["source_type"],
                    source_name=gk["source_name"],
                    record_id=gk["record_id"],
                    text_snippet=gk["text_snippet"],
                    relevance_score=gk["relevance_score"],
                    license=gk.get("license", "mit")
                ))

            intro = multilingual_explanation_service.format_general_knowledge_intro(language)
            ans = f"{intro}{ans_text}"
            return ans, citations, "GENERAL_KNOWLEDGE_ONLY", [], ["What are my latest values?", "What changed from my previous report?", "What medicines are listed?"]

        # CASE 3: Document Search Query
        elif query_type == "DOCUMENT_SEARCH":
            if not user_doc_chunks and not user_structured:
                msg = evidence_guard_service.get_insufficient_evidence_message(language)
                return msg, [], "USER_DOCUMENTS_EMPTY", [], ["Upload Medical Report", "What is glucose?"]

            doc_header = "Based on the content of your uploaded reports:"
            if language == "ta":
                doc_header = "உங்கள் பதிவேற்றிய ஆவணங்களின் விவரங்களின்படி:"
            elif language == "tanglish":
                doc_header = "Ungaloda uploaded reports-il ulla vivarangal padi:"

            lines = [doc_header]
            for c in user_doc_chunks:
                lines.append(f"• {c['text_snippet']}")
                citations.append(CitationItem(
                    source_type=c["source_type"],
                    source_name=c["source_name"],
                    record_id=c["record_id"],
                    document_id=c.get("document_id"),
                    page_number=c.get("page_number", 1),
                    text_snippet=c["text_snippet"][:150],
                    relevance_score=c["relevance_score"]
                ))
            return "\n".join(lines), citations, "USER_DOCUMENTS_PRIMARY", [], ["What are my latest values?", "What changed from my previous report?"]

        # CASE 4: Hybrid Query (User Data + General Physiological Explanation)
        else: # HYBRID
            lines = []
            has_user_evidence = bool(user_structured or user_doc_chunks)
            h1, h2 = multilingual_explanation_service.format_hybrid_section_headers(language)

            if has_user_evidence:
                lines.append(h1)
                for item in user_structured[:5]:
                    if item.get("data", {}).get("type") in {"lab_test", "vital_record"}:
                        d = item["data"]
                        lines.append(multilingual_explanation_service.format_lab_item(
                            test_name=d['test_name'],
                            value=d['value'],
                            unit=d.get('unit'),
                            date=d.get('date', 'Recent'),
                            flag=d.get('flag', 'normal'),
                            language=language
                        ))
                        citations.append(CitationItem(
                            source_type=item["source_type"],
                            source_name=item["source_name"],
                            record_id=item["record_id"],
                            document_id=item.get("document_id"),
                            page_number=item.get("page_number", 1),
                            text_snippet=item["text_snippet"],
                            relevance_score=item["relevance_score"]
                        ))
            else:
                lines.append(evidence_guard_service.get_insufficient_evidence_message(language))

            if general_knowledge:
                lines.append(h2)
                gk = general_knowledge[0]
                lines.append(gk["data"]["answer"][:500] + ("..." if len(gk["data"]["answer"]) > 500 else ""))
                citations.append(CitationItem(
                    source_type=gk["source_type"],
                    source_name=gk["source_name"],
                    record_id=gk["record_id"],
                    text_snippet=gk["text_snippet"],
                    relevance_score=gk["relevance_score"],
                    license=gk.get("license", "mit")
                ))

            lines.append(multilingual_explanation_service.format_disclaimer(language))
            
            ans = "\n".join(lines)
            ans = evidence_guard_service.sanitize_and_guard_response(
                answer=ans,
                query_type=query_type,
                has_patient_records=has_user_evidence,
                is_cause_inquiry=is_cause_inquiry,
                language=language
            )
            return ans, citations, "HYBRID_USER_RECORDS_OVER_GENERAL_KNOWLEDGE", [], ["What are my latest values?", "What medicines are listed?"]

    def process_chat_query(self, db: Session, user_id: int, query: str, language: str = "en") -> ChatQueryResponse:
        """
        Main entrypoint for Hybrid RAG Chat with Phase 14.1 Evidence Guard & User Isolation:
        1. Classify query intent
        2. Retrieve from respective collections with strict user isolation
        3. Apply Evidence Guard verification & relevance filtering
        4. Synthesize response adhering to Evidence Hierarchy
        5. Validate citations and calculate evidence status
        """
        query_type = self.classify_query(query)

        # 1. Retrieve User Structured Records (user-isolated)
        user_structured = self.retrieve_user_structured(db, user_id, query, query_type)
        user_structured = evidence_guard_service.verify_user_isolation(user_id, user_structured)
        user_structured = evidence_guard_service.filter_relevant_evidence(query, user_structured)

        # 2. Retrieve User Document Chunks (user-isolated)
        user_doc_chunks = self.retrieve_user_document_chunks(db, user_id, query, query_type)
        user_doc_chunks = evidence_guard_service.verify_user_isolation(user_id, user_doc_chunks)
        user_doc_chunks = evidence_guard_service.filter_relevant_evidence(query, user_doc_chunks)

        # 3. Retrieve General Medical Knowledge (global collection) - ONLY for GENERAL or HYBRID
        general_knowledge = self.retrieve_general_knowledge(db, query, query_type)
        
        # 3b. Retrieve General Nutrition Knowledge if query pertains to nutrition/food
        nutrition_knowledge = self.retrieve_nutrition_knowledge(db, query) if query_type == "GENERAL_MEDICAL_KNOWLEDGE" else []

        # 4. Generate Grounded Response adhering to Evidence Priority
        answer, citations, priority_applied, structured_cards, follow_ups = self.generate_grounded_response(
            query=query,
            query_type=query_type,
            user_structured=user_structured,
            user_doc_chunks=user_doc_chunks,
            general_knowledge=general_knowledge,
            nutrition_knowledge=nutrition_knowledge,
            language=language
        )

        # 5. Evidence Status Calculation
        has_user_data = bool(user_structured or user_doc_chunks)
        has_general_data = bool(general_knowledge or nutrition_knowledge)
        evidence_found = bool(citations)

        if query_type in {"PATIENT_FACTUAL", "PATIENT_MEDICATIONS", "PATIENT_CHANGES", "DOCUMENT_SEARCH"}:
            status = "SUPPORTED" if has_user_data else "INSUFFICIENT"
        elif query_type == "GENERAL_MEDICAL_KNOWLEDGE":
            status = "SUPPORTED" if has_general_data else "INSUFFICIENT"
        else: # HYBRID
            if has_user_data and has_general_data:
                status = "SUPPORTED"
            elif has_user_data or has_general_data:
                status = "PARTIAL"
            else:
                status = "INSUFFICIENT"

        # Diagnostic metadata (internal counts, no PII logged)
        logger.debug(
            f"RAG Diagnostics | QueryType: {query_type} | UserID: {user_id} | "
            f"Structured: {len(user_structured)} | Chunks: {len(user_doc_chunks)} | "
            f"General: {len(general_knowledge)} | Citations: {len(citations)} | Status: {status}"
        )

        return ChatQueryResponse(
            answer=answer,
            query_type=query_type,
            evidence_found=evidence_found,
            evidence_priority_applied=priority_applied,
            evidence_status=status,
            citations=citations,
            sources=citations,
            language=language,
            structured_cards=structured_cards,
            follow_up_suggestions=follow_ups
        )

    def get_knowledge_sources_info(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Returns metadata and licensing information for active RAG knowledge collections."""
        user_docs_count = db.query(Document).filter(Document.user_id == user_id).count()
        user_chunks_count = db.query(RAGChunk).filter(RAGChunk.user_id == user_id).count()
        gen_count = db.query(MedicalKnowledgeChunk).count()

        return [
            {
                "collection_name": "USER_MEDICAL_RECORDS",
                "total_records": user_docs_count + user_chunks_count,
                "is_user_isolated": True,
                "description": "Authenticated patient uploaded documents, structured lab tests, and extracted clinical records."
            },
            {
                "collection_name": "GENERAL_MEDICAL_KNOWLEDGE",
                "total_records": gen_count,
                "is_user_isolated": False,
                "description": "Curated Medical QA Dataset for general physiological concepts and reference definitions.",
                "dataset_name": "Medical QA Reference (MIT)",
                "dataset_version": "29833779cb5921f474d9f469aa85c115277bf489",
                "license": "mit",
                "source_url": "https://huggingface.co/datasets/Malikeh1375/medical-question-answering-datasets"
            }
        ]

hybrid_rag_service = HybridRAGService()
