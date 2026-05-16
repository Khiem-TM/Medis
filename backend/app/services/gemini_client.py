from __future__ import annotations

import httpx

from app.config import settings


class GeminiClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate_text(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 800,
        temperature: float = 0.7,
    ) -> str:
        contents = []
        for message in messages:
            role = "model" if message["role"] == "assistant" else "user"
            contents.append({
                "role": role,
                "parts": [{"text": message["content"]}],
            })

        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        url = f"{self.base_url}/models/{self.model}:generateContent"

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            response = await client.post(
                url,
                headers={
                    "x-goog-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini response has no candidates")

        parts = candidates[0].get("content", {}).get("parts") or []
        text = "\n".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise RuntimeError("Gemini response has no text")
        return text


def build_gemini_client() -> GeminiClient | None:
    if not settings.GEMINI_API_KEY:
        return None
    return GeminiClient(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)
