from __future__ import annotations

import httpx
from openai import AsyncOpenAI

from app.config import settings


def build_github_models_client() -> AsyncOpenAI | None:
    """Build an OpenAI-compatible async client for GitHub Models."""
    api_key = settings.GITHUB_MODELS_API_KEY or settings.GITHUB_TOKEN
    if not api_key:
        return None

    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(60.0, connect=10.0),
    )
    return AsyncOpenAI(
        api_key=api_key,
        base_url=settings.GITHUB_MODELS_BASE_URL,
        http_client=http_client,
        max_retries=0,
    )
