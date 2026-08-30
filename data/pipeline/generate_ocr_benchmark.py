import json
import os
from pathlib import Path
from PIL import Image, ImageDraw

def generate_ocr_prescription_benchmark():
    """
    Generates synthetic OCR-processed prescription dataset under data/raw/OCR_Processed_Prescriptions/
    for benchmark evaluation. Does not alter existing files.
    """
    raw_ocr_dir = Path("data/raw/OCR_Processed_Prescriptions")
    img_dir = raw_ocr_dir / "images"
    labels_file = raw_ocr_dir / "prescription_labels.json"

    img_dir.mkdir(parents=True, exist_ok=True)

    sample_prescriptions = [
        {"id": "ocr_rx_001", "clinic": "City Health Clinic", "doctor": "Dr. A. Sharma, MD", "patient": "John Doe", "meds": ["Tab Azithromycin 500mg 1-0-0 5 days", "Tab Paracetamol 650mg 1-1-1 SOS"]},
        {"id": "ocr_rx_002", "clinic": "Apollo Medical Center", "doctor": "Dr. R. K. Patel, MBBS", "patient": "Anita Roy", "meds": ["Cap Amoxicillin 500mg 1-0-1 7 days", "Tab Montelukast 10mg 0-0-1 HS"]},
        {"id": "ocr_rx_003", "clinic": "Care & Cure Clinic", "doctor": "Dr. S. Nair, MD", "patient": "Rajesh Kumar", "meds": ["Tab Metformin 500mg 1-0-1 AC", "Tab Atorvastatin 10mg 0-0-1 HS"]},
        {"id": "ocr_rx_004", "clinic": "Metro General Hospital", "doctor": "Dr. V. Gupta, MS", "patient": "Priya Sharma", "meds": ["Tab Pantoprazole 40mg 1-0-0 BBF", "Tab Domperidone 10mg 1-0-1 AC"]},
        {"id": "ocr_rx_005", "clinic": "Sunrise Diagnostics", "doctor": "Dr. M. K. Das, DNB", "patient": "Vikram Singh", "meds": ["Tab Telmisartan 40mg 1-0-0 OD", "Tab Amlodipine 5mg 1-0-0 OD"]},
        {"id": "ocr_rx_006", "clinic": "Global Health Hospital", "doctor": "Dr. P. Sundaram, MD", "patient": "Meena Kumari", "meds": ["Tab Cefuroxime 500mg 1-0-1 5 days", "Tab Levocetirizine 5mg 0-0-1 HS"]},
        {"id": "ocr_rx_007", "clinic": "Lifecare PolyClinic", "doctor": "Dr. H. Mehta, MD", "patient": "Suresh Raina", "meds": ["Tab Ciprofloxacin 500mg 1-0-1 5 days", "Syrup Benadryl 10ml 1-1-1"]},
        {"id": "ocr_rx_008", "clinic": "Apex Medicare", "doctor": "Dr. K. Iyer, MBBS", "patient": "Lata Venkatesh", "meds": ["Tab Losartan 500mg 1-0-0 OD", "Tab Hydrochlorothiazide 12.5mg 1-0-0"]},
        {"id": "ocr_rx_009", "clinic": "St. Jude Hospital", "doctor": "Dr. E. Thomas, MD", "patient": "David Miller", "meds": ["Cap Omeprazole 20mg 1-0-0 BBF", "Tab Sucralfate 1000mg 1-1-1 AC"]},
        {"id": "ocr_rx_010", "clinic": "Prime Care Clinic", "doctor": "Dr. N. Joshi, MD", "patient": "Sunita Verma", "meds": ["Tab Glimepiride 1mg 1-0-0 BBF", "Tab Teneligliptin 20mg 1-0-0 AC"]},
        {"id": "ocr_rx_011", "clinic": "Fortis Health Center", "doctor": "Dr. G. Saxena, MS", "patient": "Rahul Kapoor", "meds": ["Tab Ibuprofen 400mg 1-0-1 PC", "Tab Paracetamol 500mg 1-1-1 SOS"]},
        {"id": "ocr_rx_012", "clinic": "Max Healthcare", "doctor": "Dr. B. Sengupta, MD", "patient": "Anjali Mishra", "meds": ["Tab Doxycycline 100mg 1-0-1 7 days", "Tab Probiotic 1 cap 1-0-1"]},
        {"id": "ocr_rx_013", "clinic": "Manipal Medical Hub", "doctor": "Dr. R. Deshmukh, MBBS", "patient": "Amitabh Bose", "meds": ["Tab Rosuvastatin 10mg 0-0-1 HS", "Tab Clopidogrel 75mg 1-0-0 OD"]},
        {"id": "ocr_rx_014", "clinic": "Green Valley Clinic", "doctor": "Dr. T. Reddy, MD", "patient": "Kavita Rao", "meds": ["Tab Cetirizine 10mg 0-0-1 HS", "Nasal Spray Fluticasone 2 puffs OD"]},
        {"id": "ocr_rx_015", "clinic": "Unity Care Hospital", "doctor": "Dr. A. Khan, MS", "patient": "Tariq Hussain", "meds": ["Tab Augmentin 625mg 1-0-1 5 days", "Tab Linezolid 600mg 1-0-1"]},
        {"id": "ocr_rx_016", "clinic": "City Health Clinic", "doctor": "Dr. A. Sharma, MD", "patient": "Robert Brown", "meds": ["Tab Azithromycin 500mg 1-0-0 5 days", "Tab Paracetamol 650mg 1-1-1 SOS"]},
        {"id": "ocr_rx_017", "clinic": "Apollo Medical Center", "doctor": "Dr. R. K. Patel, MBBS", "patient": "Sneha Bose", "meds": ["Cap Amoxicillin 500mg 1-0-1 7 days", "Tab Montelukast 10mg 0-0-1 HS"]},
        {"id": "ocr_rx_018", "clinic": "Care & Cure Clinic", "doctor": "Dr. S. Nair, MD", "patient": "Rohan Malhotra", "meds": ["Tab Metformin 500mg 1-0-1 AC", "Tab Atorvastatin 10mg 0-0-1 HS"]},
        {"id": "ocr_rx_019", "clinic": "Metro General Hospital", "doctor": "Dr. V. Gupta, MS", "patient": "Deepak Chopra", "meds": ["Tab Pantoprazole 40mg 1-0-0 BBF", "Tab Domperidone 10mg 1-0-1 AC"]},
        {"id": "ocr_rx_020", "clinic": "Sunrise Diagnostics", "doctor": "Dr. M. K. Das, DNB", "patient": "Shalini Nair", "meds": ["Tab Telmisartan 40mg 1-0-0 OD", "Tab Amlodipine 5mg 1-0-0 OD"]}
    ]

    labels_data = {}

    for rx in sample_prescriptions:
        file_name = f"{rx['id']}.png"
        img_path = img_dir / file_name

        width, height = 800, 600
        image = Image.new("RGB", (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)

        text_lines = [
            f"CLINIC: {rx['clinic']}",
            f"DOCTOR: {rx['doctor']}",
            f"PATIENT: {rx['patient']}",
            "--------------------------------------------------",
            "PRESCRIPTION / MEDICATION INSTRUCTIONS:",
        ]
        for med in rx['meds']:
            text_lines.append(f"  * {med}")
        text_lines.append("--------------------------------------------------")
        text_lines.append("Refill: 0 | Signature: Digitally Signed")

        full_text = "\n".join(text_lines)

        y_offset = 40
        for line in text_lines:
            draw.text((40, y_offset), line, fill=(0, 0, 0))
            y_offset += 30

        image.save(img_path)

        labels_data[file_name] = {
            "id": rx["id"],
            "clinic": rx["clinic"],
            "doctor": rx["doctor"],
            "patient": rx["patient"],
            "medications": rx["meds"],
            "full_ground_truth": full_text
        }

    with open(labels_file, "w", encoding="utf-8") as f:
        json.dump(labels_data, f, indent=2)

    print(f"Generated {len(sample_prescriptions)} OCR benchmark prescriptions in {raw_ocr_dir}")

if __name__ == "__main__":
    generate_ocr_prescription_benchmark()
