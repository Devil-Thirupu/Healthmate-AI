import re
from typing import List, Dict, Any, Optional, Tuple
from backend.app.core.logging import logger

# Standard Clinical Lab Reference Catalog
LAB_STANDARDS = {
    "hba1c": {
        "canonical_name": "HbA1c (Glycated Hemoglobin)",
        "category": "Diabetes",
        "unit": "%",
        "min": 4.0,
        "max": 5.6,
        "critical_high": 9.5,
        "ref_text": "4.0 - 5.6 %",
        "patterns": [r'hba1c', r'glycated\s+hemoglobin', r'glycosylated\s+hemoglobin', r'a1c'],
        "tamil": "சராசரி 3 மாத இரத்த சர்க்கரை அளவு. 5.7% க்கு மேல் இருந்தால் நீரிழிவு அபாயம்.",
        "tanglish": "3 months average blood sugar level. 5.7% mela irundha sugar risk."
    },
    "glucose_fasting": {
        "canonical_name": "Fasting Blood Sugar (FBS)",
        "category": "Diabetes",
        "unit": "mg/dL",
        "min": 70.0,
        "max": 99.0,
        "critical_high": 250.0,
        "ref_text": "70 - 99 mg/dL",
        "patterns": [r'fasting\s+blood\s+sugar', r'glucose\s+fasting', r'fbs', r'fasting\s+glucose'],
        "tamil": "சாப்பிடுவதற்கு முன் இரத்தத்தில் உள்ள சர்க்கரை அளவு.",
        "tanglish": "Saappiduvadharku munnaadi ulla sugar level."
    },
    "glucose_postprandial": {
        "canonical_name": "Postprandial Blood Sugar (PPBS)",
        "category": "Diabetes",
        "unit": "mg/dL",
        "min": 70.0,
        "max": 140.0,
        "critical_high": 300.0,
        "ref_text": "< 140 mg/dL",
        "patterns": [r'post\s+prandial', r'ppbs', r'glucose\s+pp', r'postprandial\s+glucose'],
        "tamil": "உணவு உண்ட 2 மணி நேரம் கழித்து இரத்தத்தில் உள்ள சர்க்கரை அளவு.",
        "tanglish": "Food saappitta 2 hours apram ulla blood sugar level."
    },
    "creatinine": {
        "canonical_name": "Serum Creatinine",
        "category": "Renal / Kidney",
        "unit": "mg/dL",
        "min": 0.6,
        "max": 1.2,
        "critical_high": 2.5,
        "ref_text": "0.6 - 1.2 mg/dL",
        "patterns": [r'serum\s+creatinine', r'creatinine', r's\.creatinine'],
        "tamil": "சிறுநீரகச் செயல்பாடு காட்டும் முக்கிய குறியீடு. 1.2 க்கு மேல் இருந்தால் சிறுநீரக கவனம் தேவை.",
        "tanglish": "Kidney function paarkka mudhal indicator. 1.2 mela irundha kidney care thevai."
    },
    "cholesterol_total": {
        "canonical_name": "Total Cholesterol",
        "category": "Lipid Profile",
        "unit": "mg/dL",
        "min": 125.0,
        "max": 200.0,
        "critical_high": 300.0,
        "ref_text": "< 200 mg/dL",
        "patterns": [r'total\s+cholesterol', r'serum\s+cholesterol', r'cholesterol\s+total'],
        "tamil": "இரத்தத்தில் உள்ள மொத்த கொழுப்பு அளவு.",
        "tanglish": "Rathathil ulla motha cholesterol alavu."
    },
    "cholesterol_ldl": {
        "canonical_name": "LDL Cholesterol (Bad)",
        "category": "Lipid Profile",
        "unit": "mg/dL",
        "min": 0.0,
        "max": 100.0,
        "critical_high": 190.0,
        "ref_text": "< 100 mg/dL",
        "patterns": [r'ldl\s+cholesterol', r'ldl', r'low\s+density\s+lipoprotein'],
        "tamil": "கெட்ட கொழுப்பு (LDL). இதய நலம் காக்க இது 100 க்குள் இருப்பது நல்லது.",
        "tanglish": "Ketta koluppu (LDL). Heart health-ku 100-kulla irukkanum."
    },
    "cholesterol_hdl": {
        "canonical_name": "HDL Cholesterol (Good)",
        "category": "Lipid Profile",
        "unit": "mg/dL",
        "min": 40.0,
        "max": 60.0,
        "critical_high": 100.0,
        "ref_text": "> 40 mg/dL",
        "patterns": [r'hdl\s+cholesterol', r'hdl', r'high\s+density\s+lipoprotein'],
        "tamil": "நல்ல கொழுப்பு (HDL). இது இதயத்தைப் பாதுகாக்கும்.",
        "tanglish": "Nalla koluppu (HDL). Idhu heart-ah protect pannum."
    },
    "triglycerides": {
        "canonical_name": "Triglycerides",
        "category": "Lipid Profile",
        "unit": "mg/dL",
        "min": 50.0,
        "max": 150.0,
        "critical_high": 400.0,
        "ref_text": "< 150 mg/dL",
        "patterns": [r'triglycerides', r'serum\s+triglycerides', r'tg'],
        "tamil": "இரத்தத்தில் உள்ள கொழுப்பு வகை (ட்ரைஹ்ளிசரைடு).",
        "tanglish": "Blood fat category (Triglycerides)."
    },
    "hemoglobin": {
        "canonical_name": "Hemoglobin (Hb)",
        "category": "Complete Blood Count",
        "unit": "g/dL",
        "min": 12.0,
        "max": 16.5,
        "critical_high": 20.0,
        "ref_text": "12.0 - 16.5 g/dL",
        "patterns": [r'hemoglobin', r'haemoglobin', r'\bhb\b'],
        "tamil": "இரத்தத்தில் உள்ள சிவப்பு அணுக்களின் பிராணவாயு கடத்தும் புரதம்.",
        "tanglish": "Rathathil ulla red blood cell oxygen carrier protein."
    },
    "wbc_total": {
        "canonical_name": "Total Leukocyte Count (WBC)",
        "category": "Complete Blood Count",
        "unit": "cells/cu.mm",
        "min": 4000.0,
        "max": 11000.0,
        "critical_high": 25000.0,
        "ref_text": "4,000 - 11,000 /cu.mm",
        "patterns": [r'total\s+leukocyte\s+count', r'total\s+wbc\s+count', r'wbc\s+count', r'tlc', r'wbc'],
        "tamil": "இரத்த வெள்ளை அணுக்கள். தொற்று மற்றும் நோயெதிர்ப்பு சக்தி காட்டும் குறியீடு.",
        "tanglish": "White blood cells. Infection mattrum immunity indicator."
    },
    "platelets": {
        "canonical_name": "Platelet Count",
        "category": "Complete Blood Count",
        "unit": "lakh/cu.mm",
        "min": 1.5,
        "max": 4.5,
        "critical_high": 10.0,
        "ref_text": "1.5 - 4.5 lakh/cu.mm",
        "patterns": [r'platelet\s+count', r'platelets'],
        "tamil": "இரத்தத் தட்டுக்கள். இரத்தம் உறைதலுக்கு அவசியமானது.",
        "tanglish": "Ratha thathukkal (Platelets). Blood clot aaga thevai."
    },
    "tsh": {
        "canonical_name": "TSH (Thyroid Stimulating Hormone)",
        "category": "Thyroid Panel",
        "unit": "uIU/mL",
        "min": 0.35,
        "max": 4.94,
        "critical_high": 20.0,
        "ref_text": "0.35 - 4.94 uIU/mL",
        "patterns": [r'tsh', r'thyroid\s+stimulating\s+hormone'],
        "tamil": "தைராய்டு சுரப்பியின் செயல்பாடு காட்டும் ஹார்மோன்.",
        "tanglish": "Thyroid hormone level indicator."
    }
}

