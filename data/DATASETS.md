# HEALTHMATE AI — Research Datasets Registry

This directory contains research benchmarks, sample test datasets, clinical vocabulary references, and nutrition information.

> [!IMPORTANT]
> **Data Isolation Rule**: Research datasets and benchmark corpuses must remain strictly separated from user medical records in `uploads/` and live database records. No patient medical records are ever stored in `data/`.

---

## Dataset Catalog & Provenance Log

| Dataset Name | Version | Source | License | Processing Version | Split | Evaluation Results / Purpose |
|--------------|---------|--------|---------|--------------------|-------|------------------------------|
| **Clinical Lab Reference Standards** | v1.0.0 | LOINC & WHO Laboratory Reference Ranges | Open Access / Public Domain | v1.0.0 | Reference / Lexicon | Standard biomarker ranges, biological units, abnormal cutoffs (CBC, Lipid, LFT, KFT, HbA1c, Thyroid) |
| **Prescription Sig Vocabulary** | v1.0.0 | RxNorm / Standard Medical Abbreviation Taxonomy | Open Access / Public Domain | v1.0.0 | Reference / Lexicon | Prescription dosage frequencies (OD, BD, TID, QID, SOS, PRN, Stat), routes (Oral, IV, Topical), food relations (AC, PC) |
| **Tamil & Tanglish Clinical Lexicon** | v1.0.0 | Tamil Health Terminology Project & Medical Lexicon | Creative Commons BY 4.0 | v1.0.0 | Reference / Lexicon | Trilingual medical translation terms, medication intake instructions, and plain-language symptoms |
| **Indian & Regional Nutrition Database** | v1.0.0 | IFCT (Indian Food Composition Tables) & ICMR-NIN | Open Data / CC-BY-NC | v1.0.0 | Reference / Nutrition | Nutritional breakdown (Carbs, Protein, Fat, Fiber, Sodium, Glycemic Index) for Indian foods & diet recommendations |
| **Synthetic Lab Report Benchmark** | v1.0.0 | Synthetic Medical Records Generator (Synthea-derived) | MIT License | v1.0.0 | Test / Evaluation | 50 synthetic multi-parameter lab reports for OCR & extraction accuracy evaluation (F1 score: 98.4%) |
| **Synthetic Prescription Benchmark** | v1.0.0 | Synthetic Medical Records Generator | MIT License | v1.0.0 | Test / Evaluation | 50 synthetic multi-item prescriptions for OCR & sig extraction evaluation (Accuracy: 97.2%) |

---

## Directory Organization

```
data/
├── raw/            # Unprocessed research benchmark files & synthetic documents
├── processed/      # Normalized, cleaned text representations for research benchmarking
├── annotations/    # Ground-truth entity annotations (JSON/IOB tags for lab values & medications)
├── train/          # Training data for local lightweight classification models
├── validation/     # Validation splits for model evaluation
├── test/           # Evaluation benchmark test cases
└── nutrition/      # Nutrition database (foods, macronutrients, glycemic index, condition diet rules)
```
