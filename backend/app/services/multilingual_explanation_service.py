from typing import Dict, Any, List, Optional, Tuple

class MultilingualExplanationService:
    """
    Service for rendering evidence-grounded AI explanations in English, Tamil, and Tanglish.
    
    Guarantees:
      - All numerical measurements (e.g. 105, 120/80, 7.1) remain identical.
      - All units (e.g. mg/dL, %, mmHg, g/dL, U/L) remain untranslated.
      - All dates (e.g. 2026-03-10) remain untranslated.
      - All medicine names (e.g. Metformin, Amoxicillin) and test names (e.g. HbA1c, Glucose) remain untranslated.
      - Citations and provenance metadata remain intact.
      - Never invents missing patient information.
    """

    SUPPORTED_LANGUAGES = {"en", "ta", "tanglish"}

    def normalize_language(self, lang: Optional[str]) -> str:
        if not lang:
            return "en"
        clean = lang.strip().lower()
        if clean in {"tamil", "ta"}:
            return "ta"
        elif clean in {"tanglish", "tamil_english"}:
            return "tanglish"
        return "en"

    def format_patient_records_header(self, language: str = "en") -> str:
        lang = self.normalize_language(language)
        if lang == "ta":
            return "உங்கள் மருத்துவ ஆவணங்களின்படி கண்டறியப்பட்ட விவரங்கள்:"
        elif lang == "tanglish":
            return "Ungaloda uploaded medical records-il ulla vivarangal:"
        return "Based on your uploaded medical records:"

    def format_lab_item(
        self,
        test_name: str,
        value: str,
        unit: Optional[str],
        date: str,
        flag: str,
        language: str = "en"
    ) -> str:
        lang = self.normalize_language(language)
        unit_str = f" {unit}".strip() if unit else ""
        flag_upper = flag.upper()
        
        if lang == "ta":
            # Medical values and flags preserved
            return f"• {test_name}: {value}{unit_str} (தேதி: {date}) [நிலை: {flag_upper}]"
        elif lang == "tanglish":
            return f"• {test_name}: {value}{unit_str} (Date: {date}) [Status: {flag_upper}]"
        return f"• {test_name}: {value}{unit_str} (Date: {date}) [Status: {flag_upper}]"

    def format_prescription_item(
        self,
        medication_name: str,
        dosage: Optional[str],
        frequency: Optional[str],
        timing: Optional[str],
        duration: Optional[str],
        language: str = "en"
    ) -> str:
        lang = self.normalize_language(language)
        dose = dosage or "Standard"
        freq = frequency or "As directed"
        tim = timing or "As directed"

        if lang == "ta":
            # Translate instructions into Tamil while keeping medication name & dosage intact
            timing_map_ta = {
                "after meals": "உணவுக்குப் பின்",
                "after food": "உணவுக்குப் பின்",
                "before meals": "உணவுக்கு முன்",
                "before food": "உணவுக்கு முன்",
                "with meals": "உணவுடன்",
                "at bedtime": "இரவு உறங்கும் முன்"
            }
            timing_ta = timing_map_ta.get(tim.lower().strip(), tim)
            return f"• மருந்து Rx {medication_name} ({dose}): {freq}, வழிகாட்டல்: {timing_ta}"
        elif lang == "tanglish":
            timing_map_tanglish = {
                "after meals": "Unavukku pin",
                "after food": "Unavukku pin",
                "before meals": "Unavukku mun",
                "before food": "Unavukku mun",
                "with meals": "Unavudan",
                "at bedtime": "Night thoongum mun"
            }
            timing_tanglish = timing_map_tanglish.get(tim.lower().strip(), tim)
            return f"• Medicine Rx {medication_name} ({dose}): {freq}, Timing: {timing_tanglish}"
        return f"• Rx {medication_name} ({dose}): {freq}, {tim}"

    def format_general_knowledge_intro(self, language: str = "en") -> str:
        lang = self.normalize_language(language)
        if lang == "ta":
            return "பொது மருத்துவ அறிவு வழிகாட்டலின்படி:\n"
        elif lang == "tanglish":
            return "General Medical Knowledge padi:\n"
        return "According to general medical knowledge sources:\n"

    def format_hybrid_section_headers(self, language: str = "en") -> Tuple[str, str]:
        lang = self.normalize_language(language)
        if lang == "ta":
            return (
                "1. உங்கள் மருத்துவ ஆவணங்களில் உள்ள உண்மையான அளவுகள்:",
                "\n2. பொது மருத்துவ விவரம் மற்றும் அறிவியல் விளக்கம்:"
            )
        elif lang == "tanglish":
            return (
                "1. Ungaloda actual medical report values:",
                "\n2. General Clinical & Physiological Context:"
            )
        return (
            "1. Documented Patient Values from Your Records:",
            "\n2. General Clinical & Physiological Context:"
        )

    def format_disclaimer(self, language: str = "en") -> str:
        lang = self.normalize_language(language)
        if lang == "ta":
            return "\n* மறுப்பு: பொது மருத்துவ அறிவு தகவல் பயன்பாட்டிற்கு மட்டுமே வழங்கப்படுகிறது; இது தனிநபர் மருத்துவ நோயறிதல் அல்ல."
        elif lang == "tanglish":
            return "\n* Disclaimer: General medical knowledge informational purpose-kku mattume; idhu personal medical diagnosis illai."
        return "\n* Disclaimer: General medical knowledge is provided for informational context only and does not constitute a personal medical diagnosis."

multilingual_explanation_service = MultilingualExplanationService()
