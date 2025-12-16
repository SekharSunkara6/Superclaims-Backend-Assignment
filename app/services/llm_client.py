import json
import httpx

from httpx import HTTPStatusError
from app.core.config import settings


OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


async def llm_json_call(prompt: str) -> dict:
    """
    Call OpenAI Chat Completion API and enforce JSON-only output.
    On errors (e.g., 401/429), return a JSON error object instead of raising.
    """
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": settings.OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a strict JSON API. Always respond with valid JSON only, no extra text.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.1,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(OPENAI_API_URL, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"parse_error": True, "raw": content}

    except HTTPStatusError as e:
        # Graceful degradation on rate limit / auth errors
        status = e.response.status_code
        return {
            "llm_error": True,
            "status_code": status,
            "message": str(e),
        }
    except Exception as e:
        return {
            "llm_error": True,
            "status_code": None,
            "message": str(e),
        }
