from __future__ import annotations

from app.config import settings


class GeminiClient:
    def __init__(self, api_key: str, model: str) -> None:
        from google import genai

        self.model = model
        self.client = genai.Client(api_key=api_key)

    async def generate_text(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 800,
        temperature: float = 0.7,
    ) -> str:
        from google.genai import types

        contents: list[types.Content] = []
        for message in messages:
            role = "model" if message["role"] == "assistant" else "user"
            content = message.get("content", "").strip()
            if not content:
                continue
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=content)],
                )
            )

        if not contents:
            raise ValueError("Gemini request has no content")

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                systemInstruction=system_prompt,
                temperature=temperature,
                maxOutputTokens=max_tokens,
            ),
        )

        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Gemini response has no text")
        return text


def build_gemini_client() -> GeminiClient | None:
    if not settings.GEMINI_API_KEY:
        return None
    try:
        return GeminiClient(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)
    except ImportError:
        return None
