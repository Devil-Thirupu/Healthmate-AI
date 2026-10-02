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

GEMINI_SYSTEM_INSTRUCTION = """You are HealthMate, a warm, friendly, knowledgeable personal health AI companion.
Tone: Caring, conversational, plain language, supportive, helpful emojis (🩺 💊 🥗 🌟).

CORE DUTIES:
1. Medical Records & Lab Results: Summarize, explain, and compare user's uploaded lab tests and reports.
2. Biomarkers & Trends: Explain values, normal ranges, and progress over time in plain words.
3. Food & Nutrition: Give personalized food suggestions aligned with their biomarker values.
4. Prescriptions: Explain dosages and timing found in their records.
5. OCR & Image Analysis: Extract data accurately from medical documents and reports.

SAFETY RULES:
- Never recommend changing or stopping prescribed medication; always advise checking with their doctor.
- Do not diagnose diseases definitively.
- Never invent lab numbers or facts not in the evidence.
- Stay on health topics.

FORMATTING:
- For comparisons, use clean markdown tables.
- Cite document name and date when answering from records."""

class GeminiService:
    """
    Gemini API Integration for HealthMate AI Report Chat.
    Enforces clinical grounding, evidence guardrails, strict non-prescriptive safety rules,
    conversational assistance, and token efficiency.
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
        """Formats verified retrieved evidence compactly to minimize LLM token consumption."""
        context_parts = []

        if user_structured:
            context_parts.append("### USER RECORDS:")
            for item in user_structured[:10]:
                src_name = item.get("source_name", "Medical Record")
                page = item.get("page_number", 1)
                data = item.get("data", {})
                item_type = data.get("type", "record")
                
                conf = item.get("confidence") or item.get("ocr_confidence")
                conf_tag = " [Low OCR Conf]" if (isinstance(conf, (int, float)) and conf < 70) else ""

                if item_type == "lab_test":
                    t_name = data.get("test_name", "Test")
                    val = data.get("value", "N/A")
                    unit = data.get("unit", "")
                    ref = data.get("reference_range", data.get("reference_range_text", "N/A"))
                    date = data.get("date", "N/A")
                    flag = data.get("flag", "normal")
                    context_parts.append(f"- Lab: {t_name}={val} {unit} (Ref: {ref}, {flag}, {date}, {src_name}){conf_tag}")
                elif item_type == "prescription":
                    med_name = data.get("medication_name", "Medicine")
                    dosage = data.get("dosage", "N/A")
                    freq = data.get("frequency", "N/A")
                    timing = data.get("timing", "N/A")
                    dur = data.get("duration", "N/A")
                    context_parts.append(f"- Rx: {med_name} {dosage} ({freq}, {timing}, {dur}, {src_name}){conf_tag}")
                elif item_type == "change":
                    t_name = data.get("test_name", "Biomarker")
                    prev_val = data.get("previous_value", "N/A")
                    lat_val = data.get("latest_value", "N/A")
                    chg = data.get("change", data.get("percentage_change", "N/A"))
                    context_parts.append(f"- Trend: {t_name} prev={prev_val} curr={lat_val} chg={chg} ({src_name})")
                else:
                    context_parts.append(f"- {item.get('text_snippet', '')} ({src_name})")

        if user_doc_chunks:
            context_parts.append("\n### OCR SNIPPETS:")
            for chunk in user_doc_chunks[:4]:
                src_name = chunk.get("source_name", "Document")
                page = chunk.get("page_number", 1)
                snippet = (chunk.get("text_snippet", "") or "")[:200]
                context_parts.append(f"- '{src_name}' p.{page}: {snippet}")

        if general_knowledge:
            context_parts.append("\n### KNOWLEDGE REF:")
            for gk in general_knowledge[:3]:
                q = gk.get("data", {}).get("question", "")
                a = (gk.get("data", {}).get("answer", "") or "")[:200]
                context_parts.append(f"- Q: {q} | A: {a}")

        if not context_parts:
            return "NO EVIDENCE IN USER RECORDS."

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
        Sends grounded evidence to Gemini API using a token-optimized prompt.
        """
        if not self.is_configured:
            logger.info("Gemini API key not configured; using deterministic local grounded engine.")
            return None

        if self.is_medication_change_query(query):
            query = query + " [Include reminder to consult doctor for dosage changes]"

        evidence_text = self.format_evidence_context(user_structured, user_doc_chunks, general_knowledge)

        user_prompt = f"""Language: {language} | Intent: {query_type}
Question: {query}

EVIDENCE:
{evidence_text}

Instructions:
1. Answer warmly and concisely using only provided evidence.
2. Use markdown table for biomarker comparisons.
3. If not in evidence, reply: "{UNSUPPORTED_RECORDS_RESPONSE}".
4. Cite document name and date for records."""

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
                "maxOutputTokens": 600
            }
        }

        models_to_try = [self.default_model] + self.fallback_models
        start_time = time.time()

        for model in models_to_try:
            url = f"{self.api_url_template.format(model=model)}?key={settings.GEMINI_API_KEY}"
            try:
                with httpx.Client(timeout=10.0) as client:
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
                                    f"Chars: {len(answer)}"
                                )
                                return answer
                    else:
                        logger.warning(f"Gemini API returned status {resp.status_code} for model {model}.")
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
        Use Gemini Vision to analyze medical image with optimized token limits.
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
                            "text": f"{GEMINI_SYSTEM_INSTRUCTION}\n\nTask: {prompt}\n\nPlease extract visible text accurately and summarize key health data."
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.85,
                "maxOutputTokens": 800
            }
        }

        url = f"{self.api_url_template.format(model=self.vision_model)}?key={settings.GEMINI_API_KEY}"
        try:
            with httpx.Client(timeout=25.0) as client:
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
                            logger.info(f"Gemini Vision analysis success | Chars: {len(result)}")
                            return result
                else:
                    logger.warning(f"Gemini Vision returned status {resp.status_code}")
        except Exception as ex:
            logger.warning(f"Gemini Vision call failed: {type(ex).__name__}: {ex}")

        return None

gemini_service = GeminiService()
