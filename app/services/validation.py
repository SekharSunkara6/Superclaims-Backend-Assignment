from typing import List, Dict, Optional
from app.models.schemas import DocumentData

REQUIRED_TYPES = ["bill", "discharge_summary", "id_card"]


def _find_by_type(documents: List[DocumentData], doc_type: str) -> Optional[DocumentData]:
    for d in documents:
        if d.doc_type == doc_type:
            return d
    return None


def run_validation(documents: List[DocumentData]) -> Dict:
    present_types = {doc.doc_type for doc in documents}
    missing = [t for t in REQUIRED_TYPES if t not in present_types]

    discrepancies: List[str] = []

    bill_doc = _find_by_type(documents, "bill")
    discharge_doc = _find_by_type(documents, "discharge_summary")
    id_doc = _find_by_type(documents, "id_card")

    bill_data = bill_doc.structured_data if bill_doc else {}
    discharge_data = discharge_doc.structured_data if discharge_doc else {}
    id_data = id_doc.structured_data if id_doc else {}

    # 1) Patient name consistency (bill vs discharge vs ID)
    names = []

    for src, data in [
        ("bill", bill_data),
        ("discharge_summary", discharge_data),
        ("id_card", id_data),
    ]:
        name = (data.get("patient_name") or "").strip().lower()
        if name:
            names.append((src, name))

    if len(names) >= 2:
        base_src, base_name = names[0]
        for src, name in names[1:]:
            if name != base_name:
                discrepancies.append(
                    f"Patient name mismatch between {base_src} and {src} "
                    f"('{base_name}' vs '{name}')."
                )

    # 2) Bill date should be within admission–discharge stay
    bill_date = bill_data.get("bill_date")
    admission_date = discharge_data.get("admission_date")
    discharge_date_val = discharge_data.get("discharge_date")

    if bill_date and admission_date and discharge_date_val:
        # String comparison only; in README note this is a simple check
        if not (admission_date <= bill_date <= discharge_date_val):
            discrepancies.append(
                f"Bill date {bill_date} is outside admission period "
                f"{admission_date}–{discharge_date_val}."
            )

    # 3) Simple amount sanity check
    total_amount = bill_data.get("total_amount")
    if isinstance(total_amount, (int, float)) and total_amount <= 0:
        discrepancies.append("Bill total_amount must be positive.")

    # Decide status
    if missing:
        status = "manual_review"
        reason = f"Missing required documents: {', '.join(missing)}"
    elif discrepancies:
        status = "manual_review"
        reason = f"Found {len(discrepancies)} potential inconsistencies."
    else:
        status = "approved"
        reason = "All required documents present and basic checks passed."

    return {
        "missing_documents": missing,
        "discrepancies": discrepancies,
        "status": status,
        "reason": reason,
    }
