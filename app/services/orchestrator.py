from typing import List

from fastapi import UploadFile

from app.models.schemas import (
    ClaimResponse,
    DocumentData,
    ValidationResult,
    ClaimDecision,
)
from app.services.validation import run_validation
from app.utils.pdf_utils import pdf_to_text
from app.services.llm_client import llm_json_call
from app.agents.bill_agent import BillAgent
from app.agents.discharge_agent import DischargeAgent
from app.agents.id_agent import IDAgent
from app.agents.pharmacy_agent import PharmacyAgent


async def classify_document(text: str) -> str:
    """
    LLM-based classifier for document type.
    """
    prompt = (
        "You are a classifier for a health insurance claim system.\n"
        "You MUST choose exactly ONE of these types for the ENTIRE document:\n"
        "- bill\n"
        "- discharge_summary\n"
        "- id_card\n"
        "- pharmacy_bill\n"
        "- claim_form\n"
        "- other\n\n"
        "Return JSON ONLY with this exact schema:\n"
        "{ \"doc_type\": \"bill | discharge_summary | id_card | pharmacy_bill | claim_form | other\" }\n\n"
        "Classification rules:\n"
        "- If it looks like a hospital invoice, hospital bill, medical charges, admission/discharge dates, "
        "  or itemized hospital charges → classify as \"bill\".\n"
        "- If it is a narrative clinical document describing admission, discharge, diagnoses, procedures, "
        "  and recommendations → classify as \"discharge_summary\".\n"
        "- If it is an insurance / health card with insurer name, policy number, member id → classify as \"id_card\".\n"
        "- If it is a bill from a pharmacy / medicines invoice → classify as \"pharmacy_bill\".\n"
        "- If it is a generic insurance form with many fields to fill, signatures, etc. → classify as \"claim_form\".\n"
        "- Use \"other\" ONLY if it clearly does NOT match any of the above types.\n\n"
        "Document text:\n"
        f"{text[:3000]}\n"
    )

    result = await llm_json_call(prompt)

    if result.get("llm_error"):
        return "other"

    doc_type = result.get("doc_type", "").strip().lower()

    allowed = {
        "bill",
        "discharge_summary",
        "id_card",
        "pharmacy_bill",
        "claim_form",
        "other",
    }
    if doc_type not in allowed:
        return "other"

    return doc_type


def get_agent_for_doc_type(doc_type: str):
    """
    Map doc_type to specific agent class.
    """
    if doc_type == "bill":
        return BillAgent()
    if doc_type == "discharge_summary":
        return DischargeAgent()
    if doc_type == "id_card":
        return IDAgent()
    if doc_type == "pharmacy_bill":
        return PharmacyAgent()
    # claim_form or other → no dedicated agent yet
    return None


async def process_claims(files: List[UploadFile]) -> ClaimResponse:
    documents: list[DocumentData] = []

    for f in files:
        content = await f.read()
        text = await pdf_to_text(content)

        filename = (f.filename or "").lower()

        # Filename-based hint for demo, fallback to LLM
        if "bill" in filename:
            doc_type = "bill"
        elif "discharge" in filename:
            doc_type = "discharge_summary"
        elif "idcard" in filename or "id_card" in filename or "insurance" in filename:
            doc_type = "id_card"
        else:
            doc_type = await classify_document(text)

        agent = get_agent_for_doc_type(doc_type)
        structured_data = await agent.parse(text) if agent else {}

        documents.append(
            DocumentData(
                filename=f.filename,
                doc_type=doc_type,
                raw_text=text,
                structured_data=structured_data,
            )
        )

    v = run_validation(documents)

    validation = ValidationResult(
        missing_documents=v["missing_documents"],
        discrepancies=v["discrepancies"],
    )
    decision = ClaimDecision(
        status=v["status"],
        reason=v["reason"],
    )

    return ClaimResponse(
        documents=documents,
        validation=validation,
        claim_decision=decision,
    )

