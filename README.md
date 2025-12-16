# SuperClaims – Backend Developer Assignment

## Overview

SuperClaims is a FastAPI-based backend that processes multiple medical claim PDFs using LLM-powered agents. It ingests several PDFs in a single request, classifies each document, extracts structured fields with dedicated agents, validates the overall claim, and returns a consolidated JSON response with a final claim decision.

A live deployment is available here:

- Root: https://superclaims-backend-assignment.onrender.com/  
- API docs (Swagger): https://superclaims-backend-assignment.onrender.com/docs  

---

## Getting Started

### 1. Clone the repository

```
git clone https://github.com/SekharSunkara6/superclaims-backend-assignment.git
cd superclaims-backend-assignment
```

### 2. Create virtual environment & install dependencies

```
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini   # or any chat/completions-capable model
```

(There is also a `.env.example` with placeholder keys; do not commit your real `.env`.)

### 4. Run the app locally

```
uvicorn app.main:app --reload
```

Local URLs:

- Root: http://127.0.0.1:8000  
- Docs: http://127.0.0.1:8000/docs  

From `/docs`, use `POST /process-claim` → **Try it out** to upload multiple PDFs and inspect the JSON response.

---

## Architecture

### High-level flow

1. Client uploads multiple PDFs to `POST /process-claim`.  
2. Orchestrator:
   - Extracts text from each PDF.
   - Classifies document type using an LLM (with a small filename hint for demo stability).
   - Routes the text to a document-specific agent (`BillAgent`, `DischargeAgent`, `IDAgent`, `PharmacyAgent`).  
3. Agents:
   - Build strict JSON-only prompts.
   - Call the shared LLM client to extract structured fields.
   - Return a typed `structured_data` object, or a fallback with `llm_error: true` if the LLM fails.  
4. Validation:
   - Detects missing required documents (bill, discharge summary, ID card).
   - Runs basic cross-checks (name/date/amount consistency).
   - Produces a final decision: `approved`, `rejected`, or `manual_review`.  
5. API response:
   - Returns all `documents` with raw and structured data.
   - Returns `validation` and `claim_decision`.

### Modules and structure

- `app/main.py`  
  - FastAPI app entrypoint and root endpoint.  
  - Mounts the API router and serves a simple landing page with a button linking to `/docs`.

- `app/api/routes.py`  
  - Defines `POST /process-claim` (async).  
  - Accepts multiple `UploadFile` objects (`files`).  
  - Delegates to `process_claims` in the orchestrator service.

- `app/services/orchestrator.py`  
  - `process_claims(files)` – central orchestration:
    - Reads each file and converts PDF bytes to text via `pdf_to_text`.
    - Calls `classify_document(text)` (LLM-based) plus a simple filename hint (e.g., “Bill.pdf” → `bill`) for deterministic behavior on the sample PDFs.
    - Selects the appropriate agent with `get_agent_for_doc_type`.
    - Runs the agent (if any) to produce `structured_data`.
  - Collects `DocumentData` objects and passes them to `run_validation(documents)`.

- `app/services/llm_client.py`  
  - `llm_json_call(prompt: str) -> dict`:
    - Calls the OpenAI Chat Completions API.  
    - Sends a system message: “You are a strict JSON API. Always respond with valid JSON only, no extra text.”  
    - Parses JSON from the model’s `message.content`.  
    - On HTTP/connection errors (e.g., 401/429), returns:
      ```
      {
        "llm_error": true,
        "status_code": 429,
        "message": "..."
      }
      ```
    - This ensures the rest of the system never crashes due to LLM issues.

- `app/agents/`  
  - `bill_agent.py` (`BillAgent`) – extracts fields from hospital bills:
    - `patient_name`, `hospital_name`, `bill_date`, `total_amount`, `currency`, `line_items`, `llm_error`.  
  - `discharge_agent.py` (`DischargeAgent`) – extracts from discharge summaries:
    - `patient_name`, `hospital_name`, `admission_date`, `discharge_date`, `primary_diagnosis`, `secondary_diagnoses`, `procedures`, `attending_physician`, `llm_error`.  
  - `id_agent.py` (`IDAgent`) – extracts from insurance / health ID cards:
    - `patient_name`, `id_number`, `policy_number`, `insurer_name`, `date_of_birth`, `valid_from`, `valid_to`, `llm_error`.  
  - `pharmacy_agent.py` (`PharmacyAgent`, optional) – extracts pharmacy bill fields.

  Each agent:
  - Builds a schema-specific JSON-only prompt.
  - Calls `llm_json_call`.
  - If `result["llm_error"]` is true, returns a fallback JSON with `null` or empty values plus `llm_error` and `error_message`.

