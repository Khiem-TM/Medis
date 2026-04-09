from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.security import decode_token
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# ── Path → action mapping ──────────────────────────────────────────────────

_RULES: list[tuple[str, str, str]] = [
    # (method, path_pattern, action)
    ("POST",   r"^/api/v1/auth/login$",                    "LOGIN"),
    ("POST",   r"^/api/v1/auth/logout$",                   "LOGOUT"),
    ("POST",   r"^/api/v1/auth/register$",                 "REGISTER"),
    ("PUT",    r"^/api/v1/users/me$",                      "PROFILE_UPDATE"),
    ("PUT",    r"^/api/v1/users/me/password$",             "PASSWORD_CHANGE"),
    ("POST",   r"^/api/v1/users/me/prescriptions$",        "PRESCRIPTION_CREATE"),
    ("PUT",    r"^/api/v1/users/me/prescriptions/\d+$",    "PRESCRIPTION_UPDATE"),
    ("DELETE", r"^/api/v1/users/me/prescriptions",         "PRESCRIPTION_DELETE"),
    ("POST",   r"^/api/v1/users/me/health-profiles$",      "HEALTH_PROFILE_CREATE"),
    ("PUT",    r"^/api/v1/users/me/health-profiles/\d+$",  "HEALTH_PROFILE_UPDATE"),
    ("DELETE", r"^/api/v1/users/me/health-profiles",       "HEALTH_PROFILE_DELETE"),
    ("POST",   r"^/api/v1/interactions/check$",            "INTERACTION_CHECK"),
    ("GET",    r"^/api/v1/drugs",                          "DRUG_SEARCH"),
    ("POST",   r"^/api/v1/chatbot/message$",               "CHATBOT_MESSAGE"),
]

_ENTITY_RE = re.compile(r"/(\w+)/(\d+)$")


def _resolve_action(method: str, path: str, query_string: str) -> Optional[str]:
    for rule_method, pattern, action in _RULES:
        if rule_method != method:
            continue
        if re.match(pattern, path):
            # DRUG_SEARCH only if ?search= query param present
            if action == "DRUG_SEARCH" and "search=" not in query_string:
                continue
            return action
    return None


def _extract_entity(path: str) -> tuple[Optional[str], Optional[str]]:
    m = _ENTITY_RE.search(path)
    if not m:
        return None, None
    segment, eid = m.group(1), m.group(2)
    entity_map = {
        "prescriptions": "prescription",
        "health-profiles": "health_profile",
        "users": "user",
        "drugs": "drug",
        "interactions": "interaction",
    }
    return entity_map.get(segment, segment), eid


class ActivityLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Only log successful responses
        if response.status_code >= 400:
            return response

        path = request.url.path
        method = request.method
        query_string = str(request.url.query)

        action = _resolve_action(method, path, query_string)
        if not action:
            return response

        # Extract user_id from Bearer token (best-effort — no raise)
        user_id: Optional[int] = None
        try:
            auth_header = request.headers.get("authorization", "")
            token = auth_header.replace("Bearer ", "").strip()
            if token:
                payload = decode_token(token)
                if payload:
                    user_id = int(payload["sub"])
        except Exception:
            pass

        # Build detail / entity
        detail: Optional[dict] = None
        if action == "DRUG_SEARCH":
            detail = {"query": request.query_params.get("search")}

        entity_type, entity_id = _extract_entity(path)

        # Fire-and-forget log — never block the response
        asyncio.ensure_future(
            self._do_log(
                action=action,
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                detail=detail,
                ip=request.client.host if request.client else None,
                ua=request.headers.get("user-agent", ""),
            )
        )

        return response

    @staticmethod
    async def _do_log(
        action: str,
        user_id: Optional[int],
        entity_type: Optional[str],
        entity_id: Optional[str],
        detail: Optional[dict],
        ip: Optional[str],
        ua: Optional[str],
    ) -> None:
        try:
            from app.models.log import ActivityLog

            async with AsyncSessionLocal() as db:
                entry = ActivityLog(
                    action=action,
                    user_id=user_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    detail=detail,
                    ip_address=ip,
                    user_agent=ua,
                )
                db.add(entry)
                await db.commit()
        except Exception as exc:
            logger.error("ActivityLogMiddleware._do_log failed: %s", exc)
