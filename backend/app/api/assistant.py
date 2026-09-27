from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.services.hybrid_rag_service import hybrid_rag_service
from backend.app.services.gemini_service import gemini_service
from backend.app.services.audit_service import audit_service
from backend.app.schemas.assistant import ChatQueryRequest, ChatQueryResponse, KnowledgeSourceInfo

router = APIRouter()

@router.post("/chat", response_model=ChatQueryResponse)
def chat_with_assistant(
    chat_req: ChatQueryRequest,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Executes Hybrid RAG retrieval across:
    - User Structured Records (Lab Tests, Prescriptions, Documents)
    - User Document Semantic Chunks
    - General Medical Knowledge (Medical QA Dataset)

    Enforces Evidence Priority (USER RECORDS > GENERAL KNOWLEDGE) and cross-user security isolation.
    """
    if not chat_req.query or not chat_req.query.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query text cannot be empty.")

    target_lang = chat_req.language or current_user.language_preference or "en"

    response = hybrid_rag_service.process_chat_query(
        db=db,
        user_id=current_user.id,
        query=chat_req.query,
        language=target_lang
    )

    if request:
        audit_service.log_event(
            db=db,
            action="ASSISTANT_HYBRID_RAG_QUERY",
            resource_type="assistant_chat",
            user_id=current_user.id,
            resource_id=f"query_len_{len(chat_req.query)}",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            details={
                "query_type": response.query_type,
                "evidence_found": response.evidence_found,
                "priority_applied": response.evidence_priority_applied,
                "citations_count": len(response.citations),
                "language": target_lang
            }
        )

    return response

@router.post("/analyze-image")
async def analyze_medical_image(
    image: UploadFile = File(...),
    query: str = Form(default="Analyze this medical image and extract all information."),
    language: str = Form(default="en"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Accepts an uploaded medical image or document photo and uses Gemini Vision
    to extract text and analyze health information from it.
    Returns a friendly AI response with the extracted content.
    """
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/tiff", "application/pdf"}
    content_type = image.content_type or "image/jpeg"
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{content_type}' not supported. Please upload an image (JPG, PNG, WEBP) or PDF."
        )

    # Read image bytes
    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image too large. Max 10MB.")

    # Use Gemini Vision to analyze
    if not gemini_service.is_configured:
        return {
            "answer": "📸 I received your image! However, image analysis requires the Gemini API key to be configured. Please ask your administrator to set up the API key.\n\nIn the meantime, you can upload this document using the Medical Records upload feature for text extraction.",
            "query_type": "IMAGE_ANALYSIS",
            "evidence_found": False,
            "evidence_status": "INSUFFICIENT",
            "evidence_priority_applied": False,
            "citations": [],
            "sources": [],
            "structured_cards": [],
            "follow_up_suggestions": ["Upload document to records", "Ask about my health"]
        }

    # Determine mime type
    mime_map = {
        "image/jpeg": "image/jpeg",
        "image/png": "image/png",
        "image/webp": "image/webp",
        "image/gif": "image/gif",
        "image/tiff": "image/jpeg",  # convert to jpeg-compatible
        "application/pdf": "application/pdf"
    }
    mime_type = mime_map.get(content_type, "image/jpeg")

    vision_prompt = f"""The user asked: "{query}"

Please analyze this medical document/image and:
1. Extract ALL visible text accurately (preserve numbers, values, units)
2. Identify key health information: lab values, medications, diagnoses, dates, doctor info
3. Summarize the findings in a friendly, easy-to-understand way
4. Highlight any values that are outside normal ranges
5. Suggest relevant follow-up questions the user might want to ask

Language preference: {language}"""

    result = gemini_service.analyze_image_with_vision(
        image_bytes=image_bytes,
        mime_type=mime_type,
        prompt=vision_prompt
    )

    if not result:
        answer = "📸 I received your image, but I had trouble analyzing it right now. Please try again, or upload the document through Medical Records for processing."
        evidence_found = False
    else:
        answer = f"📋 **Image Analysis Complete!**\n\n{result}"
        evidence_found = True

    return {
        "answer": answer,
        "query_type": "IMAGE_ANALYSIS",
        "evidence_found": evidence_found,
        "evidence_status": "SUPPORTED" if evidence_found else "INSUFFICIENT",
        "evidence_priority_applied": False,
        "citations": [],
        "sources": [],
        "structured_cards": [],
        "follow_up_suggestions": [
            "What are my latest lab values? 🩺",
            "What does this medication do?",
            "Upload this to my records"
        ]
    }

@router.get("/knowledge-sources", response_model=List[KnowledgeSourceInfo])
def get_knowledge_sources_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Returns metadata and licensing information for active RAG knowledge collections."""
    return hybrid_rag_service.get_knowledge_sources_info(db=db, user_id=current_user.id)