- `app/services/validation.py`  
  - `run_validation(documents)`:
    - Computes which required doc types are missing among `["bill", "discharge_summary", "id_card"]`.
    - Performs simple cross-checks:
      - Name consistency across bill, discharge, and ID (when `patient_name` is present).  
      - Bill date within admission–discharge range (string comparison).  
      - `total_amount` positive when present.  
    - Produces:
      ```
      {
        "missing_documents": [...],
        "discrepancies": [...],
        "status": "approved" | "manual_review" | "rejected",
        "reason": "..."
      }
      ```

- `app/models/schemas.py`  
  - Pydantic models:
    - `DocumentData` – per-document info (filename, doc_type, raw_text, structured_data).  
    - `ValidationResult` – `missing_documents`, `discrepancies`.  
    - `ClaimDecision` – `status`, `reason`.  
    - `ClaimResponse` – top-level response wrapper.

- `app/utils/pdf_utils.py`  
  - `pdf_to_text(bytes)` – converts PDF bytes into text for use by the LLM.

- `app/core/config.py`  
  - Loads configuration from environment variables (OpenAI API key, model, etc.).

---

## Live Deployment (Render)

The app is deployed as a Python Web Service on Render.

- Root: https://superclaims-backend-assignment.onrender.com/  
- Docs: https://superclaims-backend-assignment.onrender.com/docs  

**Render settings (summary):**

- Runtime: **Python**  
- Build command: `pip install -r requirements.txt`  
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`  
- Environment variables (in Render dashboard):
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`

---

## AI Tools and LLM Usage

- **Provider**: OpenAI Chat Completions API.  
- **Use-cases in this service**:
  - LLM-based **classification** of documents.  
  - LLM-based **extraction** via specialized agents.  
  - Validation is implemented in Python; LLM could be added later for more complex reasoning.

### Error handling and rate limits (429)

- When the OpenAI API returns HTTP 429 (“Too Many Requests”) or similar:
  - `llm_json_call` returns `{"llm_error": true, "status_code": 429, "message": "..."}`.  
  - Each agent detects this and returns its schema with:
    - All data fields as `null` or empty arrays.  
    - `llm_error: true` and an `error_message`.  
- The API still returns:
  - A full `documents` list.  
  - `validation` and `claim_decision`.  

Given current limits on the key used for this project, 429 can be frequent, so `structured_data` may contain mostly nulls plus `llm_error`, but the architecture is ready to use real values when the model responds successfully.

---

## Sample Prompts

### 1. Classification prompt

**System message:**

> You are a strict JSON API. Always respond with valid JSON only, no extra text.

**User message (simplified):**

```
You are a classifier for a health insurance claim system.
You MUST choose exactly ONE of these types for the ENTIRE document:
- bill
- discharge_summary
- id_card
- pharmacy_bill
- claim_form
- other

Return JSON ONLY with this exact schema:
{ "doc_type": "bill | discharge_summary | id_card | pharmacy_bill | claim_form | other" }

Classification rules:
- Hospital invoice or itemized hospital charges → "bill".
- Narrative clinical document with admission, discharge, diagnoses, procedures → "discharge_summary".
- Insurance / health card with insurer name, policy number, member id → "id_card".
- Pharmacy or medicines invoice → "pharmacy_bill".
- Generic insurance form with many fields to fill and signatures → "claim_form".
- Use "other" only if it clearly does not match any of the above.

Document text:
<first 3000 characters of the PDF>
```

### 2. Bill extraction (BillAgent)

```
You are a JSON API that extracts structured fields from a hospital bill.

Return STRICT JSON with this schema:
{
  "patient_name": string | null,
  "hospital_name": string | null,
  "bill_date": string | null,
  "total_amount": number | null,
  "currency": string | null,
  "line_items": [
    {
      "description": string | null,
      "amount": number | null
    }
  ],
  "llm_error": false
}

Rules:
- Use null for missing or unknown values.
- Do not add extra keys.
- bill_date should be the billing date.
- total_amount is the final amount due, if available.

Document text:
<bill text here>
```

### 3. Discharge summary extraction (DischargeAgent)

```
You are a JSON API that extracts structured fields from a hospital discharge summary.

Return STRICT JSON with this schema:
{
  "patient_name": string | null,
  "hospital_name": string | null,
  "admission_date": string | null,
  "discharge_date": string | null,
  "primary_diagnosis": string | null,
  "secondary_diagnoses": [string],
  "procedures": [string],
  "attending_physician": string | null,
  "llm_error": false
}

Use null for missing values and do not add extra keys.

Document text:
<discharge summary text here>
```

