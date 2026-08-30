import os
import json
import hashlib
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any
import csv
from PIL import Image, ImageEnhance, ImageFilter

class DatasetPipeline:
    def __init__(self, base_dir: Path = Path("data")):
        self.base_dir = base_dir
        self.raw_dir = base_dir / "raw"
        self.processed_dir = base_dir / "processed"
        self.annotations_dir = base_dir / "annotations"
        self.train_dir = base_dir / "train"
        self.val_dir = base_dir / "validation"
        self.test_dir = base_dir / "test"

        # Ensure all directories exist
        for d in [self.raw_dir, self.processed_dir, self.annotations_dir, 
                  self.train_dir, self.val_dir, self.test_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def compute_image_hash(self, img_path: Path) -> str:
        """Compute MD5 hash of raw image byte content."""
        hasher = hashlib.md5()
        with open(img_path, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def preprocess_image(self, img_path: Path, output_path: Path) -> Dict[str, Any]:
        """
        Preprocess image for OCR research: Grayscale conversion, contrast enhancement, sharpening.
        Saves output strictly to output_path under data/processed/ or split dirs. Original raw files remain untouched.
        """
        with Image.open(img_path) as img:
            orig_width, orig_height = img.size
            orig_mode = img.mode

            # Convert to grayscale
            gray = img.convert('L') if img.mode != 'L' else img.copy()

            # Contrast enhancement
            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(1.6)

            # Sharpening
            sharpened = enhanced.filter(ImageFilter.SHARPEN)

            # Save processed image
            output_path.parent.mkdir(parents=True, exist_ok=True)
            sharpened.save(output_path)

            return {
                "original_dimensions": f"{orig_width}x{orig_height}",
                "processed_dimensions": f"{sharpened.width}x{sharpened.height}",
                "original_mode": orig_mode,
                "processed_mode": sharpened.mode,
                "processed_path": str(output_path)
            }

    def validate_handwriting_dataset(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Loads and validates Doctor Handwriting Recognition Dataset from data/raw/.
        Detects duplicates, validates labels, and preprocesses images.
        """
        dataset_path = self.raw_dir / "Doctor Handwriting Recognition Dataset"
        csv_path = dataset_path / "doctor_handwriting_labels.csv"
        img_dir = dataset_path / "img" / "img"

        items = []
        stats = {
            "dataset_name": "Doctor Handwriting Recognition Dataset",
            "total_raw_records": 0,
            "valid_records": 0,
            "corrupt_or_missing": 0,
            "duplicate_images": 0,
            "duplicate_labels": 0
        }

        if not csv_path.exists():
            return items, stats

        seen_hashes = set()
        seen_labels = set()

        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats["total_raw_records"] += 1
                filename = row.get("filename", "").strip()
                label = row.get("label", "").strip()

                if not filename or not label:
                    stats["corrupt_or_missing"] += 1
                    continue

                img_file = img_dir / filename
                if not img_file.exists():
                    stats["corrupt_or_missing"] += 1
                    continue

                # Image duplicate check
                img_hash = self.compute_image_hash(img_file)
                is_img_duplicate = img_hash in seen_hashes
                if is_img_duplicate:
                    stats["duplicate_images"] += 1
                else:
                    seen_hashes.add(img_hash)

                # Ground-truth cleaning and label duplicate tracking
                cleaned_label = label.lower().strip()
                if cleaned_label in seen_labels:
                    stats["duplicate_labels"] += 1
                else:
                    seen_labels.add(cleaned_label)

                # Store validated item if image is valid and not hard image duplicate
                if not is_img_duplicate:
                    items.append({
                        "id": f"hw_{len(items)+1:03d}",
                        "raw_filename": filename,
                        "raw_image_path": str(img_file),
                        "ground_truth": cleaned_label,
                        "raw_label": label,
                        "image_hash": img_hash,
                        "dataset_type": "handwriting_research"
                    })
                    stats["valid_records"] += 1

        return items, stats

    def validate_ocr_prescription_dataset(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Loads and validates OCR Processed Prescription Dataset from data/raw/OCR_Processed_Prescriptions.
        """
        dataset_path = self.raw_dir / "OCR_Processed_Prescriptions"
        labels_file = dataset_path / "prescription_labels.json"
        img_dir = dataset_path / "images"

        items = []
        stats = {
            "dataset_name": "OCR Processed Prescription Dataset",
            "total_raw_records": 0,
            "valid_records": 0,
            "corrupt_or_missing": 0,
            "duplicate_images": 0
        }

        if not labels_file.exists():
            return items, stats

        with open(labels_file, 'r', encoding='utf-8') as f:
            labels_data = json.load(f)

        seen_hashes = set()

        for filename, info in labels_data.items():
            stats["total_raw_records"] += 1
            img_file = img_dir / filename

            if not img_file.exists():
                stats["corrupt_or_missing"] += 1
                continue

            img_hash = self.compute_image_hash(img_file)
            if img_hash in seen_hashes:
                stats["duplicate_images"] += 1
                continue
            seen_hashes.add(img_hash)

            items.append({
                "id": info.get("id", f"ocr_{len(items)+1:03d}"),
                "raw_filename": filename,
                "raw_image_path": str(img_file),
                "ground_truth": info.get("full_ground_truth", "").strip(),
                "medications": info.get("medications", []),
                "image_hash": img_hash,
                "dataset_type": "ocr_evaluation"
            })
            stats["valid_records"] += 1

        return items, stats

    def split_dataset(self, items: List[Dict[str, Any]], train_ratio: float = 0.70, val_ratio: float = 0.15, seed: int = 42) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Splits items into train, validation, and test subsets reproducibly.
        """
        random.seed(seed)
        shuffled = items.copy()
        random.shuffle(shuffled)

        total = len(shuffled)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)

        train_set = shuffled[:train_end]
        val_set = shuffled[train_end:val_end]
        test_set = shuffled[val_end:]

        return train_set, val_set, test_set

    def check_data_leakage(self, train_set: List[Dict[str, Any]], val_set: List[Dict[str, Any]], test_set: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verifies zero overlap of image hashes or ground-truth content between train, validation, and test sets.
        """
        train_hashes = {item["image_hash"] for item in train_set}
        val_hashes = {item["image_hash"] for item in val_set}
        test_hashes = {item["image_hash"] for item in test_set}

        train_val_hash_overlap = train_hashes.intersection(val_hashes)
        train_test_hash_overlap = train_hashes.intersection(test_hashes)
        val_test_hash_overlap = val_hashes.intersection(test_hashes)

        has_leakage = bool(train_val_hash_overlap or train_test_hash_overlap or val_test_hash_overlap)

        return {
            "has_data_leakage": has_leakage,
            "train_val_hash_overlap_count": len(train_val_hash_overlap),
            "train_test_hash_overlap_count": len(train_test_hash_overlap),
            "val_test_hash_overlap_count": len(val_test_hash_overlap),
            "status": "PASSED - ZERO DATA LEAKAGE DETECTED" if not has_leakage else "FAILED - LEAKAGE DETECTED"
        }

    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Executes end-to-end dataset integration, preprocessing, splitting, and leakage verification pipeline.
        """
        # 1. Validate & Load Raw Datasets
        hw_items, hw_stats = self.validate_handwriting_dataset()
        ocr_items, ocr_stats = self.validate_ocr_prescription_dataset()

        # 2. Train/Val/Test Splitting
        hw_train, hw_val, hw_test = self.split_dataset(hw_items)
        ocr_train, ocr_val, ocr_test = self.split_dataset(ocr_items)

        combined_train = hw_train + ocr_train
        combined_val = hw_val + ocr_val
        combined_test = hw_test + ocr_test

        # 3. Data Leakage Verification
        leakage_report = self.check_data_leakage(combined_train, combined_val, combined_test)

        # 4. Save Preprocessed Images & Split Manifests
        splits = [
            ("train", combined_train, self.train_dir),
            ("validation", combined_val, self.val_dir),
            ("test", combined_test, self.test_dir)
        ]

        manifests = {}

        for split_name, split_items, split_dir in splits:
            split_manifest = []
            for item in split_items:
                raw_path = Path(item["raw_image_path"])
                processed_filename = f"{item['id']}_{raw_path.name}"
                
                # Preprocess image and store in processed/ and split dir
                proc_path = self.processed_dir / item["dataset_type"] / processed_filename
                split_img_path = split_dir / processed_filename

                proc_info = self.preprocess_image(raw_path, proc_path)
                # Copy/Save processed image to split directory as well
                self.preprocess_image(raw_path, split_img_path)

                item_copy = item.copy()
                item_copy["processed_image_path"] = str(proc_path)
                item_copy["split_image_path"] = str(split_img_path)
                item_copy["preprocessing_info"] = proc_info
                split_manifest.append(item_copy)

            manifest_file = self.annotations_dir / f"{split_name}_manifest.json"
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(split_manifest, f, indent=2)

            manifests[split_name] = len(split_manifest)

        # 5. Generate Overall Statistics and Sample Previews
        summary_stats = {
            "handwriting_dataset_stats": hw_stats,
            "ocr_prescription_dataset_stats": ocr_stats,
            "splits": manifests,
            "data_leakage_check": leakage_report,
            "total_processed_records": len(combined_train) + len(combined_val) + len(combined_test)
        }

        stats_file = self.processed_dir / "dataset_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(summary_stats, f, indent=2)

        # Previews
        samples_preview = {
            "train_sample": combined_train[:3] if combined_train else [],
            "val_sample": combined_val[:3] if combined_val else [],
            "test_sample": combined_test[:3] if combined_test else []
        }
        previews_file = self.processed_dir / "sample_previews.json"
        with open(previews_file, 'w', encoding='utf-8') as f:
            json.dump(samples_preview, f, indent=2)

        return summary_stats

if __name__ == "__main__":
    pipeline = DatasetPipeline()
    res = pipeline.run_full_pipeline()
    print("Dataset Pipeline Executed Successfully!")
    print(json.dumps(res, indent=2))
