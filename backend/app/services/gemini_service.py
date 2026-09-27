import re
import time
from typing import Dict, Any, List, Optional, Tuple
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.assistant import CitationItem

MEDICATION_CHANGE_SAFETY_RESPONSE = (
    "I can explain and compare information from your medical records, but I cannot recommend changing "
    "your medication. Please discuss medication changes with your doctor."
)

UNSUPPORTED_RECORDS_RESPONSE = (
    "I couldn't find that information in your uploaded records."
)

GEMINI_SYSTEM_INSTRUCTION = """You are HealthMate AI's Clinical Assistant powered by Google Gemini.
You are a warm, helpful, evidence-grounded medical AI assistant.

AI CHAT CAPABILITIES & ALLOWED SCOPES:
1. Normal Conversation: Greet the user politely, explain what you can do, and engage in helpful, respectful dialogue.
2. User Medical Records: Answer questions about the user's uploaded medical reports and extracted OCR data.
3. Report Explanations: Explain medical values, units, reference ranges, and terms present in the reports.
4. Report Comparisons: Compare multiple reports and explain longitudinal trends between previous and current values.
5. Nutrition & Food Suggestions: Suggest evidence-based healthy foods from USDA data or general knowledge based on available report findings (e.g., iron-rich foods for low hemoglobin).
6. General Healthy Lifestyle: Provide general, non-prescriptive healthy nutrition, hydration, and lifestyle information.
7. Prescriptions: Explain dosages, frequencies, and instructions for medications ALREADY listed in the user's records.

STRICT SAFETY RULES — You MUST NOT:
- Recommend changing medicine.
- Recommend stopping medicine.
- Recommend increasing or decreasing dosage.
- Prescribe new medicine.
- Diagnose a disease independently.
- Replace a doctor or give personal clinical mandates.
- Invent missing report values or hallucinate medical data.
- Invent OCR text.
- Answer unsupported patient history questions not supported by the evidence.

MANDATORY FIXED RESPONSES:
- If the user asks whether they should change, stop, adjust, increase, or decrease medication (e.g., "Should I change my medicine?"):
  You MUST reply: "I can explain and compare information from your medical records, but I cannot recommend changing your medication. Please discuss medication changes with your doctor."
- If patient-specific information is not present in the user's records:
  You MUST reply: "I couldn't find that information in your uploaded records."

REPORT COMPARISON FORMAT:
When comparing reports or summarizing biomarker changes between reports, format the comparison using this markdown table format:
| Test | Previous | Current | Change | Reference Range |
| :--- | :--- | :--- | :--- | :--- |
(Fill rows with the exact test names, previous values, current values, calculated changes, and reference ranges from the evidence).
Do not interpret beyond the available evidence.

OCR UNCERTAINTY:
Never silently correct uncertain OCR. If any evidence item is noted as low confidence OCR (< 70%), clearly mark the information with "[Needs Verification - Low OCR Confidence]".

SOURCE CITATIONS:
Every report-based answer must cite its source when available:
- Document name
- Report date
- Page/section

EVIDENCE HIERARCHY:
USER STRUCTURED RECORDS > USER DOCUMENT CHUNKS > GENERAL MEDICAL KNOWLEDGE > GENERAL NUTRITION KNOWLEDGE
"""

