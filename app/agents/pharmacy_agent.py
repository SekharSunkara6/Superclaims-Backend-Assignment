from app.agents.base import BaseAgent
from app.services.llm_client import llm_json_call


class PharmacyAgent(BaseAgent):
    async def parse(self, text: str) -> dict:
        prompt = (
            "You are an agent that extracts structured data from a pharmacy bill or medicine invoice.\n"
            "Return strict JSON only with this schema:\n"
            "{\n"
            "  \"patient_name\": string | null,\n"
            "  \"pharmacy_name\": string | null,\n"
            "  \"bill_date\": string | null,\n"
            "  \"total_amount\": number | null,\n"
            "  \"currency\": string | null,\n"
            "  \"items\": [\n"
            "    {\n"
            "      \"drug_name\": string | null,\n"
            "      \"dosage\": string | null,\n"
            "      \"quantity\": number | null,\n"
            "      \"unit_price\": number | null,\n"
            "      \"amount\": number | null\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "Rules:\n"
            "- Respond with valid JSON only, no explanations.\n"
            "- Use null for missing or unknown values.\n"
            "- If this is not a pharmacy bill, still follow the schema.\n\n"
            f"Document text:\n{text[:4000]}"
        )
        result = await llm_json_call(prompt)

        if result.get("llm_error"):
            return {
                "patient_name": None,
                "pharmacy_name": None,
                "bill_date": None,
                "total_amount": None,
                "currency": None,
                "items": [],
                "llm_error": True,
                "error_message": result.get("message"),
            }

        result.setdefault("items", [])
        return result
