from typing import List
from pydantic import BaseModel


class DocumentData(BaseModel):
    filename: str
    doc_type: str
    raw_text: str
    structured_data: dict


class ValidationResult(BaseModel):
    missing_documents: List[str]
    discrepancies: List[str]


class ClaimDecision(BaseModel):
    status: str  # "approved" | "rejected" | "manual_review"
    reason: str


class ClaimResponse(BaseModel):
    documents: List[DocumentData]
    validation: ValidationResult
    claim_decision: ClaimDecision
