import os
import pytest
from pathlib import Path
from data.pipeline.dataset_pipeline import DatasetPipeline
from data.pipeline.ocr_evaluator import calculate_cer, calculate_wer, OCREvaluator

def test_duplicate_detection(tmp_path):
    """Tests image hash duplicate detection logic."""
    pipeline = DatasetPipeline(base_dir=tmp_path)
    
    img1 = tmp_path / "img1.png"
    img2 = tmp_path / "img2.png"
    
    content = b"sample_prescription_image_bytes_12345"
    img1.write_bytes(content)
    img2.write_bytes(content)

    hash1 = pipeline.compute_image_hash(img1)
    hash2 = pipeline.compute_image_hash(img2)

    assert hash1 == hash2

def test_data_leakage_checker():
    """Tests data leakage check logic."""
    pipeline = DatasetPipeline()

    train_set = [{"image_hash": "hash_001"}, {"image_hash": "hash_002"}]
    val_set = [{"image_hash": "hash_003"}]
    test_set = [{"image_hash": "hash_004"}]

    clean_report = pipeline.check_data_leakage(train_set, val_set, test_set)
    assert clean_report["has_data_leakage"] is False
    assert clean_report["status"] == "PASSED - ZERO DATA LEAKAGE DETECTED"

    # Simulate leakage
    leaky_val_set = [{"image_hash": "hash_001"}]
    leaky_report = pipeline.check_data_leakage(train_set, leaky_val_set, test_set)
    assert leaky_report["has_data_leakage"] is True
    assert leaky_report["train_val_hash_overlap_count"] == 1

def test_split_ratios():
    """Tests train/validation/test 70/15/15 ratio split."""
    pipeline = DatasetPipeline()
    items = [{"id": f"item_{i}", "image_hash": f"hash_{i}"} for i in range(100)]

    train, val, test = pipeline.split_dataset(items, train_ratio=0.70, val_ratio=0.15)
    
    assert len(train) == 70
    assert len(val) == 15
    assert len(test) == 15

def test_cer_wer_metrics():
    """Tests Character Error Rate (CER) and Word Error Rate (WER) metrics."""
    ref = "tab azithromycin 500mg"
    hyp_exact = "tab azithromycin 500mg"
    hyp_diff = "tab azithromycin 250mg"

    assert calculate_cer(ref, hyp_exact) == 0.0
    assert calculate_wer(ref, hyp_exact) == 0.0

    assert calculate_cer(ref, hyp_diff) > 0.0
    assert calculate_wer(ref, hyp_diff) > 0.0

def test_pipeline_isolation_guarantee():
    """Confirms research pipeline operates within data/ and does not contaminate uploads/."""
    pipeline = DatasetPipeline()
    res = pipeline.run_full_pipeline()

    assert "handwriting_dataset_stats" in res
    assert "ocr_prescription_dataset_stats" in res
    assert res["data_leakage_check"]["has_data_leakage"] is False

    uploads_dir = Path("uploads")
    # Verify no pipeline files were created in uploads/
    pipeline_files_in_uploads = list(uploads_dir.glob("*_manifest.json"))
    assert len(pipeline_files_in_uploads) == 0
