import os
import sys
import json
import time
import statistics
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from data.pipeline.ocr_evaluator import calculate_cer, calculate_wer
from backend.app.services.ocr_service import ocr_service
from backend.app.services.prescription_model_service import prescription_model_service

def evaluate_lightweight_pipeline():
    """
    Evaluates the lightweight, CPU-only prescription OCR and structured extraction pipeline
    on the Phase 3 held-out test datasets.
    """
    test_manifest_file = Path("data/annotations/test_manifest.json")
    if not test_manifest_file.exists():
        print(f"Error: test_manifest.json not found at {test_manifest_file}")
        return

    with open(test_manifest_file, "r", encoding="utf-8") as f:
        test_items = json.load(f)

    print("================================================================================")
    print("PHASE 4 — LIGHTWEIGHT PRESCRIPTION OCR & EXTRACTION EVALUATION")
    print("================================================================================")

    detailed_samples = []
    ocr_latencies = []
    extraction_latencies = []
    total_latencies = []

    cer_list = []
    wer_list = []

    med_tp = 0
    med_fp = 0
    med_fn = 0

    hw_samples_count = 0
    printed_samples_count = 0

    for item in test_items:
        img_path = Path(item["processed_image_path"])
        ground_truth = item.get("ground_truth", "")
        dataset_type = item.get("dataset_type", "unknown")
        if dataset_type == "handwriting_research":
            hw_samples_count += 1
        else:
            printed_samples_count += 1

        # 1. Measure OCR processing time
        t_ocr_start = time.time()
        ocr_result = ocr_service.extract_from_image_file(img_path)
        t_ocr_elapsed = time.time() - t_ocr_start
        ocr_latencies.append(t_ocr_elapsed)

        raw_ocr_text = ocr_result.get("full_text", "")
        conf_score = ocr_result.get("confidence_score", 0.0)

        # 2. Measure Structured Extraction time (rule-based)
        t_ext_start = time.time()
        extracted = prescription_model_service.extract_with_baseline_provider(
            image_path=img_path,
            ocr_raw_text=raw_ocr_text,
            doctor_name=None,
            doc_date=None,
            ocr_confidence_score=conf_score
        )
        t_ext_elapsed = time.time() - t_ext_start
        extraction_latencies.append(t_ext_elapsed)

        t_total = t_ocr_elapsed + t_ext_elapsed
        total_latencies.append(t_total)

        # 3. Calculate CER and WER
        cer = calculate_cer(ground_truth, raw_ocr_text)
        wer = calculate_wer(ground_truth, raw_ocr_text)
        cer_list.append(cer)
        wer_list.append(wer)

        # 4. Evaluate structured medication accuracy where ground truth is available
        extracted_meds = extracted.get("medications", [])
        expected_meds = item.get("medications", [])
        if not expected_meds and ground_truth:
            expected_meds = [ground_truth]

        for exp in expected_meds:
            exp_str = str(exp).lower().strip()
            found = any(
                exp_str in str(m.get("drug_name", "")).lower() or
                str(m.get("drug_name", "")).lower() in exp_str or
                exp_str in str(m.get("normalized_name", "")).lower()
                for m in extracted_meds
            )
            if found:
                med_tp += 1
            else:
                med_fn += 1

        med_fp += max(0, len(extracted_meds) - med_tp)

        detailed_samples.append({
            "image_id": item["id"],
            "dataset_type": dataset_type,
            "ground_truth": ground_truth,
            "ocr_raw_text": raw_ocr_text,
            "cer": round(cer, 4),
            "wer": round(wer, 4),
            "ocr_latency_ms": round(t_ocr_elapsed * 1000, 2),
            "extraction_latency_ms": round(t_ext_elapsed * 1000, 2),
            "total_latency_ms": round(t_total * 1000, 2),
            "confidence_level": extracted["confidence_level"],
            "parsing_status": extracted["parsing_status"],
            "extracted_medications": extracted_meds
        })

    prec = med_tp / max(med_tp + med_fp, 1)
    rec = med_tp / max(med_tp + med_fn, 1)
    f1 = (2 * prec * rec) / max(prec + rec, 1e-9)

    avg_ocr_ms = round(statistics.mean(ocr_latencies) * 1000, 2)
    avg_ext_ms = round(statistics.mean(extraction_latencies) * 1000, 2)
    avg_total_ms = round(statistics.mean(total_latencies) * 1000, 2)
    med_total_ms = round(statistics.median(total_latencies) * 1000, 2)

    avg_cer = round(statistics.mean(cer_list), 4)
    avg_wer = round(statistics.mean(wer_list), 4)

    results = {
        "evaluation_metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pipeline_type": "Lightweight Rule-Based OCR & Structured Extractor (CPU-Only)",
            "neural_models_used": False,
            "pytorch_required": False,
            "transformers_required": False,
            "gpu_required": False,
            "total_test_samples": len(test_items),
            "handwriting_samples": hw_samples_count,
            "printed_ocr_samples": printed_samples_count
        },
        "performance_latency": {
            "average_ocr_time_ms": avg_ocr_ms,
            "average_extraction_time_ms": avg_ext_ms,
            "average_total_processing_time_ms": avg_total_ms,
            "median_total_processing_time_ms": med_total_ms
        },
        "ocr_metrics": {
            "average_cer": avg_cer,
            "average_wer": avg_wer,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4)
        },
        "hardware_info": prescription_model_service.get_hardware_info(),
        "sample_evaluations": detailed_samples
    }

    out_file = Path("data/processed/phase4_lightweight_evaluation.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nEvaluation complete!")
    print(f"Total Samples Tested: {len(test_items)}")
    print(f"Average OCR Time: {avg_ocr_ms} ms")
    print(f"Average Extraction Time: {avg_ext_ms} ms")
    print(f"Average Total Processing Time: {avg_total_ms} ms")
    print(f"Average CER: {avg_cer}")
    print(f"Average WER: {avg_wer}")
    print(f"Results saved to: {out_file}")

    return results

if __name__ == "__main__":
    evaluate_lightweight_pipeline()
