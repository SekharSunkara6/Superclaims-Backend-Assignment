from app.agents.base import BaseAgent
from app.services.llm_client import llm_json_call


class BillAgent(BaseAgent):
    async def parse(self, text: str) -> dict:
        prompt = (
            "You are an agent that extracts structured data from a medical bill.\n"
            "Return strict JSON only with this schema:\n"
            "{\n"
            "  \"patient_name\": string | null,\n"
            "  \"hospital_name\": string | null,\n"
            "  \"bill_date\": string | null,\n"
            "  \"total_amount\": number | null,\n"
            "  \"currency\": string | null,\n"
            "  \"line_items\": [\n"
            "    {\n"
            "      \"description\": string | null,\n"
            "      \"quantity\": number | null,\n"
            "      \"unit_price\": number | null,\n"
            "      \"amount\": number | null\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "Rules:\n"
            "- Respond with valid JSON only, no explanations.\n"
            "- Use null for missing or unknown values.\n"
            "- If the document is not a bill, still follow the schema.\n\n"
            f"Document text:\n{text[:4000]}"
        )
        result = await llm_json_call(prompt)

        if result.get("llm_error"):
            # Fallback minimal structure to keep pipeline stable
            return {
                "patient_name": None,
                "hospital_name": None,
                "bill_date": None,
                "total_amount": None,
                "currency": None,
                "line_items": [],
                "llm_error": True,
                "error_message": result.get("message"),
            }

        return result
