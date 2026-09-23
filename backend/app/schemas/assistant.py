from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatQueryRequest(BaseModel):
    query: str = Field(..., description="User question or clinical inquiry")
    language: Optional[str] = Field("en", description="Target language: 'en', 'ta', 'tanglish'")

class CitationItem(BaseModel):
    source_type: str = Field(..., description="'USER_STRUCTURED_RECORD' | 'USER_DOCUMENT_CHUNK' | 'GENERAL_MEDICAL_KNOWLEDGE'")
    source_name: str = Field(..., description="Document title or dataset source name")
    record_id: Optional[str] = None
    document_id: Optional[int] = None
    page_number: Optional[int] = None
    text_snippet: str = Field(..., description="Ground-truth textual evidence excerpt")
    relevance_score: Optional[float] = None
    license: Optional[str] = None

class ChatQueryResponse(BaseModel):
    answer: str
    query_type: str # 'PATIENT_FACTUAL' | 'DOCUMENT_SEARCH' | 'GENERAL_MEDICAL_KNOWLEDGE' | 'HYBRID' | 'PATIENT_CHANGES' | 'PATIENT_MEDICATIONS'
    evidence_found: bool
    evidence_priority_applied: str
    evidence_status: str = "SUPPORTED" # 'SUPPORTED' | 'PARTIAL' | 'INSUFFICIENT'
    citations: List[CitationItem] = []
    sources: List[CitationItem] = []
    language: str = "en"
    structured_cards: Optional[List[Dict[str, Any]]] = []
    follow_up_suggestions: Optional[List[str]] = []

class KnowledgeSourceInfo(BaseModel):
    collection_name: str
    total_records: int
    is_user_isolated: bool
    description: str
    dataset_name: Optional[str] = None
    dataset_version: Optional[str] = None
    license: Optional[str] = None
    source_url: Optional[str] = None