# Common Medication Database for Prescription Parsing
MEDICATION_CATALOG = [
    {"name": "Metformin", "generic": "Metformin HCl", "form": "Tablet", "category": "Antidiabetic", "tamil": "சர்க்கரை நோய்க்கான மாத்திரை. உணவுக்குப் பின் உட்கொள்ளவும்.", "tanglish": "Sugar tablet. Food-ku pinnaadi saapidavum."},
    {"name": "Atorvastatin", "generic": "Atorvastatin Calcium", "form": "Tablet", "category": "Lipid Lowering", "tamil": "கொழுப்பு குறைக்கும் மாத்திரை. இரவு உணவுக்குப் பின் உட்கொள்ளவும்.", "tanglish": "Cholesterol tablet. Night dinner-ku apram saapidavum."},
    {"name": "Telmisartan", "generic": "Telmisartan", "form": "Tablet", "category": "Antihypertensive", "tamil": "இரத்த அழுத்தத்தைக் கட்டுப்படுத்தும் மாத்திரை. காலை நேரத்தில் உட்கொள்ளவும்.", "tanglish": "Blood pressure control tablet. Morning eduthukkollavum."},
    {"name": "Amlodipine", "generic": "Amlodipine Besylate", "form": "Tablet", "category": "Antihypertensive", "tamil": "இரத்த அழுத்த மாத்திரை.", "tanglish": "Blood pressure tablet."},
    {"name": "Pantoprazole", "generic": "Pantoprazole Sodium", "form": "Tablet / Capsule", "category": "Antacid / PPI", "tamil": "அசிடிட்டி / நெஞ்செரிச்சல் மாத்திரை. காலையில் வெறும் வயிற்றில் உட்கொள்ளவும்.", "tanglish": "Acidity / Gas tablet. Morning verum vayithil saapidavum."},
    {"name": "Omeprazole", "generic": "Omeprazole", "form": "Capsule", "category": "Antacid / PPI", "tamil": "அசிடிட்டி மாத்திரை. உணவுக்கு முன்.", "tanglish": "Acidity tablet. Before food."},
    {"name": "Amoxicillin", "generic": "Amoxicillin Trihydrate", "form": "Capsule / Syrup", "category": "Antibiotic", "tamil": "பாக்டீரியா தொற்றுக்கான ஆன்டிபயாடிக். மருத்துவர் கூறிய காலம் வரை முழுமையாக உட்கொள்ளவும்.", "tanglish": "Antibiotic. Doctor sonna duration full-aa mudikkavum."},
    {"name": "Azithromycin", "generic": "Azithromycin", "form": "Tablet", "category": "Antibiotic", "tamil": "ஆன்டிபயாடிக் மாத்திரை.", "tanglish": "Antibiotic tablet."},
    {"name": "Paracetamol", "generic": "Acetaminophen", "form": "Tablet / Syrup", "category": "Analgesic / Antipyretic", "tamil": "காய்ச்சல் மற்றும் உடல் வலி நிவாரணி.", "tanglish": "Fever and body pain relief tablet."},
    {"name": "Thyronorm", "generic": "Levothyroxine Sodium", "form": "Tablet", "category": "Thyroid Hormone", "tamil": "தைராய்டு மாத்திரை. காலையில் எழுந்தவுடன் வெறும் வயிற்றில் குடிக்கவும்.", "tanglish": "Thyroid tablet. Morning ezhundhadhum verum vayithil saapidavum."},
    {"name": "Glimepiride", "generic": "Glimepiride", "form": "Tablet", "category": "Antidiabetic", "tamil": "சர்க்கரை அளவு கட்டுப்படுத்தும் மாத்திரை.", "tanglish": "Blood sugar control tablet."},
    {"name": "Vildagliptin", "generic": "Vildagliptin", "form": "Tablet", "category": "Antidiabetic", "tamil": "சர்க்கரை மாத்திரை.", "tanglish": "Diabetes tablet."},
    {"name": "Rosuvastatin", "generic": "Rosuvastatin", "form": "Tablet", "category": "Lipid Lowering", "tamil": "கொழுப்பு குறைக்கும் மாத்திரை.", "tanglish": "Cholesterol tablet."},
    {"name": "Cetirizine", "generic": "Cetirizine HCl", "form": "Tablet / Syrup", "category": "Antihistamine", "tamil": "அலர்ஜி, சளி, தும்மல் மாத்திரை.", "tanglish": "Allergy, cold and sneezing tablet."},
    {"name": "Montelukast", "generic": "Montelukast Sodium", "form": "Tablet", "category": "Antiasthmatic", "tamil": "சுவாச ஒவ்வாமை மற்றும் ஆஸ்துமா மாத்திரை.", "tanglish": "Asthma and breathing allergy tablet."}
]

