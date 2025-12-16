from app.agents.base import BaseAgent
from app.services.llm_client import llm_json_call


class DischargeAgent(BaseAgent):
    async def parse(self, text: str) -> dict:
        prompt = (
            "You are an agent that extracts structured data from a hospital discharge summary.\n"
            "Return strict JSON only with this schema:\n"
            "{\n"
            "  \"patient_name\": string | null,\n"
            "  \"hospital_name\": string | null,\n"
            "  \"admission_date\": string | null,\n"
            "  \"discharge_date\": string | null,\n"
            "  \"primary_diagnosis\": string | null,\n"
            "  \"secondary_diagnoses\": [string],\n"
            "  \"procedures\": [string],\n"
            "  \"attending_physician\": string | null\n"
            "}\n"
            "Rules:\n"
            "- Respond with valid JSON only, no explanations.\n"
            "- Use null for missing or unknown values.\n"
            "- Use ISO-like date strings when possible (e.g., 2024-01-31).\n\n"
            f"Document text:\n{text[:4000]}"
        )
        result = await llm_json_call(prompt)

        if result.get("llm_error"):
            return {
                "patient_name": None,
                "hospital_name": None,
                "admission_date": None,
                "discharge_date": None,
                "primary_diagnosis": None,
                "secondary_diagnoses": [],
                "procedures": [],
                "attending_physician": None,
                "llm_error": True,
                "error_message": result.get("message"),
            }

        # Ensure list fields exist
        result.setdefault("secondary_diagnoses", [])
        result.setdefault("procedures", [])
        return result
