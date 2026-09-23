import os
import sys
import json
import pyarrow.parquet as pq
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models.rag import MedicalKnowledgeChunk

def process_medical_qa_dataset(max_records: int = 1500):
    """
    Processes the raw Parquet Medical QA dataset:
    - Validates columns, missing values, empty strings, duplicates
    - Normalizes into clean Q&A pairs
    - Attaches verified repository metadata & license
    - Ingests into the `medical_knowledge_chunks` database table
    - Writes `data/processed/medical_qa_processed.json`
    """
    raw_parquet_path = Path("data/raw/medical_qa/train-00000-of-00001-9bfe4b2cd0370c03.parquet")
    metadata_path = Path("data/raw/medical_qa/dataset_metadata.json")

    if not raw_parquet_path.exists():
        print(f"Error: Parquet file not found at {raw_parquet_path}")
        return None

    # Load verified repository metadata
    metadata = {}
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    dataset_name = metadata.get("dataset_name", "Malikeh1375/medical-question-answering-datasets")
    dataset_version = metadata.get("commit_sha", "29833779cb5921f474d9f469aa85c115277bf489")
    license_type = metadata.get("license", "mit")
    source_url = metadata.get("source_url", "https://huggingface.co/datasets/Malikeh1375/medical-question-answering-datasets")

    print(f"Reading raw Parquet dataset: {raw_parquet_path}")
    table = pq.read_table(str(raw_parquet_path))
    total_raw_rows = table.num_rows
    print(f"Total raw rows in parquet: {total_raw_rows}")

    # Process in batches to inspect and validate
    data_dict = table.to_pydict()
    instructions = data_dict.get("instruction", [])
    inputs = data_dict.get("input", [])
    outputs = data_dict.get("output", [])
    index_ids = data_dict.get("__index_level_0__", [])

    valid_records = []
    seen_questions = set()
    missing_values_count = 0
    empty_strings_count = 0
    duplicate_count = 0

    for i in range(total_raw_rows):
        inst = str(instructions[i] or "").strip()
        inp = str(inputs[i] or "").strip()
        out = str(outputs[i] or "").strip()
        rec_id = str(index_ids[i]) if i < len(index_ids) else str(i)

        # 1. Validate missing / empty
        if not inp or not out:
            empty_strings_count += 1
            continue

        if len(inp) < 10 or len(out) < 15:
            continue

        # 2. Check for question duplicate
        q_key = inp.lower()
        if q_key in seen_questions:
            duplicate_count += 1
            continue
        seen_questions.add(q_key)

        # 3. Clean and format
        combined_content = f"Question: {inp}\nAnswer: {out}"
        token_estimate = len(combined_content.split())

        valid_records.append({
            "record_id": rec_id,
            "dataset_name": dataset_name,
            "dataset_version": dataset_version,
            "license": license_type,
            "source_url": source_url,
            "source_name": "Clinical Consultation Q&A",
            "instruction": inst,
            "input_question": inp,
            "output_answer": out,
            "content": combined_content,
            "token_count": token_estimate
        })

        if len(valid_records) >= max_records:
            break

    print(f"\nValidation Summary:")
    print(f"- Total raw rows inspected: {total_raw_rows}")
    print(f"- Empty/invalid records filtered: {empty_strings_count}")
    print(f"- Duplicate questions detected: {duplicate_count}")
    print(f"- High-quality clean Q&A records extracted: {len(valid_records)}")

    # Save to data/processed
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    processed_file = out_dir / "medical_qa_processed.json"

    processed_manifest = {
        "dataset_metadata": metadata,
        "processing_summary": {
            "total_raw_rows": total_raw_rows,
            "extracted_records_count": len(valid_records),
            "duplicates_filtered": duplicate_count,
            "empty_or_short_filtered": empty_strings_count
        },
        "records": valid_records
    }

    with open(processed_file, "w", encoding="utf-8") as f:
        json.dump(processed_manifest, f, indent=2)
    print(f"Saved processed dataset to {processed_file}")

    # Ingest into database
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Clear existing general knowledge chunks before fresh ingestion
        db.query(MedicalKnowledgeChunk).delete()
        db.commit()

        chunk_objects = [
            MedicalKnowledgeChunk(
                dataset_name=r["dataset_name"],
                dataset_version=r["dataset_version"],
                license=r["license"],
                source_url=r["source_url"],
                source_name=r["source_name"],
                record_id=r["record_id"],
                instruction=r["instruction"],
                input_question=r["input_question"],
                output_answer=r["output_answer"],
                content=r["content"],
                token_count=r["token_count"]
            )
            for r in valid_records
        ]
        db.bulk_save_objects(chunk_objects)
        db.commit()
        print(f"Successfully ingested {len(chunk_objects)} records into `medical_knowledge_chunks` table.")
    finally:
        db.close()

    return processed_manifest

if __name__ == "__main__":
    process_medical_qa_dataset(max_records=2000)
