from pydantic import BaseModel
from typing import List
from datetime import datetime


class DocumentAnalysis(BaseModel):
    document_type: str
    summary: str
    topics: List[str]
    people: List[str]
    organizations: List[str]
    dates: List[str]


class DocumentResponse(BaseModel):
    id: int
    filename: str
    document_type: str
    analysis: DocumentAnalysis
    uploaded_at: datetime


class QuestionRequest(BaseModel):
    question: str