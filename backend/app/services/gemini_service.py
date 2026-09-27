import re
import time
from typing import Dict, Any, List, Optional, Tuple
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.assistant import CitationItem

MEDICATION_CHANGE_SAFETY_NOTE = (
    "Just a heads-up — I can explain your medications and what your records say, but for any changes to your "
    "dosage or prescription, please check with your doctor. They know your full picture best! 😊"
)

UNSUPPORTED_RECORDS_RESPONSE = (
    "Hmm, I couldn't find that specific info in your uploaded records. "
    "Try uploading the relevant report and I'll analyze it for you!"
)

GEMINI_SYSTEM_INSTRUCTION = """You are HealthMate — a warm, caring, and knowledgeable personal health AI assistant.
You speak like a friendly health-savvy companion who genuinely cares about the user's wellbeing.

PERSONALITY & TONE:
- Be warm, encouraging, and conversational — like a trusted friend who happens to know a lot about health.
- Use friendly language, occasional emojis where appropriate (💊 🩺 🥗 💪 🌟), and keep things easy to understand.
- Never be robotic or overly clinical. Explain things in plain language.
- Celebrate good results and gently guide about concerning ones.
- Always be supportive, never alarming or preachy.

WHAT YOU CAN HELP WITH (Health-Focused):
1. 💬 Chat & Greetings: Warm, friendly conversation about health topics.
2. 🩺 Medical Records: Explain, summarize, and compare the user's uploaded lab reports and documents.
3. 📊 Report Explanations: Break down medical values, units, reference ranges in simple terms.
4. 📈 Trends & Changes: Track and explain biomarker changes between reports over time.
5. 🥗 Nutrition & Food: Give personalized, evidence-based food suggestions tied to their health data.
6. 🏃 Lifestyle Tips: Share healthy lifestyle habits (sleep, hydration, exercise) relevant to their health status.
7. 💊 Prescription Info: Explain dosages and instructions for medications in their records.
8. 🖼️ Image Analysis: Analyze uploaded medical report images or prescription photos and extract information.
9. 🌡️ Symptom Context: Discuss symptoms in context of their records (without diagnosing).
10. ❓ General Health Questions: Answer any health-related questions with knowledge and care.

SAFETY GUARDRAILS (Always follow):
- Never recommend changing, stopping, or adjusting prescribed medication dosage — always say to check with their doctor.
- Never diagnose a disease as a definitive conclusion — share possibilities and encourage medical consultation.
- Never invent lab values, report data, or OCR text you haven't been given.
- If medication change is asked: Respond warmly but redirect to their doctor.
- Stay on HEALTH topics only. For unrelated topics, gently redirect: "That's outside my health specialty! Let's focus on keeping you healthy 😊"

REPORT COMPARISON FORMAT:
When comparing reports, use this clean markdown table:
| Test | Previous | Current | Change | Reference Range | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |

OCR UNCERTAINTY:
If evidence has low OCR confidence (< 70%), flag it as: "⚠️ [Needs Verification - Low OCR Confidence]"

SOURCE CITATIONS:
Always cite: Document name, Report date, Page/section when answering from records.

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
        self.default_model = "gemini-2.0-flash"
        self.fallback_models = ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-pro"]
        self.vision_model = "gemini-2.0-flash"

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
        """Detects if user is asking to change, stop, alter dosage, or prescribe new medications."""
        q_lower = query.lower().strip()
        med_change_patterns = [
            r'\b(should i|can i|ought i to|may i)\s+(change|stop|discontinue|alter|switch|increase|decrease|reduce|raise|adjust|taper)\s+(my\s+)?(medicine|medication|dose|dosage|pills?|tablets?|treatment|drugs?|prescription)\b',
            r'\b(should i stop|can i stop|stop taking|should i change|change my medicine|change medication|adjust my dose|increase dosage|decrease dosage)\b',
            r'\b(prescribe me|give me a prescription|write me a prescription)\b'
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

        # Safety Check: Medication Change Request — handle warmly, don't block
        if self.is_medication_change_query(query):
            logger.info("Safety note triggered: Medication change inquiry.")
            # Don't hard-block; include safety note in context but let AI respond warmly
            query = query + " [Note: Provide general info about the medication from records if available, but add the safety note about consulting a doctor for dosage changes]"

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

    def analyze_image_with_vision(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        prompt: str = "Extract all text and medical information from this image. Identify lab values, medications, diagnoses, dates, and any other health-relevant information. Format clearly."
    ) -> Optional[str]:
        """
        Use Gemini Vision to analyze a medical image/document photo and extract text + insights.
        Returns extracted text and analysis, or None on failure.
        """
        if not self.is_configured:
            return None

        import base64
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_b64
                            }
                        },
                        {
                            "text": f"{GEMINI_SYSTEM_INSTRUCTION}\n\nTask: {prompt}\n\nPlease extract ALL text visible in this medical document/image accurately. Then summarize the key health information found."
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.85,
                "maxOutputTokens": 2048
            }
        }

        url = f"{self.api_url_template.format(model=self.vision_model)}?key={settings.GEMINI_API_KEY}"
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload
                )
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            result = parts[0]["text"].strip()
                            logger.info(f"Gemini Vision analysis success | Length: {len(result)} chars")
                            return result
                else:
                    logger.warning(f"Gemini Vision returned status {resp.status_code}")
        except Exception as ex:
            logger.warning(f"Gemini Vision call failed: {type(ex).__name__}: {ex}")

        return None

gemini_service = GeminiService()
