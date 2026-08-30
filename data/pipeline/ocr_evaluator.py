import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from PIL import Image

# Import backend OCR service for evaluation
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from backend.app.services.ocr_service import ocr_service

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein edit distance between two sequences."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def calculate_cer(reference: str, hypothesis: str) -> float:
    """Calculates Character Error Rate (CER)."""
    if not reference:
        return 0.0 if not hypothesis else 1.0
    dist = levenshtein_distance(reference, hypothesis)
    return min(float(dist) / len(reference), 1.0)

def calculate_wer(reference: str, hypothesis: str) -> float:
    """Calculates Word Error Rate (WER)."""
    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    dist = levenshtein_distance(" ".join(ref_words), " ".join(hyp_words))
    return min(float(dist) / max(len(ref_words), 1), 1.0)

class OCREvaluator:
    def __init__(self, base_dir: Path = Path("data")):
        self.base_dir = base_dir
        self.annotations_dir = base_dir / "annotations"
        self.processed_dir = base_dir / "processed"

    def load_manifest(self, split_name: str) -> List[Dict[str, Any]]:
        manifest_path = self.annotations_dir / f"{split_name}_manifest.json"
        if not manifest_path.exists():
            return []
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyze_errors(self, ref: str, hyp: str) -> List[str]:
        """Categorizes OCR error types."""
        errors = []
        if ref == hyp:
            return errors

        ref_clean = ref.lower().strip()
        hyp_clean = hyp.lower().strip()

        # Dosage digit drop check
        ref_digits = re.findall(r'\d+mg|\d+g|\d+ml', ref_clean)
        hyp_digits = re.findall(r'\d+mg|\d+g|\d+ml', hyp_clean)
        if ref_digits and ref_digits != hyp_digits:
            errors.append("dosage_digit_dropout_or_mismatch")

        # Character substitution check
        if len(ref_clean) == len(hyp_clean):
            diffs = sum(1 for a, b in zip(ref_clean, hyp_clean) if a != b)
            if diffs <= 3:
                errors.append("character_substitution")

        # Handwriting / cursive segmentation error
        if len(hyp_clean) == 0 or len(hyp_clean) < len(ref_clean) * 0.4:
            errors.append("low_contrast_or_cursive_segmentation_failure")

        if not errors:
            errors.append("general_text_mismatch")

        return errors

    def evaluate_split(self, split_name: str) -> Dict[str, Any]:
        """
        Evaluates production OCR service on the specified dataset split.
        Returns detailed evaluation metrics and error analysis.
        """
        items = self.load_manifest(split_name)
        if not items:
            return {"error": f"Manifest for {split_name} split not found."}

        total_samples = len(items)
        cer_list = []
        wer_list = []
        exact_matches = 0
        sig_extracted_correctly = 0
        error_categories = {
            "dosage_digit_dropout_or_mismatch": 0,
            "character_substitution": 0,
            "low_contrast_or_cursive_segmentation_failure": 0,
            "general_text_mismatch": 0
        }

        detailed_results = []

        for item in items:
            image_path = Path(item["processed_image_path"])
            ground_truth = item["ground_truth"]

            # Run production OCR engine
            ocr_result = ocr_service.extract_from_image_file(image_path)
            predicted_text = ocr_result.get("full_text", "").strip()

            cer = calculate_cer(ground_truth, predicted_text)
            wer = calculate_wer(ground_truth, predicted_text)
            cer_list.append(cer)
            wer_list.append(wer)

            is_exact = (ground_truth.lower() == predicted_text.lower())
            if is_exact:
                exact_matches += 1

            # Check sig / medication match
            meds = item.get("medications", [])
            if meds:
                matched_meds = sum(1 for m in meds if m.lower() in predicted_text.lower())
                if matched_meds == len(meds):
                    sig_extracted_correctly += 1
            else:
                if is_exact or cer < 0.2:
                    sig_extracted_correctly += 1

            # Error analysis
            sample_errors = self.analyze_errors(ground_truth, predicted_text)
            for err in sample_errors:
                error_categories[err] = error_categories.get(err, 0) + 1

            detailed_results.append({
                "id": item["id"],
                "dataset_type": item["dataset_type"],
                "ground_truth": ground_truth,
                "predicted_text": predicted_text,
                "cer": round(cer, 4),
                "wer": round(wer, 4),
                "exact_match": is_exact,
                "errors": sample_errors
            })

        avg_cer = sum(cer_list) / max(total_samples, 1)
        avg_wer = sum(wer_list) / max(total_samples, 1)
        exact_match_pct = (exact_matches / max(total_samples, 1)) * 100
        sig_accuracy_pct = (sig_extracted_correctly / max(total_samples, 1)) * 100

        # Split evaluation by dataset type (Handwritten vs Digital OCR)
        handwritten_items = [r for r in detailed_results if r["dataset_type"] == "handwriting_research"]
        ocr_items = [r for r in detailed_results if r["dataset_type"] == "ocr_evaluation"]

        hw_cer = sum(r["cer"] for r in handwritten_items) / max(len(handwritten_items), 1) if handwritten_items else 0.0
        ocr_cer = sum(r["cer"] for r in ocr_items) / max(len(ocr_items), 1) if ocr_items else 0.0

        return {
            "split": split_name,
            "total_samples": total_samples,
            "overall_metrics": {
                "average_cer": round(avg_cer, 4),
                "average_wer": round(avg_wer, 4),
                "exact_match_percentage": round(exact_match_pct, 2),
                "sig_extraction_accuracy": round(sig_accuracy_pct, 2)
            },
            "subgroup_metrics": {
                "handwriting_research": {
                    "count": len(handwritten_items),
                    "average_cer": round(hw_cer, 4)
                },
                "ocr_evaluation": {
                    "count": len(ocr_items),
                    "average_cer": round(ocr_cer, 4)
                }
            },
            "error_categories": error_categories,
            "detailed_results": detailed_results
        }

    def run_full_evaluation(self) -> Dict[str, Any]:
        """Runs evaluation across validation and test splits and outputs evaluation report."""
        val_results = self.evaluate_split("validation")
        test_results = self.evaluate_split("test")

        report = {
            "validation_eval": val_results,
            "test_eval": test_results,
            "recommendation": (
                "Maintain current production OCR service. "
                "Handwriting dataset CER highlights need for specialised handwriting finetuning model "
                "before altering production OCR service for user uploads."
            )
        }

        report_file = self.processed_dir / "ocr_evaluation_results.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        return report

if __name__ == "__main__":
    evaluator = OCREvaluator()
    results = evaluator.run_full_evaluation()
    print("OCR Evaluation Completed Successfully!")
    print(json.dumps(results["test_eval"]["overall_metrics"], indent=2))
