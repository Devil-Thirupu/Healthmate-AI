from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Citation(BaseModel):
    document_id: int
    document_title: str
    document_date: Optional[str] = None
    page_number: int
    text_snippet: str
    confidence_score: float
    relevance_score: float

class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=2)
    language: Optional[str] = "en" # "en", "ta", "tanglish"
    document_ids: Optional[List[int]] = None # Filter by specific documents if provided
    top_k: Optional[int] = 5

class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    language: str
    has_sufficient_evidence: bool
    disclaimer: str
    citations: List[Citation] = []
    suggested_followups: List[str] = []
