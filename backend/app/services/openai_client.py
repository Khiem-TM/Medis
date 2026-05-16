from __future__ import annotations

import httpx
from openai import AsyncOpenAI

from app.config import settings


def build_async_openai_client() -> AsyncOpenAI | None:
    if not settings.OPENAI_API_KEY:
        return None

    # `openai==1.30.0` is incompatible with `httpx>=0.28` when it builds its
    # own wrapper client, so provide an explicit httpx client here.
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(60.0, connect=10.0),
    )
    return AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        http_client=http_client,
        max_retries=0,
    )
