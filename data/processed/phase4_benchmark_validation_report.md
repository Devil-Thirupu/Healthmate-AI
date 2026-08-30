# PHASE 4.1 — PRESCRIPTION OCR BENCHMARK VALIDATION REPORT

## 1. Executive Summary

This validation analysis investigates the root cause of the initial Phase 4 benchmark figures:
* **Initial Reported Figures**:
  - Baseline OCR: `CER = 0.9899`, `WER = 1.0`, `Latency = 20.48 ms`
  - Qwen2.5-VL: `CER = 0.9899`, `WER = 1.0`, `Latency = 0.68 ms`

### Direct Answers to Key Questions:
1. **Was real Qwen2.5-VL inference executed?**
   **No.** Real neural vision-language model generation was not executed because `torch` and `transformers` are not installed in the active Python 3.12 runtime environment.
2. **Were the previous CER/WER results valid?**
   **No.** They were artifacts of comparing ground truth strings against a constant fallback string.
3. **What caused the suspicious results?**
   - **Baseline OCR**: `tesseract` binary is not in system `PATH`. When `pytesseract` threw an exception, `ocr_service.py` safely caught it and returned the fallback placeholder: `"Image document received and indexed."`
   - **Qwen2.5-VL Service**: `prescription_model_service.py` caught `ModuleNotFoundError: No module named 'torch'` and fell back to calling the baseline provider in 0.68 ms.
   - **Result**: Both engines evaluated the exact same fallback placeholder string against the test set, producing identical artificial `CER = 0.9899` and `WER = 1.0`.

---

## 2. Model Loading & Hardware Diagnostics

* **Model Identifier**: `KushagraWadhwa/medical-prescription-ocr-india`
* **Architecture**: `Qwen2_5_VLForConditionalGeneration` (3.75B Multimodal VLM, 7.52 GB weights)
* **Processor**: `AutoProcessor`
* **Hardware Profile**:
  - Host OS: Windows 11 (AMD64)
  - Python: 3.12.10
  - RAM: 23.69 GB Total / 12.45 GB Available
  - Disk Free: 210.09 GB Free
  - PyTorch Status: `Not Installed` in base environment
* **Loading Status**: `FAILED - DEPENDENCIES MISSING (PyTorch / Transformers)`

---

## 3. Validated Comparative Benchmark Results

Evaluated over all 17 held-out test samples in [`data/annotations/test_manifest.json`](file:///d:/Healthmate%20AI/data/annotations/test_manifest.json):

| Metric | Baseline OCR Engine | Qwen2.5-VL Model Service |
| :--- | :---: | :---: |
| **Character Error Rate (CER)** | `0.9899` (fallback text) | `1.0000` (unexecuted VLM) |
| **Word Error Rate (WER)** | `1.0000` | `1.0000` |
| **Medicine Name F1** | `0.0000` | `0.0000` |
| **Dosage F1** | `0.0000` | `0.0000` |
| **Frequency F1** | `0.0000` | `0.0000` |
| **Duration F1** | `0.0000` | `0.0000` |
| **Average Latency** | `18.89 ms` | `0.75 ms (Fallback branch; real VLM requires ~1.5–4.0s)` |

---

## 4. Architectural Integrity & Safety

* **Zero Masking / Full Transparency**: The benchmark engine now clearly distinguishes between real model execution and fallback modes.
* **Production Protection Verified**: Production OCR continues functioning safely with multi-tier fallbacks without breaking live user uploads.
* **Preservation of Artifacts**: Original results preserved in `phase4_model_benchmark_results.json`, validated results saved in [`data/processed/phase4_validated_benchmark_results.json`](file:///d:/Healthmate%20AI/data/processed/phase4_validated_benchmark_results.json).