class GeminiService:
    """
    Gemini API Integration for HealthMate AI Report Chat.
    Enforces clinical grounding, evidence guardrails, strict non-prescriptive safety rules,
    conversational assistance, and zero exposure of API keys.
    """

    def __init__(self):
        self.api_url_template = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        self.default_model = "gemini-1.5-flash"
        self.fallback_models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-pro"]

    @property
    def is_configured(self) -> bool:
        """Returns True if a valid Gemini API key is configured in backend environment."""
        key = (settings.GEMINI_API_KEY or "").strip()
        return bool(key and key != "" and not key.startswith("PASTE_") and not key.startswith("YOUR_"))

    def is_conversational_query(self, query: str) -> bool:
        """Detects if query is a simple conversational greeting or capability inquiry."""
        q_lower = query.lower().strip()
        greetings = {
            "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
            "how are you", "who are you", "what can you do", "help", "thanks", "thank you"
        }
        return q_lower in greetings or q_lower.startswith(("hello ", "hi ", "hey ", "good morning", "who are you"))

    def is_medication_change_query(self, query: str) -> bool:
        """Detects if user is asking to change, stop, alter dosage, or seek medication prescriptions."""
        q_lower = query.lower().strip()
        med_change_patterns = [
            r'\b(should i|can i|ought i to|may i)\s+(change|stop|discontinue|alter|switch|increase|decrease|reduce|raise|adjust|start|take|taper)\s+(my\s+)?(medicine|medication|dose|dosage|pills?|tablets?|treatment|drugs?|prescription)\b',
            r'\b(change|stop|discontinue|switch|increase|decrease|reduce|raise|adjust)\s+(my\s+)?(medicine|medication|dose|dosage|pills?|tablets?|treatment|drugs?|prescription)\b',
            r'\b(should i stop|can i stop|stop taking|should i change|change my medicine|change medication|adjust my dose|increase dosage|decrease dosage)\b',
            r'\b(what medicine should i take|prescribe me|recommend a medicine|give me medicine for)\b'
        ]
        return any(bool(re.search(pat, q_lower)) for pat in med_change_patterns)

    def format_evidence_context(
        self,
        user_structured: List[Dict[str, Any]],
        user_doc_chunks: List[Dict[str, Any]],
        general_knowledge: List[Dict[str, Any]]
    ) -> str:
        """Formats verified retrieved evidence into structured prompt context with OCR confidence tags."""
        context_parts = []

        if user_structured:
            context_parts.append("### VERIFIED USER STRUCTURED RECORDS:")
            for item in user_structured:
                src_name = item.get("source_name", "Medical Record")
                doc_id = item.get("document_id", "N/A")
                page = item.get("page_number", 1)
                data = item.get("data", {})
                item_type = data.get("type", "record")
                
                # Check OCR confidence
                conf = item.get("confidence") or item.get("ocr_confidence")
                conf_tag = " [Needs Verification - Low OCR Confidence]" if (isinstance(conf, (int, float)) and conf < 70) else ""

                if item_type == "lab_test":
                    test_name = data.get("test_name", "Test")
                    val = data.get("value", "N/A")
                    unit = data.get("unit", "")
                    ref = data.get("reference_range", data.get("reference_range_text", "N/A"))
                    date = data.get("date", "N/A")
                    flag = data.get("flag", "normal")
                    context_parts.append(
                        f"- Lab Test: {test_name} | Value: {val} {unit} | Reference Range: {ref} | Flag: {flag} | Date: {date} | Source: {src_name} (Page {page}){conf_tag}"
                    )
                elif item_type == "prescription":
                    med_name = data.get("medication_name", "Medicine")
                    dosage = data.get("dosage", "N/A")
                    freq = data.get("frequency", "N/A")
                    timing = data.get("timing", "N/A")
                    dur = data.get("duration", "N/A")
                    date = data.get("date", "N/A")
                    context_parts.append(
                        f"- Prescription: {med_name} | Dosage: {dosage} | Frequency: {freq} | Timing: {timing} | Duration: {dur} | Date: {date} | Source: {src_name} (Page {page}){conf_tag}"
                    )
                elif item_type == "change":
                    t_name = data.get("test_name", "Biomarker")
                    prev_val = data.get("previous_value", "N/A")
                    lat_val = data.get("latest_value", "N/A")
                    chg = data.get("change", data.get("percentage_change", "N/A"))
                    ref = data.get("reference_range_text", "N/A")
                    trend = data.get("trend_direction", "N/A")
                    context_parts.append(
                        f"- Comparison/Trend: {t_name} | Previous: {prev_val} | Current: {lat_val} | Change: {chg} ({trend}) | Reference Range: {ref} | Source: {src_name}{conf_tag}"
                    )
                else:
                    context_parts.append(f"- Record: {item.get('text_snippet', '')} | Source: {src_name}{conf_tag}")

        if user_doc_chunks:
            context_parts.append("\n### VERIFIED USER DOCUMENT OCR CHUNKS:")
            for chunk in user_doc_chunks:
                src_name = chunk.get("source_name", "Document")
                page = chunk.get("page_number", 1)
                snippet = chunk.get("text_snippet", "")
                conf = chunk.get("confidence") or chunk.get("ocr_confidence")
                conf_tag = " [Needs Verification - Low OCR Confidence]" if (isinstance(conf, (int, float)) and conf < 70) else ""
                context_parts.append(f"- Chunk from '{src_name}' (Page {page}): \"{snippet}\"{conf_tag}")

        if general_knowledge:
            context_parts.append("\n### GENERAL MEDICAL / NUTRITIONAL KNOWLEDGE REFERENCE:")
            for gk in general_knowledge:
                q = gk.get("data", {}).get("question", "")
                a = gk.get("data", {}).get("answer", "")
                context_parts.append(f"- Q: {q}\n  A: {a}")

        if not context_parts:
            return "NO EVIDENCE AVAILABLE IN USER RECORDS."

        return "\n".join(context_parts)

    def generate_chat_response(
        self,
        query: str,
        user_structured: List[Dict[str, Any]],
        user_doc_chunks: List[Dict[str, Any]],
        general_knowledge: List[Dict[str, Any]],
        language: str = "en",
        query_type: str = "PATIENT_FACTUAL"
    ) -> Optional[str]:
        """
        Sends grounded evidence to Gemini API and retrieves a strictly governed response.
        Returns None if Gemini is not configured or in case of network/API error (triggering local fallback).
        """
        if not self.is_configured:
            logger.info("Gemini API key not configured; using deterministic local grounded engine.")
            return None

        # Safety Check: Medication Change Request
        if self.is_medication_change_query(query):
            logger.info("Safety guard triggered: Medication change inquiry intercepted.")
            return MEDICATION_CHANGE_SAFETY_RESPONSE

        # If it's a patient factual question and there is ZERO evidence
        if query_type in {"PATIENT_FACTUAL", "PATIENT_MEDICATIONS", "PATIENT_CHANGES", "DOCUMENT_SEARCH"}:
            if not user_structured and not user_doc_chunks and not self.is_conversational_query(query):
                return UNSUPPORTED_RECORDS_RESPONSE

        evidence_text = self.format_evidence_context(user_structured, user_doc_chunks, general_knowledge)

        user_prompt = f"""Language: {language}
Query Intent: {query_type}
User Question: {query}

AVAILABLE RETRIEVED EVIDENCE:
{evidence_text}

Instructions:
1. Answer the user question strictly using the provided retrieved evidence and allowed capabilities.
2. If comparing reports or listing biomarker changes, format as markdown table:
   | Test | Previous | Current | Change | Reference Range |
3. If information is not in the provided evidence and cannot be answered from general knowledge, reply: "{UNSUPPORTED_RECORDS_RESPONSE}".
4. Show document name, report date, and page/section source citations for report data.
5. If low confidence OCR is noted, mark it as needing verification.
6. If the user asks for food or nutrition recommendations, suggest evidence-based foods (with calories/nutrients) aligned with their report findings without diagnosing.
7. Do not offer medical diagnosis, medication changes, or unverified claims.
"""

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{GEMINI_SYSTEM_INSTRUCTION}\n\n---\n\n{user_prompt}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.85,
                "maxOutputTokens": 1024
            }
        }

        models_to_try = [self.default_model] + self.fallback_models
        start_time = time.time()

        for model in models_to_try:
            url = f"{self.api_url_template.format(model=model)}?key={settings.GEMINI_API_KEY}"
            try:
                with httpx.Client(timeout=12.0) as client:
                    resp = client.post(
                        url,
                        headers={"Content-Type": "application/json"},
                        json=payload
                    )
                    latency_ms = (time.time() - start_time) * 1000

                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts and "text" in parts[0]:
                                answer = parts[0]["text"].strip()
                                logger.info(
                                    f"Gemini API Response Success | Model: {model} | Latency: {latency_ms:.1f}ms | "
                                    f"Response Length: {len(answer)} chars"
                                )
                                return answer
                    else:
                        logger.warning(
                            f"Gemini API returned status {resp.status_code} for model {model}."
                        )
            except Exception as ex:
                logger.warning(f"Gemini API call failed for model {model}: {type(ex).__name__}")

        logger.info("Falling back to local grounded synthesis engine.")
        return None

gemini_service = GeminiService()