class ClinicalExtractor:
    def extract_lab_tests(self, text: str, document_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract structured lab biomarker test records from OCR text."""
        extracted_tests = []
        if not text:
            return extracted_tests

        lines = [line.strip() for line in text.split('\n') if line.strip()]

        for standard_key, standard_info in LAB_STANDARDS.items():
            matched_test = None
            
            for line in lines:
                line_lower = line.lower()
                for pattern in standard_info["patterns"]:
                    match = re.search(pattern, line_lower)
                    if match:
                        # Found a line mentioning the test. Search for numeric value AFTER the test name
                        after_text = line[match.end():]
                        numbers = re.findall(r'(\d+(?:\.\d+)?)', after_text)
                        if numbers:
                            # Observed value is the first number after the test parameter name
                            val_str = numbers[0]
                            try:
                                num_val = float(val_str)
                                # Assign flag
                                flag = "normal"
                                if num_val > standard_info.get("critical_high", 9999):
                                    flag = "critical"
                                elif num_val > standard_info["max"]:
                                    flag = "high"
                                elif num_val < standard_info["min"]:
                                    flag = "low"

                                matched_test = {
                                    "test_name": standard_info["canonical_name"],
                                    "canonical_name": standard_key,
                                    "test_category": standard_info["category"],
                                    "observed_value": val_str,
                                    "numeric_value": num_val,
                                    "unit": standard_info["unit"],
                                    "reference_range_min": standard_info["min"],
                                    "reference_range_max": standard_info["max"],
                                    "reference_range_text": standard_info["ref_text"],
                                    "flag": flag,
                                    "test_date": document_date,
                                    "explanation_tamil": standard_info["tamil"],
                                    "explanation_tanglish": standard_info["tanglish"],
                                    "confidence_score": 0.95,
                                    "original_ocr_snippet": line[:150]
                                }
                                break
                            except ValueError:
                                pass
                if matched_test:
                    break

            if matched_test:
                extracted_tests.append(matched_test)

        return extracted_tests

    def extract_prescriptions(self, text: str, doctor_name: Optional[str] = None, document_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract structured prescription medication items from OCR text."""
        extracted_rx = []
        if not text:
            return extracted_rx

        lines = [line.strip() for line in text.split('\n') if line.strip()]

        for med in MEDICATION_CATALOG:
            med_name = med["name"]
            med_pattern = re.compile(rf'\b{med_name}\b', re.IGNORECASE)

            for line in lines:
                if med_pattern.search(line):
                    # Found medication line! Extract dosage, frequency, and instructions
                    dosage_match = re.search(r'(\d+\s*(?:mg|ml|mcg|gm|iu|g))', line, re.IGNORECASE)
                    dosage = dosage_match.group(1) if dosage_match else "Standard"

                    # Frequency extraction (OD, BD, TID, 1-0-1, 1-0-0, etc.)
                    freq = "Once daily (OD)"
                    timing = "After food (PC)"

                    if re.search(r'\b(bd|1-0-1|twice\s+daily|bid)\b', line, re.IGNORECASE):
                        freq = "Twice daily (BD / 1-0-1)"
                    elif re.search(r'\b(tid|1-1-1|thrice\s+daily)\b', line, re.IGNORECASE):
                        freq = "Thrice daily (TID / 1-1-1)"
                    elif re.search(r'\b(qid|1-1-1-1|four\s+times)\b', line, re.IGNORECASE):
                        freq = "Four times daily (QID)"
                    elif re.search(r'\b(hs|night|bedtime|0-0-1)\b', line, re.IGNORECASE):
                        freq = "Once daily at Night (HS / 0-0-1)"
                    elif re.search(r'\b(sos|prn|as\s+needed)\b', line, re.IGNORECASE):
                        freq = "As needed (SOS / PRN)"

                    if re.search(r'\b(ac|before\s+food|empty\s+stomach)\b', line, re.IGNORECASE):
                        timing = "Before meals (AC / Empty stomach)"
                    elif re.search(r'\b(pc|after\s+food|with\s+meals)\b', line, re.IGNORECASE):
                        timing = "After meals (PC)"

                    duration_match = re.search(r'(\d+\s*(?:days|weeks|months|day|week|month))', line, re.IGNORECASE)
                    duration = duration_match.group(1) if duration_match else "30 days"

                    extracted_rx.append({
                        "medication_name": med["name"],
                        "generic_name": med["generic"],
                        "dosage": dosage,
                        "form": med["form"],
                        "route": "Oral",
                        "frequency": freq,
                        "timing_instructions": timing,
                        "duration": duration,
                        "doctor_name": doctor_name,
                        "prescribed_date": document_date,
                        "instructions_tamil": med["tamil"],
                        "instructions_tanglish": med["tanglish"],
                        "confidence_score": 0.95,
                        "original_ocr_snippet": line[:150]
                    })
                    break

        return extracted_rx

    def create_rag_chunks(self, document_id: int, user_id: int, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Split document pages into clean RAG chunks with page and character coordinates."""
        chunks = []
        chunk_idx = 0

        for p_idx, page in enumerate(pages_data):
            page_text = page.get("text", "").strip()
            page_num = page.get("page_number", p_idx + 1)
            
            if not page_text:
                continue

            # Split paragraphs or 400-char blocks
            paragraphs = [p.strip() for p in page_text.split('\n\n') if p.strip()]
            if not paragraphs:
                paragraphs = [page_text]

            current_pos = 0
            for para in paragraphs:
                char_start = current_pos
                char_end = char_start + len(para)
                current_pos = char_end + 2
                
                token_count = len(para.split())
                chunks.append({
                    "document_id": document_id,
                    "user_id": user_id,
                    "chunk_index": chunk_idx,
                    "page_number": page_num,
                    "section_heading": f"Page {page_num}",
                    "content": para,
                    "char_start": char_start,
                    "char_end": char_end,
                    "token_count": token_count,
                    "embedding_json": [] # Placeholder for dense embeddings in Phase 3
                })
                chunk_idx += 1

        return chunks

clinical_extractor = ClinicalExtractor()
