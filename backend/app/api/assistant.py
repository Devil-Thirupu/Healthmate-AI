from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Any, List

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.api.deps import get_current_user, get_client_ip
from backend.app.services.hybrid_rag_service import hybrid_rag_service
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

@router.get("/knowledge-sources", response_model=List[KnowledgeSourceInfo])
def get_knowledge_sources_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Returns metadata and licensing information for active RAG knowledge collections."""
    return hybrid_rag_service.get_knowledge_sources_info(db=db, user_id=current_user.id)