(An analogous schema and prompt are used for `IDAgent` and `PharmacyAgent`.)

---

## Example Request & Response

### Request

`POST /process-claim` with 4 uploaded files:

- `Bill.pdf`  
- `DischargeSummary.pdf`  
- `IdCard.pdf`  
- `Sunkara PurnaSekhar_Beagle HQ.pdf` (resume – treated as `other`)  

### Example response (truncated)

```
{
  "documents": [
    {
      "filename": "DischargeSummary.pdf",
      "doc_type": "discharge_summary",
      "raw_text": "DISCHARGE SUMMARY\n=================\nHospital: Metro Health Care Center\nDate: 2024-12-15\n...",
      "structured_data": {
        "patient_name": null,
        "hospital_name": null,
        "admission_date": null,
        "discharge_date": null,
        "primary_diagnosis": null,
        "secondary_diagnoses": [],
        "procedures": [],
        "attending_physician": null,
        "llm_error": true,
        "error_message": "Client error '429 Too Many Requests' for url 'https://api.openai.com/v1/chat/completions'..."
      }
    },
    {
      "filename": "IdCard.pdf",
      "doc_type": "id_card",
      "raw_text": "HEALTH INSURANCE CARD\n====================\nInsurer: United Health Insurance Ltd.\n...",
      "structured_data": {
        "patient_name": null,
        "id_number": null,
        "policy_number": null,
        "insurer_name": null,
        "date_of_birth": null,
        "valid_from": null,
        "valid_to": null,
        "llm_error": true,
        "error_message": "Client error '429 Too Many Requests' for url 'https://api.openai.com/v1/chat/completions'..."
      }
    },
    {
      "filename": "Sunkara PurnaSekhar_Beagle HQ.pdf",
      "doc_type": "other",
      "raw_text": "+91 9121975699 ⋄ Visakhapatnam, IND\n...",
      "structured_data": {}
    },
    {
      "filename": "Bill.pdf",
      "doc_type": "bill",
      "raw_text": "CARE HOSPITAL BILL\n================\nInvoice Number: INV-2024-789456\nDate: 2024-12-10\n...",
      "structured_data": {
        "patient_name": null,
        "hospital_name": null,
        "bill_date": null,
        "total_amount": null,
        "currency": null,
        "line_items": [],
        "llm_error": true,
        "error_message": "Client error '429 Too Many Requests' for url 'https://api.openai.com/v1/chat/completions'..."
      }
    }
  ],
  "validation": {
    "missing_documents": [],
    "discrepancies": []
  },
  "claim_decision": {
    "status": "approved",
    "reason": "All required documents present and basic checks passed."
  }
}
```

In a higher-quota environment, the same architecture would produce non-null extracted fields.

---

## Dockerfile (Bonus)

A simple Dockerfile is provided:

```
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Standard commands (when Docker can access Docker Hub):

```
docker build -t superclaims-backend .
docker run --env-file .env -p 8000:8000 superclaims-backend
```

On the current development machine, Docker builds fail due to network timeouts accessing Docker Hub, so the container is not tested locally. The Dockerfile follows a standard FastAPI + Uvicorn pattern and should work in a normal Docker environment.

---

## Limitations & Future Improvements

- **OpenAI rate limits (429)**  
  - Current key frequently hits rate/usage limits, resulting in `llm_error: true` and null fields.  
  - Production deployment would use better quota, retries, or multiple keys.

- **Date handling**  
  - Dates are compared as strings; could be improved by parsing into `datetime` objects with strict formats.

- **Business logic**  
  - Validation currently includes required-doc checks and a few cross-checks (name/date/amount).  
  - Additional checks like policy coverage rules, currency normalization, and fraud patterns can be layered on.

- **Persistence and caching**  
  - The demo is fully in-memory.  
  - Real-world systems would use Postgres for storage and Redis for caching LLM responses or intermediate results.

---

## Loom Walkthrough (Bonus)

(Replace with your actual Loom URL.)

> Loom walkthrough: https://www.loom.com/share/YOUR-VIDEO-ID

The video should briefly show:

- Project structure and key modules (orchestrator, agents, validation, LLM client).  
- Running the service locally or on Render.  
- Using `/docs` to upload PDFs.  
- Walking through the JSON response and explaining classification, extraction, validation, and how `llm_error` is handled.
