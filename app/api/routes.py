from fastapi import APIRouter, UploadFile, File
from typing import List

from app.services.orchestrator import process_claims
from app.models.schemas import ClaimResponse

router = APIRouter()


@router.post("/process-claim", response_model=ClaimResponse)
async def process_claim_endpoint(files: List[UploadFile] = File(...)):
    """
    Accept multiple PDF files and return consolidated claim decision.
    """
    result = await process_claims(files)
    return result
