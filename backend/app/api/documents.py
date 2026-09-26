from datetime import datetime, timezone
from typing import Any, List, Optional, Dict
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.document import Document, DocumentCategory, OCRStatus
from backend.app.models.clinical import Prescription, LabTest
from backend.app.models.rag import RAGChunk
from backend.app.models.prescription_extraction import (
    PrescriptionExtraction, ExtractionCorrection, ConfidenceLevel, ParsingStatus
)
from backend.app.schemas.prescription_extraction import (
    PrescriptionExtractionResponse, ExtractionCorrectionCreate, ExtractionCorrectionResponse,
    UserReviewConfirmRequest
)
from backend.app.schemas.document import (
    DocumentResponse, DocumentDetailResponse, DocumentUpdate, DocumentCorrectionRequest
)
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.services.storage_service import storage_service
from backend.app.services.audit_service import audit_service
from backend.app.services.ocr_service import ocr_service
from backend.app.services.clinical_extractor import clinical_extractor
from backend.app.services.prescription_model_service import prescription_model_service
from backend.app.core.logging import logger

router = APIRouter()

def execute_ocr_and_extraction(doc_id: int, user_id: int, file_path_str: str, category: str, doctor_name: Optional[str], doc_date: Optional[str], db: Session):
    """Execute multi-tier OCR, extract structured clinical entities, and index RAG chunks."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return

    try:
        doc.ocr_status = OCRStatus.PROCESSING.value
        db.commit()

        # 1. Run OCR extraction
        ocr_result = ocr_service.process_document(file_path_str, category)
        
        doc.ocr_raw_text = ocr_result.get("full_text", "")
        doc.ocr_confidence_score = ocr_result.get("confidence_score", 0.0)
        doc.ocr_language_detected = ocr_result.get("language", "en")
        doc.metadata_json = {
            "page_count": ocr_result.get("page_count", 1),
            "pages": ocr_result.get("pages", []),
            "dimensions": ocr_result.get("dimensions"),
            "format": ocr_result.get("format"),
            "extracted_at": datetime.now(timezone.utc).isoformat()
        }

        # 2. Extract structured clinical entities based on document category and text content
        full_text = doc.ocr_raw_text or ""

        # Extract Lab Tests
        lab_data = clinical_extractor.extract_lab_tests(full_text, doc_date)
        for item in lab_data:
            lab_test = LabTest(
                document_id=doc.id,
                user_id=user_id,
                test_name=item["test_name"],
                canonical_name=item["canonical_name"],
                test_category=item["test_category"],
                observed_value=item["observed_value"],
                numeric_value=item["numeric_value"],
                unit=item["unit"],
                reference_range_min=item["reference_range_min"],
                reference_range_max=item["reference_range_max"],
                reference_range_text=item["reference_range_text"],
                flag=item["flag"],
                test_date=item["test_date"],
                explanation_tamil=item["explanation_tamil"],
                explanation_tanglish=item["explanation_tanglish"],
                confidence_score=item["confidence_score"],
                original_ocr_snippet=item["original_ocr_snippet"]
            )
            db.add(lab_test)

        # Extract Prescriptions
        rx_data = clinical_extractor.extract_prescriptions(full_text, doctor_name, doc_date)
        for item in rx_data:
            prescription = Prescription(
                document_id=doc.id,
                user_id=user_id,
                medication_name=item["medication_name"],
                generic_name=item["generic_name"],
                dosage=item["dosage"],
                form=item["form"],
                route=item["route"],
                frequency=item["frequency"],
                timing_instructions=item["timing_instructions"],
                duration=item["duration"],
                doctor_name=item["doctor_name"],
                prescribed_date=item["prescribed_date"],
                instructions_tamil=item["instructions_tamil"],
                instructions_tanglish=item["instructions_tanglish"],
                confidence_score=item["confidence_score"],
                original_ocr_snippet=item["original_ocr_snippet"]
            )
            db.add(prescription)

        # 2.5 Automatically generate baseline PrescriptionExtraction entity for prescriptions
        if category == DocumentCategory.PRESCRIPTION.value or rx_data:
            ocr_conf = ocr_result.get("confidence_score")  # float 0–100 from OCR engine, or None
            baseline_extraction = prescription_model_service.extract_with_baseline_provider(
                image_path=Path(file_path_str),
                ocr_raw_text=full_text,
                doctor_name=doctor_name,
                doc_date=doc_date,
                ocr_confidence_score=ocr_conf,
            )
            extraction_record = PrescriptionExtraction(
                document_id=doc.id,
                user_id=user_id,
                provider=baseline_extraction["provider"],
                model_name=baseline_extraction["model_name"],
                model_version=baseline_extraction["model_version"],
                raw_output_text=baseline_extraction["raw_output_text"],
                doctor_name=baseline_extraction["doctor_name"],
                clinic_name=baseline_extraction["clinic_name"],
                patient_name=baseline_extraction["patient_name"],
                prescription_date=baseline_extraction["prescription_date"],
                diagnosis=baseline_extraction["diagnosis"],
                notes=baseline_extraction["notes"],
                medications_json=baseline_extraction["medications"],
                confidence_score=baseline_extraction["confidence_score"],
                confidence_level=baseline_extraction["confidence_level"],
                parsing_status=baseline_extraction["parsing_status"],
                is_user_reviewed=False
            )
            db.add(extraction_record)

        # 3. Create RAG Chunks for evidence-grounded search
        pages_list = ocr_result.get("pages", [])
        if not pages_list and full_text:
            pages_list = [{"page_number": 1, "text": full_text}]
        rag_chunks_data = clinical_extractor.create_rag_chunks(doc.id, user_id, pages_list)
        for c in rag_chunks_data:
            chunk_row = RAGChunk(
                document_id=c["document_id"],
                user_id=c["user_id"],
                chunk_index=c["chunk_index"],
                page_number=c["page_number"],
                section_heading=c["section_heading"],
                content=c["content"],
                char_start=c["char_start"],
                char_end=c["char_end"],
                token_count=c["token_count"],
                embedding_json=c["embedding_json"]
            )
            db.add(chunk_row)

        doc.ocr_status = OCRStatus.COMPLETED.value
        db.commit()
        db.refresh(doc)
        logger.info(f"OCR and extraction completed successfully for doc {doc.id}")

    except Exception as e:
        logger.error(f"OCR processing failed for document {doc.id}: {e}")
        doc.ocr_status = OCRStatus.FAILED.value
        db.commit()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form(DocumentCategory.OTHER.value),
    document_date: Optional[str] = Form(None),
    doctor_name: Optional[str] = Form(None),
    clinic_or_lab: Optional[str] = Form(None),
    specialty: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Upload and securely store a medical document with SHA-256 integrity and automatic OCR extraction."""
    doc_category = category or DocumentCategory.OTHER.value

    # 1. Save file to local disk AND mirror to Supabase Storage (when configured)
    stored_filename, clean_original_name, file_path, file_size, sha256_hash, supabase_storage_path = \
        await storage_service.save_uploaded_file(
            file=file,
            user_id=current_user.id,
            category=doc_category,
        )

    doc_title = title.strip() if title else clean_original_name
    doc_date = document_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 2. Create document record in database
    doc = Document(
        user_id=current_user.id,
        original_filename=clean_original_name,
        stored_filename=stored_filename,
        file_path=file_path,
        file_size_bytes=file_size,
        mime_type=file.content_type or "application/octet-stream",
        file_hash_sha256=sha256_hash,
        category=doc_category,
        title=doc_title,
        document_date=doc_date,
        doctor_name=doctor_name,
        clinic_or_lab=clinic_or_lab,
        specialty=specialty,
        ocr_status=OCRStatus.PENDING.value,
        ocr_confidence_score=0.0,
        # Store Supabase storage path in metadata so we can issue signed URLs later
        metadata_json={
            "supabase_storage_path": supabase_storage_path,
        }
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 3. Execute OCR and Clinical Extraction synchronously for immediate result availability
    execute_ocr_and_extraction(
        doc_id=doc.id,
        user_id=current_user.id,
        file_path_str=file_path,
        category=doc.category,
        doctor_name=doctor_name,
        doc_date=doc_date,
        db=db
    )

    # 4. Record Audit Log
    audit_service.log_event(
        db=db,
        action="DOC_UPLOAD",
        resource_type="document",
        user_id=current_user.id,
        resource_id=str(doc.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={
            "filename": clean_original_name,
            "category": doc.category,
            "sha256": sha256_hash,
            "size_bytes": file_size,
            "ocr_status": doc.ocr_status
        }
    )

    db.refresh(doc)
    return doc

@router.post("/{doc_id}/reprocess", response_model=DocumentDetailResponse)
def reprocess_document_ocr(
    doc_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Reprocess OCR and structured extraction for an existing document."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Clear previous extracted records
    db.query(Prescription).filter(Prescription.document_id == doc.id).delete()
    db.query(LabTest).filter(LabTest.document_id == doc.id).delete()
    db.query(RAGChunk).filter(RAGChunk.document_id == doc.id).delete()
    db.commit()

    execute_ocr_and_extraction(
        doc_id=doc.id,
        user_id=current_user.id,
        file_path_str=doc.file_path,
        category=doc.category,
        doctor_name=doc.doctor_name,
        doc_date=doc.document_date,
        db=db
    )

    audit_service.log_event(
        db=db,
        action="DOC_REPROCESS_OCR",
        resource_type="document",
        user_id=current_user.id,
        resource_id=str(doc.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )

    return get_document_details(doc_id=doc.id, request=request, current_user=current_user, db=db)

@router.put("/{doc_id}/corrections", response_model=DocumentDetailResponse)
def correct_extracted_document(
    doc_id: int,
    correction: DocumentCorrectionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Human-in-the-loop manual corrections for OCR raw text, prescriptions, or lab tests."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if correction.title:
        doc.title = correction.title
    if correction.category:
        doc.category = correction.category
    if correction.document_date:
        doc.document_date = correction.document_date
    if correction.doctor_name:
        doc.doctor_name = correction.doctor_name
    if correction.clinic_or_lab:
        doc.clinic_or_lab = correction.clinic_or_lab
    if correction.ocr_raw_text is not None:
        doc.ocr_raw_text = correction.ocr_raw_text

    doc.has_manual_corrections = True
    doc.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Update or replace prescriptions if provided
    if correction.prescriptions is not None:
        db.query(Prescription).filter(Prescription.document_id == doc.id).delete()
        for p in correction.prescriptions:
            rx = Prescription(
                document_id=doc.id,
                user_id=current_user.id,
                medication_name=p.get("medication_name", "Medication"),
                generic_name=p.get("generic_name"),
                dosage=p.get("dosage"),
                form=p.get("form", "Tablet"),
                route=p.get("route", "Oral"),
                frequency=p.get("frequency"),
                timing_instructions=p.get("timing_instructions"),
                duration=p.get("duration"),
                doctor_name=doc.doctor_name,
                prescribed_date=doc.document_date,
                instructions_tamil=p.get("instructions_tamil"),
                instructions_tanglish=p.get("instructions_tanglish"),
                confidence_score=1.0,
                is_manual_edited=True
            )
            db.add(rx)

    # Update or replace lab tests if provided
    if correction.lab_tests is not None:
        db.query(LabTest).filter(LabTest.document_id == doc.id).delete()
        for l in correction.lab_tests:
            lab = LabTest(
                document_id=doc.id,
                user_id=current_user.id,
                test_name=l.get("test_name", "Lab Test"),
                canonical_name=l.get("canonical_name"),
                test_category=l.get("test_category", "General"),
                observed_value=str(l.get("observed_value", "")),
                numeric_value=float(l.get("numeric_value")) if l.get("numeric_value") is not None else None,
                unit=l.get("unit"),
                reference_range_min=float(l.get("reference_range_min")) if l.get("reference_range_min") is not None else None,
                reference_range_max=float(l.get("reference_range_max")) if l.get("reference_range_max") is not None else None,
                reference_range_text=l.get("reference_range_text"),
                flag=l.get("flag", "normal"),
                test_date=doc.document_date,
                explanation_tamil=l.get("explanation_tamil"),
                explanation_tanglish=l.get("explanation_tanglish"),
                confidence_score=1.0,
                is_manual_edited=True
            )
            db.add(lab)

    db.commit()

    audit_service.log_event(
        db=db,
        action="DOC_MANUAL_CORRECTION",
        resource_type="document",
        user_id=current_user.id,
        resource_id=str(doc.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"doc_title": doc.title}
    )

    return get_document_details(doc_id=doc.id, request=request, current_user=current_user, db=db)

@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    category: Optional[str] = None,
    ocr_status: Optional[str] = None,
    search: Optional[str] = None,
    include_archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """List documents belonging to the authenticated user with optional filters."""
    query = db.query(Document).filter(Document.user_id == current_user.id)
    
    if not include_archived:
        query = query.filter(Document.is_archived == False)
    if category and category != "all":
        query = query.filter(Document.category == category)
    if ocr_status:
        query = query.filter(Document.ocr_status == ocr_status)
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (Document.title.ilike(search_term)) |
            (Document.doctor_name.ilike(search_term)) |
            (Document.clinic_or_lab.ilike(search_term)) |
            (Document.original_filename.ilike(search_term))
        )
        
    return query.order_by(desc(Document.created_at)).all()

@router.get("/{doc_id}", response_model=DocumentDetailResponse)
def get_document_details(
    doc_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get detailed document information along with extracted clinical fields."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Fetch associated extracted clinical items
    prescriptions = db.query(Prescription).filter(Prescription.document_id == doc.id).all()
    lab_tests = db.query(LabTest).filter(LabTest.document_id == doc.id).all()

    audit_service.log_event(
        db=db,
        action="DOC_VIEW",
        resource_type="document",
        user_id=current_user.id,
        resource_id=str(doc.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"title": doc.title}
    )

    doc_dict = DocumentResponse.model_validate(doc).model_dump()
    doc_dict["ocr_raw_text"] = doc.ocr_raw_text
    doc_dict["prescriptions"] = [
        {
            "id": p.id,
            "medication_name": p.medication_name,
            "generic_name": p.generic_name,
            "dosage": p.dosage,
            "form": p.form,
            "route": p.route,
            "frequency": p.frequency,
            "timing_instructions": p.timing_instructions,
            "duration": p.duration,
            "instructions_tamil": p.instructions_tamil,
            "instructions_tanglish": p.instructions_tanglish,
            "confidence_score": p.confidence_score,
            "is_manual_edited": p.is_manual_edited
        }
        for p in prescriptions
    ]
    doc_dict["lab_tests"] = [
        {
            "id": l.id,
            "test_name": l.test_name,
            "canonical_name": l.canonical_name,
            "test_category": l.test_category,
            "observed_value": l.observed_value,
            "numeric_value": l.numeric_value,
            "unit": l.unit,
            "reference_range_min": l.reference_range_min,
            "reference_range_max": l.reference_range_max,
            "reference_range_text": l.reference_range_text,
            "flag": l.flag,
            "explanation_tamil": l.explanation_tamil,
            "explanation_tanglish": l.explanation_tanglish,
            "confidence_score": l.confidence_score,
            "is_manual_edited": l.is_manual_edited
        }
        for l in lab_tests
    ]
    return doc_dict

@router.get("/{doc_id}/download")
def download_document(
    doc_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download the original file with SHA-256 integrity verification.

    If the file is in Supabase Storage, returns a 1-hour signed URL redirect.
    Falls back to serving the local copy when Supabase is not configured.
    """
    from fastapi.responses import RedirectResponse
    from backend.app.core.config import settings as _cfg

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    audit_service.log_event(
        db=db,
        action="DOC_DOWNLOAD",
        resource_type="document",
        user_id=current_user.id,
        resource_id=str(doc.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )

    # --- Supabase Storage path: issue a signed URL redirect ---
    supabase_path = (doc.metadata_json or {}).get("supabase_storage_path", "")
    if supabase_path and _cfg.supabase_enabled:
        try:
            from backend.app.services.supabase_storage_service import supabase_storage
            signed_url = supabase_storage.create_signed_url(
                storage_path=supabase_path,
                category=doc.category,
                expiry_seconds=3600,
            )
            if signed_url:
                return RedirectResponse(url=signed_url, status_code=302)
        except Exception as exc:
            logger.warning(f"[Supabase] Signed URL generation failed, falling back to local: {exc}")

    # --- Fallback: serve from local disk ---
    safe_path = storage_service.resolve_safe_path(current_user.id, doc.stored_filename)
    if not safe_path or not safe_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical file missing on server")

    # Verify SHA-256 integrity on local file
    if not storage_service.verify_integrity(str(safe_path), doc.file_hash_sha256):
        logger.error(f"Integrity check failed for document {doc.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File integrity check failed: file may have been modified or corrupted."
        )

    return FileResponse(
        path=safe_path,
        media_type=doc.mime_type,
        filename=doc.original_filename
    )

@router.get("/{doc_id}/preview")
def preview_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Serve file inline for browser/PDF/image preview without forcing download.

    Uses a Supabase signed URL redirect when available, otherwise serves locally.
    """
    from fastapi.responses import RedirectResponse
    from backend.app.core.config import settings as _cfg

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # --- Supabase Storage: signed URL redirect for inline preview ---
    supabase_path = (doc.metadata_json or {}).get("supabase_storage_path", "")
    if supabase_path and _cfg.supabase_enabled:
        try:
            from backend.app.services.supabase_storage_service import supabase_storage
            signed_url = supabase_storage.create_signed_url(
                storage_path=supabase_path,
                category=doc.category,
                expiry_seconds=3600,
            )
            if signed_url:
                return RedirectResponse(url=signed_url, status_code=302)
        except Exception as exc:
            logger.warning(f"[Supabase] Preview signed URL failed, falling back to local: {exc}")

    # --- Fallback: serve from local disk ---
    safe_path = storage_service.resolve_safe_path(current_user.id, doc.stored_filename)
    if not safe_path or not safe_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical file missing on server")

    return FileResponse(
        path=safe_path,
        media_type=doc.mime_type,
        content_disposition_type="inline"
    )

@router.put("/{doc_id}", response_model=DocumentResponse)
def update_document_metadata(
    doc_id: int,
    doc_update: DocumentUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update document metadata (title, category, date, doctor)."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    update_data = doc_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doc, field, value)

    doc.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(doc)

    audit_service.log_event(
        db=db,
        action="DOC_METADATA_UPDATE",
        resource_type="document",
        user_id=current_user.id,
        resource_id=str(doc.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"updated_fields": list(update_data.keys())}
    )

    return doc

@router.delete("/{doc_id}")
def delete_document(
    doc_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete a document record (with cascade to prescriptions and lab tests) and audit trail."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Audit log
    audit_service.log_event(
        db=db,
        action="DOC_DELETE",
        resource_type="document",
        user_id=current_user.id,
        resource_id=str(doc.id),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        details={"title": doc.title, "filename": doc.original_filename}
    )

    # Remove physical file
    safe_path = storage_service.resolve_safe_path(current_user.id, doc.stored_filename)
    if safe_path and safe_path.exists():
        try:
            safe_path.unlink()
        except Exception as e:
            logger.warning(f"Could not delete physical file: {e}")

    db.delete(doc)
    db.commit()

    return {"status": "success", "message": "Document deleted successfully"}

# -------------------------------------------------------------------------------------------------
# Phase 4 — Prescription OCR Model, Structured Extraction & User Review APIs
# -------------------------------------------------------------------------------------------------

@router.get("/models/info")
def get_model_information(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Returns metadata and hardware status for the lightweight prescription OCR pipeline."""
    return prescription_model_service.get_hardware_info()

@router.get("/{doc_id}/extractions", response_model=List[PrescriptionExtractionResponse])
def get_document_extractions(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve all structured extraction records (baseline and VLM) for a prescription document."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    extractions = db.query(PrescriptionExtraction).filter(
        PrescriptionExtraction.document_id == doc.id,
        PrescriptionExtraction.user_id == current_user.id
    ).order_by(desc(PrescriptionExtraction.created_at)).all()

    return extractions

@router.post("/{doc_id}/extract-model", response_model=PrescriptionExtractionResponse)
def run_model_extraction(
    doc_id: int,
    provider: str = "baseline_ocr",
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Run lightweight rule-based structured extraction on a prescription document.
    Only 'baseline_ocr' is supported (CPU-only, no GPU/model required).
    """
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if provider not in {"baseline_ocr"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider '{provider}'. Only 'baseline_ocr' is available."
        )

    image_path = Path(doc.file_path)
    result = prescription_model_service.extract_with_baseline_provider(
        image_path=image_path,
        ocr_raw_text=doc.ocr_raw_text or "",
        doctor_name=doc.doctor_name,
        doc_date=doc.document_date,
        ocr_confidence_score=doc.ocr_confidence_score,
    )

    extraction = PrescriptionExtraction(
        document_id=doc.id,
        user_id=current_user.id,
        provider=result["provider"],
        model_name=result["model_name"],
        model_version=result["model_version"],
        raw_output_text=result["raw_output_text"],
        doctor_name=result["doctor_name"],
        clinic_name=result["clinic_name"],
        patient_name=result["patient_name"],
        prescription_date=result["prescription_date"],
        diagnosis=result["diagnosis"],
        notes=result["notes"],
        medications_json=result["medications"],
        confidence_score=result["confidence_score"],
        confidence_level=result["confidence_level"],
        parsing_status=result["parsing_status"],
        is_user_reviewed=False
    )
    db.add(extraction)
    db.commit()
    db.refresh(extraction)

    if request:
        audit_service.log_event(
            db=db,
            action="PRESCRIPTION_MODEL_EXTRACTION",
            resource_type="prescription_extraction",
            user_id=current_user.id,
            resource_id=str(extraction.id),
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"provider": provider, "doc_id": doc.id}
        )

    return extraction

@router.post("/{doc_id}/corrections/field", response_model=ExtractionCorrectionResponse)
def record_field_correction(
    doc_id: int,
    correction_in: ExtractionCorrectionCreate,
    extraction_id: Optional[int] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Records human-in-the-loop field correction with full provenance tracking."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    corr = ExtractionCorrection(
        extraction_id=extraction_id,
        document_id=doc.id,
        user_id=current_user.id,
        field_name=correction_in.field_name,
        item_index=correction_in.item_index,
        original_value=correction_in.original_value,
        corrected_value=correction_in.corrected_value,
        notes=correction_in.notes
    )
    db.add(corr)

    # If extraction record provided, update its medication json list in-place
    if extraction_id:
        ext = db.query(PrescriptionExtraction).filter(
            PrescriptionExtraction.id == extraction_id,
            PrescriptionExtraction.user_id == current_user.id
        ).first()
        if ext and isinstance(ext.medications_json, list) and correction_in.item_index < len(ext.medications_json):
            meds = list(ext.medications_json)
            med_item = dict(meds[correction_in.item_index])
            med_item[correction_in.field_name] = correction_in.corrected_value
            meds[correction_in.item_index] = med_item
            ext.medications_json = meds
            ext.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(corr)

    if request:
        audit_service.log_event(
            db=db,
            action="PRESCRIPTION_FIELD_CORRECTION",
            resource_type="extraction_correction",
            user_id=current_user.id,
            resource_id=str(corr.id),
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={
                "doc_id": doc.id,
                "field_name": correction_in.field_name,
                "original": correction_in.original_value,
                "corrected": correction_in.corrected_value
            }
        )

    return corr

@router.get("/{doc_id}/corrections/history", response_model=List[ExtractionCorrectionResponse])
def get_correction_history(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve full audit history of user corrections for a prescription document."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    corrections = db.query(ExtractionCorrection).filter(
        ExtractionCorrection.document_id == doc.id,
        ExtractionCorrection.user_id == current_user.id
    ).order_by(desc(ExtractionCorrection.created_at)).all()

    return corrections

@router.post("/{doc_id}/confirm-review", response_model=PrescriptionExtractionResponse)
def confirm_user_review(
    doc_id: int,
    extraction_id: int,
    review_req: UserReviewConfirmRequest,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Marks extraction as user-reviewed and synchronizes medications to active prescription schedule."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    ext = db.query(PrescriptionExtraction).filter(
        PrescriptionExtraction.id == extraction_id,
        PrescriptionExtraction.document_id == doc.id,
        PrescriptionExtraction.user_id == current_user.id
    ).first()
    if not ext:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction record not found")

    ext.is_user_reviewed = True
    ext.user_review_timestamp = datetime.now(timezone.utc)
    if review_req.medications is not None:
        ext.medications_json = review_req.medications

    # Synchronize confirmed medications into active Prescription table for schedule & clinical view
    db.query(Prescription).filter(Prescription.document_id == doc.id).delete()
    for med in ext.medications_json:
        drug_name = med.get("drug_name") or "Medication"
        if drug_name != "Not available in source":
            rx_row = Prescription(
                document_id=doc.id,
                user_id=current_user.id,
                medication_name=drug_name,
                generic_name=med.get("normalized_name") if med.get("normalized_name") != "Not available in source" else None,
                dosage=med.get("dosage") if med.get("dosage") != "Not available in source" else None,
                form="Tablet",
                route="Oral",
                frequency=med.get("frequency") if med.get("frequency") != "Not available in source" else None,
                timing_instructions=med.get("instructions") if med.get("instructions") != "Not available in source" else None,
                duration=med.get("duration") if med.get("duration") != "Not available in source" else None,
                doctor_name=ext.doctor_name if ext.doctor_name != "Not available in source" else doc.doctor_name,
                prescribed_date=ext.prescription_date if ext.prescription_date != "Not available in source" else doc.document_date,
                confidence_score=1.0,
                is_manual_edited=True
            )
            db.add(rx_row)

    db.commit()
    db.refresh(ext)

    if request:
        audit_service.log_event(
            db=db,
            action="PRESCRIPTION_USER_REVIEW_CONFIRMED",
            resource_type="prescription_extraction",
            user_id=current_user.id,
            resource_id=str(ext.id),
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={"doc_id": doc.id, "medications_count": len(ext.medications_json)}
        )

    return ext
