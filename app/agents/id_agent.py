from app.agents.base import BaseAgent
from app.services.llm_client import llm_json_call


class IDAgent(BaseAgent):
    async def parse(self, text: str) -> dict:
        prompt = (
            "You are an agent that extracts structured data from a patient ID card or insurance card.\n"
            "Return strict JSON only with this schema:\n"
            "{\n"
            "  \"patient_name\": string | null,\n"
            "  \"id_number\": string | null,\n"
            "  \"policy_number\": string | null,\n"
            "  \"insurer_name\": string | null,\n"
            "  \"date_of_birth\": string | null,\n"
            "  \"valid_from\": string | null,\n"
            "  \"valid_to\": string | null\n"
            "}\n"
            "Rules:\n"
            "- Respond with valid JSON only, no explanations.\n"
            "- Use null for missing or unknown values.\n"
            "- Use ISO-like date strings when possible.\n\n"
            f"Document text:\n{text[:4000]}"
        )
        result = await llm_json_call(prompt)

        if result.get("llm_error"):
            return {
                "patient_name": None,
                "id_number": None,
                "policy_number": None,
                "insurer_name": None,
                "date_of_birth": None,
                "valid_from": None,
                "valid_to": None,
                "llm_error": True,
                "error_message": result.get("message"),
            }

        return result
