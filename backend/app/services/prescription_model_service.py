"""
Lightweight Prescription OCR & Structured Extraction Service
=============================================================
CPU-only, zero-heavy-dependency pipeline.

Providers:
  - baseline_ocr: Multi-tier OCR (PyMuPDF → pypdf → pytesseract) + rule-based
                  clinical extractor. Works on any hardware; no GPU required.

NOT included:
  - PyTorch, Transformers, CUDA, bitsandbytes, large model downloads.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from backend.app.core.logging import logger
from backend.app.services.clinical_extractor import clinical_extractor, MEDICATION_CATALOG
from backend.app.models.prescription_extraction import ConfidenceLevel, ParsingStatus

class PrescriptionModelService:
    """
    Lightweight prescription structured extraction service.

    Uses only the existing OCR pipeline (PyMuPDF / pypdf / pytesseract) plus
    rule-based regex extraction. No neural models, no GPU, no internet required.
    """

    PROVIDER = "baseline_ocr"
    MODEL_NAME = "Lightweight Rule-Based OCR Extractor"
    MODEL_VERSION = "v2.0"

    def sanitize_field(self, val: Any) -> str:
        """Enforce zero-hallucination policy: missing / empty → 'Not available in source'."""
        if val is None:
            return "Not available in source"
        s = str(val).strip()
        if not s or s.lower() in {"null", "none", "n/a", "na", "", "standard"}:
            return "Not available in source"
        return s

    def normalize_medicine_name(self, raw_name: str) -> Optional[str]:
        """
        Attempt a catalog match for the drug name.
        Returns canonical name on match, None otherwise.
        Always preserves original raw_name in the caller's record.
        """
        if not raw_name or raw_name == "Not available in source":
            return None
        clean = re.sub(
            r'^(tab|cap|syrup|inj|tablet|capsule|solution|susp|drops?|oint|gel|cream|lotion)\.?\s*',
            '', raw_name.strip(), flags=re.IGNORECASE
        )
        clean = re.sub(r'\s*\d+\s*(mg|ml|g|mcg|iu|units?).*$', '', clean, flags=re.IGNORECASE).strip().lower()

        for med in MEDICATION_CATALOG:
            med_lower = med["name"].lower()
            if med_lower == clean:
                return med["name"]
            if len(clean) >= 4 and (med_lower in clean or clean in med_lower):
                return med["name"]
        return None

    def safe_parse_json(self, raw_text: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Safely parse a JSON block from raw model / extractor text.
        Returns (None, NEEDS_USER_REVIEW) on failure — never guesses missing fields.
        """
        import json
        if not raw_text or not raw_text.strip():
            return None, ParsingStatus.FAILED.value

        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed, ParsingStatus.SUCCESS.value
        except Exception:
            pass

        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(cleaned[start:end + 1])
                if isinstance(parsed, dict):
                    return parsed, ParsingStatus.SUCCESS.value
            except Exception:
                pass

        return None, ParsingStatus.NEEDS_USER_REVIEW.value

    def structure_medications(self, raw_medications: List[Any], source_snippet: str = "") -> List[Dict[str, Any]]:
        """
        Build a clean medication list from raw items without fabricating missing values.
        Preserves original OCR drug_name and attaches normalized_name separately.
        """
        structured = []
        if not isinstance(raw_medications, list):
            return structured

        for item in raw_medications:
            if isinstance(item, str):
                drug_raw = item.strip()
                structured.append({
                    "drug_name": self.sanitize_field(drug_raw),
                    "normalized_name": self.normalize_medicine_name(drug_raw) or "Not available in source",
                    "dosage": "Not available in source",
                    "frequency": "Not available in source",
                    "duration": "Not available in source",
                    "instructions": "Not available in source",
                    "confidence": None,
                    "source_snippet": source_snippet[:150],
                })
            elif isinstance(item, dict):
                drug_raw = item.get("drug_name") or item.get("medication_name") or item.get("name")
                structured.append({
                    "drug_name": self.sanitize_field(drug_raw),
                    "normalized_name": self.normalize_medicine_name(str(drug_raw or "")) or "Not available in source",
                    "dosage": self.sanitize_field(item.get("dosage")),
                    "frequency": self.sanitize_field(item.get("frequency")),
                    "duration": self.sanitize_field(item.get("duration")),
                    "instructions": self.sanitize_field(item.get("instructions")),
                    "confidence": item.get("confidence") if isinstance(item.get("confidence"), (int, float)) else None,
                    "source_snippet": str(item.get("source_snippet") or source_snippet)[:150],
                })

        return structured

    def extract_header_fields(self, ocr_text: str, hint_doctor: Optional[str] = None, hint_date: Optional[str] = None) -> Dict[str, str]:
        """
        Extract prescription header fields from raw OCR text using regex patterns.
        Only returns values that are explicitly present; 'Not available in source' otherwise.
        """
        text = ocr_text or ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        # 1. Doctor name
        doctor_name = self.sanitize_field(hint_doctor)
        if doctor_name == "Not available in source":
            for line in lines:
                m = re.search(r'(?:Dr\.?|Doctor|Doc\.?)\s+([A-Za-z\.\s]+)', line, re.IGNORECASE)
                if m:
                    doc_cand = m.group(1).strip()
                    # Strip medical qualifications
                    doc_cand = re.sub(r'[\,\s]+(?:MBBS|MD|MS|MCh|DM|DNB|BDS|MDS|FRCS|FRCR|PhD|FACS).*$', '', doc_cand, flags=re.IGNORECASE).strip()
                    if doc_cand:
                        doctor_name = doc_cand
                        break
                m2 = re.search(r'^([A-Z][a-zA-Z\s]+)[\,\s]+(?:MBBS|MD|MS|MCh|DM|DNB|BDS|MDS|FRCS|FRCR|PhD)', line)
                if m2:
                    doctor_name = m2.group(1).strip()
                    break

        # 2. Clinic / Hospital name
        clinic_name = "Not available in source"
        for line in lines:
            if re.search(r'\b(Hospitals?|Clinics?|Centres?|Centers?|Nursing\s+Home|Dispensar(?:y|ies)|Healthcare)\b', line, re.IGNORECASE):
                # Clean up line
                cand = re.sub(r'^(Welcome to|At|From)\s+', '', line, flags=re.IGNORECASE).strip()
                if len(cand) >= 4:
                    clinic_name = cand
                    break

        # 3. Prescription date
        prescription_date = self.sanitize_field(hint_date)
        if prescription_date == "Not available in source":
            for line in lines:
                m_date = re.search(r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b', line)
                if m_date:
                    prescription_date = m_date.group(1).strip()
                    break
                m_date2 = re.search(r'\b(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})\b', line)
                if m_date2:
                    prescription_date = m_date2.group(1).strip()
                    break
                m_date3 = re.search(r'(?:Date|Dt|Dated)[:\s]+([^\n]{5,20})', line, re.IGNORECASE)
                if m_date3:
                    prescription_date = m_date3.group(1).strip()
                    break

        # 4. Patient name
        patient_name = "Not available in source"
        for line in lines:
            m_pat = re.search(r'(?:Patient(?:\s+Name)?|Name|Patient\'s Name)[:\s]+([A-Za-z\s]+)', line, re.IGNORECASE)
            if m_pat:
                cand = m_pat.group(1).strip()
                if len(cand) >= 2:
                    patient_name = cand
                    break

        return {
            "doctor_name": doctor_name,
            "clinic_name": clinic_name,
            "prescription_date": prescription_date,
            "patient_name": patient_name,
        }

    def get_confidence_level(self, ocr_confidence_score: Optional[float]) -> Tuple[Optional[float], str]:
        """
        Map an OCR engine confidence score (0–100 scale from ocr_service) to a
        categorical confidence level. Returns (score, level).
        If score is None or 0.0, returns (None, 'NOT_AVAILABLE') — never invented.
        """
        if ocr_confidence_score is None or ocr_confidence_score <= 0.0:
            return None, ConfidenceLevel.NOT_AVAILABLE.value
        score_0to1 = ocr_confidence_score / 100.0 if ocr_confidence_score > 1.0 else ocr_confidence_score
        if score_0to1 >= 0.85:
            level = ConfidenceLevel.HIGH.value
        elif score_0to1 >= 0.60:
            level = ConfidenceLevel.MEDIUM.value
        else:
            level = ConfidenceLevel.LOW.value
        return round(ocr_confidence_score, 2), level

    def extract_with_baseline_provider(
        self,
        image_path: Path,
        ocr_raw_text: str,
        doctor_name: Optional[str] = None,
        doc_date: Optional[str] = None,
        ocr_confidence_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Run structured extraction using the lightweight rule-based pipeline:
        1. Receive raw OCR text
        2. Run medication extraction with explicit presence checking
        3. Run header regex extraction (doctor, clinic, date, patient)
        4. Sanitize all fields — nothing invented
        5. Map OCR confidence to categorical level if available
        """
        lines = [line.strip() for line in (ocr_raw_text or "").splitlines() if line.strip()]
        medications = []
        seen_drugs = set()

        # Phase A: Check against clinical medication catalog
        for med in MEDICATION_CATALOG:
            med_name = med["name"]
            med_pat = re.compile(rf'\b{med_name}\b', re.IGNORECASE)
            for line in lines:
                if med_pat.search(line):
                    # Found drug match in line
                    key = med_name.lower()
                    if key in seen_drugs:
                        continue
                    seen_drugs.add(key)

                    # Dosage
                    dosage_match = re.search(r'(\d+\s*(?:mg|ml|mcg|gm|iu|g))', line, re.IGNORECASE)
                    dosage = dosage_match.group(1) if dosage_match else "Not available in source"

                    # Frequency
                    freq = "Not available in source"
                    if re.search(r'\b(bd|1-0-1|twice\s+daily|bid)\b', line, re.IGNORECASE):
                        freq = "Twice daily (BD / 1-0-1)"
                    elif re.search(r'\b(tid|1-1-1|thrice\s+daily)\b', line, re.IGNORECASE):
                        freq = "Thrice daily (TID / 1-1-1)"
                    elif re.search(r'\b(qid|1-1-1-1|four\s+times)\b', line, re.IGNORECASE):
                        freq = "Four times daily (QID)"
                    elif re.search(r'\b(hs|night|bedtime|0-0-1)\b', line, re.IGNORECASE):
                        freq = "Once daily at Night (HS / 0-0-1)"
                    elif re.search(r'\b(od|1-0-0|once\s+daily)\b', line, re.IGNORECASE):
                        freq = "Once daily (OD)"
                    elif re.search(r'\b(sos|prn|as\s+needed)\b', line, re.IGNORECASE):
                        freq = "As needed (SOS / PRN)"

                    # Timing / Instructions
                    timing = "Not available in source"
                    if re.search(r'\b(ac|before\s+food|empty\s+stomach)\b', line, re.IGNORECASE):
                        timing = "Before meals (AC / Empty stomach)"
                    elif re.search(r'\b(pc|after\s+food|with\s+meals)\b', line, re.IGNORECASE):
                        timing = "After meals (PC)"

                    # Duration
                    dur_match = re.search(r'(\d+\s*(?:days|weeks|months|day|week|month))', line, re.IGNORECASE)
                    duration = dur_match.group(1) if dur_match else "Not available in source"

                    medications.append({
                        "drug_name": med_name,
                        "normalized_name": med.get("generic") or med_name,
                        "dosage": dosage,
                        "frequency": freq,
                        "duration": duration,
                        "instructions": timing,
                        "confidence": None,
                        "source_snippet": line[:150],
                    })

        # Phase B: Generic Tab/Cap regex pattern for medicines not in catalog (e.g. Aspirin, etc.)
        for line in lines:
            generic_rx_match = re.search(
                r'(?:^|\b)(?:Tab|Cap|Tablet|Capsule|Syrup|Inj)\.?\s+([A-Za-z]{3,25})(?:\s+(\d+\s*(?:mg|ml|mcg|gm|g)))?',
                line, re.IGNORECASE
            )
            if generic_rx_match:
                extracted_drug = generic_rx_match.group(1).capitalize()
                key = extracted_drug.lower()
                if key not in seen_drugs and extracted_drug.lower() not in {"the", "and", "for", "with"}:
                    seen_drugs.add(key)
                    dosage_match = generic_rx_match.group(2)
                    if not dosage_match:
                        d_search = re.search(r'(\d+\s*(?:mg|ml|mcg|gm|iu|g))', line, re.IGNORECASE)
                        dosage = d_search.group(1) if d_search else "Not available in source"
                    else:
                        dosage = dosage_match

                    freq = "Not available in source"
                    if re.search(r'\b(bd|1-0-1|twice\s+daily|bid)\b', line, re.IGNORECASE):
                        freq = "Twice daily (BD / 1-0-1)"
                    elif re.search(r'\b(tid|1-1-1|thrice\s+daily)\b', line, re.IGNORECASE):
                        freq = "Thrice daily (TID / 1-1-1)"
                    elif re.search(r'\b(qid|1-1-1-1)\b', line, re.IGNORECASE):
                        freq = "Four times daily (QID)"
                    elif re.search(r'\b(hs|0-0-1|0-1-0|night)\b', line, re.IGNORECASE):
                        freq = "Once daily at Night (HS / 0-0-1)"
                    elif re.search(r'\b(od|1-0-0|once\s+daily)\b', line, re.IGNORECASE):
                        freq = "Once daily (OD)"

                    timing = "Not available in source"
                    if re.search(r'\b(ac|before\s+food)\b', line, re.IGNORECASE):
                        timing = "Before meals (AC)"
                    elif re.search(r'\b(pc|after\s+food)\b', line, re.IGNORECASE):
                        timing = "After meals (PC)"

                    dur_match = re.search(r'(\d+\s*(?:days|weeks|months|day|week|month))', line, re.IGNORECASE)
                    duration = dur_match.group(1) if dur_match else "Not available in source"

                    medications.append({
                        "drug_name": extracted_drug,
                        "normalized_name": self.normalize_medicine_name(extracted_drug) or "Not available in source",
                        "dosage": dosage,
                        "frequency": freq,
                        "duration": duration,
                        "instructions": timing,
                        "confidence": None,
                        "source_snippet": line[:150],
                    })

        # Step 2 — Header field extraction
        header = self.extract_header_fields(ocr_raw_text, hint_doctor=doctor_name, hint_date=doc_date)

        # Step 3 — Confidence mapping
        conf_score, conf_level = self.get_confidence_level(ocr_confidence_score)

        # Step 4 — Parsing status
        if medications:
            parsing_status = ParsingStatus.SUCCESS.value
        else:
            parsing_status = ParsingStatus.NEEDS_USER_REVIEW.value

        return {
            "provider": self.PROVIDER,
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_VERSION,
            "doctor_name": header["doctor_name"],
            "clinic_name": header["clinic_name"],
            "patient_name": header["patient_name"],
            "prescription_date": header["prescription_date"],
            "diagnosis": "Not available in source",
            "notes": "Not available in source",
            "medications": medications,
            "raw_output_text": ocr_raw_text or "",
            "confidence_score": conf_score,
            "confidence_level": conf_level,
            "parsing_status": parsing_status,
        }

    def get_hardware_info(self) -> Dict[str, Any]:
        """Returns metadata about the lightweight extraction pipeline."""
        import platform
        import sys
        try:
            import psutil
            ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
            ram_available_gb = round(psutil.virtual_memory().available / (1024 ** 3), 2)
        except ImportError:
            ram_gb = None
            ram_available_gb = None

        from backend.app.services.ocr_service import HAS_PYTESSERACT, HAS_PYMUPDF

        return {
            "pipeline": "Lightweight Rule-Based OCR Extractor",
            "version": self.MODEL_VERSION,
            "provider": self.PROVIDER,
            "description": (
                "CPU-only, zero-heavy-dependency prescription extraction pipeline. "
                "Uses existing OCR (PyMuPDF / pypdf / pytesseract) + regex clinical extractor. "
                "No PyTorch, Transformers, CUDA, or large model files required."
            ),
            "gpu_required": False,
            "cuda_required": False,
            "torch_required": False,
            "os": platform.system(),
            "python_version": sys.version.split()[0],
            "ram_total_gb": ram_gb,
            "ram_available_gb": ram_available_gb,
            "tesseract_available": HAS_PYTESSERACT,
            "pymupdf_available": HAS_PYMUPDF,
        }

prescription_model_service = PrescriptionModelService()
