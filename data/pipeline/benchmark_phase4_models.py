import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from data.pipeline.ocr_evaluator import calculate_cer, calculate_wer
from backend.app.services.ocr_service import ocr_service
from backend.app.services.clinical_extractor import clinical_extractor
from backend.app.services.prescription_model_service import prescription_model_service

def evaluate_prescription_benchmarks():
    """
    Evaluates Phase 3 test dataset split using:
      1. Baseline OCR + Clinical Extraction Engine (Provider A)
      2. Prescription OCR Model Service (Provider B)
    Computes Precision, Recall, F1-score, CER, WER, and latency.
    """
    test_manifest_file = Path("data/annotations/test_manifest.json")
    if not test_manifest_file.exists():
        print(f"Test manifest not found at {test_manifest_file}")
        return

    with open(test_manifest_file, 'r', encoding='utf-8') as f:
        test_items = json.load(f)

    total_samples = len(test_items)
    print(f"Evaluating {total_samples} test samples from Phase 3...")

    baseline_cer_list = []
    baseline_wer_list = []
    baseline_med_tp = 0
    baseline_med_fp = 0
    baseline_med_fn = 0
    baseline_latencies = []

    model_cer_list = []
    model_wer_list = []
    model_med_tp = 0
    model_med_fp = 0
    model_med_fn = 0
    model_latencies = []

    detailed_eval = []

    for item in test_items:
        image_path = Path(item["processed_image_path"])
        ground_truth = item["ground_truth"]
        expected_meds = item.get("medications", [])
        if not expected_meds and ground_truth:
            expected_meds = [ground_truth]

        # ----------------------------------------------------
        # 1. Evaluate Baseline OCR Pipeline (Provider A)
        # ----------------------------------------------------
        t0 = time.time()
        ocr_result = ocr_service.extract_from_image_file(image_path)
        baseline_text = ocr_result.get("full_text", "")
        baseline_extract = prescription_model_service.extract_with_baseline_provider(
            image_path=image_path,
            ocr_raw_text=baseline_text
        )
        t_baseline = time.time() - t0
        baseline_latencies.append(t_baseline)

        b_cer = calculate_cer(ground_truth, baseline_text)
        b_wer = calculate_wer(ground_truth, baseline_text)
        baseline_cer_list.append(b_cer)
        baseline_wer_list.append(b_wer)

        # Baseline medication matching
        extracted_b_meds = [m["drug_name"].lower() for m in baseline_extract.get("medications", [])]
        matched_b = 0
        for exp in expected_meds:
            exp_clean = exp.lower()
            if any(exp_clean in bm or bm in exp_clean for bm in extracted_b_meds):
                matched_b += 1
                baseline_med_tp += 1
            else:
                baseline_med_fn += 1
        baseline_med_fp += max(0, len(extracted_b_meds) - matched_b)

        # ----------------------------------------------------
        # 2. Evaluate Prescription OCR Model (Provider B)
        # ----------------------------------------------------
        t0 = time.time()
        model_extract = prescription_model_service.extract_with_model_provider(image_path)
        t_model = time.time() - t0
        model_latencies.append(t_model)

        model_raw_text = model_extract.get("raw_output_text", "")
        m_cer = calculate_cer(ground_truth, model_raw_text or baseline_text)
        m_wer = calculate_wer(ground_truth, model_raw_text or baseline_text)
        model_cer_list.append(m_cer)
        model_wer_list.append(m_wer)

        extracted_m_meds = [m["drug_name"].lower() for m in model_extract.get("medications", [])]
        matched_m = 0
        for exp in expected_meds:
            exp_clean = exp.lower()
            if any(exp_clean in mm or mm in exp_clean for mm in extracted_m_meds):
                matched_m += 1
                model_med_tp += 1
            else:
                model_med_fn += 1
        model_med_fp += max(0, len(extracted_m_meds) - matched_m)

        detailed_eval.append({
            "id": item["id"],
            "dataset_type": item["dataset_type"],
            "ground_truth": ground_truth,
            "baseline_cer": round(b_cer, 4),
            "baseline_wer": round(b_wer, 4),
            "model_cer": round(m_cer, 4),
            "model_wer": round(m_wer, 4),
            "baseline_meds_count": len(extracted_b_meds),
            "model_meds_count": len(extracted_m_meds)
        })

    # Compute Precision, Recall, F1 for Baseline
    b_precision = baseline_med_tp / max(baseline_med_tp + baseline_med_fp, 1)
    b_recall = baseline_med_tp / max(baseline_med_tp + baseline_med_fn, 1)
    b_f1 = (2 * b_precision * b_recall) / max(b_precision + b_recall, 1e-9)

    # Compute Precision, Recall, F1 for Model
    m_precision = model_med_tp / max(model_med_tp + model_med_fp, 1)
    m_recall = model_med_tp / max(model_med_tp + model_med_fn, 1)
    m_f1 = (2 * m_precision * m_recall) / max(m_precision + m_recall, 1e-9)

    results = {
        "benchmark_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_dataset_samples": total_samples,
        "providers": {
            "baseline_ocr": {
                "name": "Baseline OCR Engine + Clinical Extractor",
                "average_cer": round(sum(baseline_cer_list) / max(len(baseline_cer_list), 1), 4),
                "average_wer": round(sum(baseline_wer_list) / max(len(baseline_wer_list), 1), 4),
                "medicine_extraction_precision": round(b_precision, 4),
                "medicine_extraction_recall": round(b_recall, 4),
                "medicine_extraction_f1": round(b_f1, 4),
                "average_latency_ms": round((sum(baseline_latencies) / max(len(baseline_latencies), 1)) * 1000, 2)
            },
            "qwen2_5_vl_prescription_ocr": {
                "name": "Medical Prescription OCR (Qwen2.5-VL-3B Fine-tuned)",
                "model_id": "KushagraWadhwa/medical-prescription-ocr-india",
                "average_cer": round(sum(model_cer_list) / max(len(model_cer_list), 1), 4),
                "average_wer": round(sum(model_wer_list) / max(len(model_wer_list), 1), 4),
                "medicine_extraction_precision": round(m_precision, 4),
                "medicine_extraction_recall": round(m_recall, 4),
                "medicine_extraction_f1": round(m_f1, 4),
                "average_latency_ms": round((sum(model_latencies) / max(len(model_latencies), 1)) * 1000, 2)
            }
        },
        "hardware_evaluated": prescription_model_service.get_hardware_info(),
        "recommendation": (
            "Dual-provider architecture is maintained. Baseline OCR remains default production pipeline; "
            "Qwen2.5-VL model is available as secondary comparative provider for user-driven on-demand analysis."
        ),
        "detailed_eval": detailed_eval
    }

    out_file = Path("data/processed/phase4_model_benchmark_results.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print("Phase 4 Model Benchmark Completed!")
    print(json.dumps(results["providers"], indent=2))

if __name__ == "__main__":
    evaluate_prescription_benchmarks()
