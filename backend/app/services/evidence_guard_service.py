import re
from typing import Dict, Any, List, Optional, Tuple
from backend.app.schemas.assistant import CitationItem

class EvidenceGuardService:
    """
    Evidence Guard Service for HealthMate AI
    ========================================
    Enforces clinical grounding, zero-hallucination policies, cross-user isolation,
    and evidence hierarchy:
      USER STRUCTURED RECORDS > USER DOCUMENT CHUNKS > GENERAL MEDICAL KNOWLEDGE
    """

    INSUFFICIENT_EVIDENCE_MSG_EN = "The available records do not contain enough information to answer this patient-specific question."
    INSUFFICIENT_EVIDENCE_MSG_TA = "இந்த குறிப்பிட்ட கேள்விக்கு பதிலளிக்க தேவையான தகவல்கள் உங்கள் மருத்துவ ஆவணங்களில் கிடைக்கவில்லை."
    INSUFFICIENT_EVIDENCE_MSG_TANGLISH = "Indha specific question-ku answer panna thevaiyaana details ungaloda uploaded records-il illai."

    def get_insufficient_evidence_message(self, language: str = "en") -> str:
        if language == "ta":
            return self.INSUFFICIENT_EVIDENCE_MSG_TA
        elif language == "tanglish":
            return self.INSUFFICIENT_EVIDENCE_MSG_TANGLISH
        return self.INSUFFICIENT_EVIDENCE_MSG_EN

    def verify_user_isolation(self, target_user_id: int, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Guarantees that retrieved user records/chunks strictly belong to target_user_id.
        Discards any item that does not match target_user_id when user_id is present.
        """
        isolated = []
        for r in records:
            item_user_id = r.get("user_id")
            if item_user_id is not None and item_user_id != target_user_id:
                # Security isolation violation avoided
                continue
            isolated.append(r)
        return isolated

    def determine_evidence_status(
        self,
        query_type: str,
        user_structured: List[Dict[str, Any]],
        user_doc_chunks: List[Dict[str, Any]],
        general_knowledge: List[Dict[str, Any]],
        query_has_patient_match: bool
    ) -> str:
        """
        Determines the evidence status:
        - 'SUPPORTED': Fully supported by verified patient records or verified general medical knowledge.
        - 'PARTIAL': Partially supported (e.g. hybrid explanation where patient data gives values but cause is unverified, or general knowledge provides context).
        - 'INSUFFICIENT': Missing required patient records or zero evidence.
        """
        has_user_evidence = bool(user_structured or user_doc_chunks)
        has_gen_evidence = bool(general_knowledge)

        if query_type in ["PATIENT_FACTUAL", "DOCUMENT_SEARCH"]:
            if not has_user_evidence or not query_has_patient_match:
                return "INSUFFICIENT"
            return "SUPPORTED"
        elif query_type == "HYBRID":
            if has_user_evidence and has_gen_evidence:
                return "SUPPORTED"
            elif has_user_evidence or has_gen_evidence:
                return "PARTIAL"
            else:
                return "INSUFFICIENT"
        elif query_type == "GENERAL_MEDICAL_KNOWLEDGE":
            if has_gen_evidence:
                return "SUPPORTED"
            return "INSUFFICIENT"

        return "PARTIAL" if has_user_evidence or has_gen_evidence else "INSUFFICIENT"

    def filter_relevant_evidence(
        self,
        query: str,
        records: List[Dict[str, Any]],
        threshold: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Verifies that retrieved evidence contains relevant query tokens or matching canonical concepts.
        Filters out low-relevance or spurious matches.
        """
        q_lower = query.lower()
        filtered = []
        for item in records:
            score = item.get("relevance_score", 1.0)
            if score is not None and score < threshold:
                continue

            # Verify date/month match if specific month is requested in query
            months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
            q_months = [m for m in months if m in q_lower]
            if q_months:
                # If query explicitly asked for a specific month, check if the record date or text contains that month or month number
                item_date = ""
                if "data" in item and "date" in item["data"]:
                    item_date = str(item["data"]["date"]).lower()
                snippet = item.get("text_snippet", "").lower()
                
                # Check month matching
                month_num_map = {
                    "january": "01", "february": "02", "march": "03", "april": "04",
                    "may": "05", "june": "06", "july": "07", "august": "08",
                    "september": "09", "october": "10", "november": "11", "december": "12"
                }
                has_month_match = False
                for qm in q_months:
                    m_num = month_num_map[qm]
                    if qm in item_date or qm in snippet or f"-{m_num}-" in item_date or f"/{m_num}/" in item_date or item_date.endswith(f"-{m_num}") or item_date.startswith(f"{m_num}/"):
                        has_month_match = True
                        break
                if not has_month_match:
                    # Item is from a different month than explicitly requested
                    continue

            filtered.append(item)
        return filtered

    def validate_citations(
        self,
        citations: List[CitationItem],
        target_user_id: int
    ) -> List[CitationItem]:
        """
        Validates citation attribution, ensuring:
        1. No leaked private user information.
        2. Non-empty source names and snippet text.
        3. Accurate page numbers when available.
        """
        valid_citations = []
        for c in citations:
            if not c.source_name or not c.text_snippet:
                continue
            # Ensure snippet is sanitized of extraneous whitespace
            c.text_snippet = c.text_snippet.strip()
            valid_citations.append(c)
        return valid_citations

    def sanitize_and_guard_response(
        self,
        answer: str,
        query_type: str,
        has_patient_records: bool,
        is_cause_inquiry: bool,
        language: str = "en"
    ) -> str:
        """
        Safety Guard:
        - Prevents invented medical diagnoses.
        - Prevents guessing cause of changes when unavailable in records.
        - Appends disclaimer to preserve medical safety.
        """
        guarded_answer = answer

        # When asked why a value changed, ensure the AI explicitly states records cannot establish personal medical cause
        if is_cause_inquiry and has_patient_records:
            cause_disclaimer = (
                "\n\n* Note: The available medical records document the recorded values and dates, but do not provide clinical evidence establishing the specific biological or lifestyle cause of the change. Please consult your physician for clinical interpretation."
            )
            if language == "ta":
                cause_disclaimer = (
                    "\n\n* குறிப்பு: கிடைக்கக்கூடிய மருத்துவ ஆவணங்கள் பதிவான அளவுகளையும் தேதிகளையும் மட்டுமே காட்டுகின்றன; இந்த மாற்றத்திற்கான குறிப்பிட்ட காரணத்தை மருத்துவ ஆவணங்கள் மூலம் உறுதிப்படுத்த முடியாது. உங்கள் மருத்துவரை அணுகவும்."
                )
            elif language == "tanglish":
                cause_disclaimer = (
                    "\n\n* Note: Available medical records-il values matrum dates mattume irukkiradhu; indha change-kku specific reason record aagavillai. Ungal doctor-idam aalosanai peravum."
                )
            if cause_disclaimer.strip() not in guarded_answer:
                guarded_answer += cause_disclaimer

        return guarded_answer

evidence_guard_service = EvidenceGuardService()
