#!/usr/bin/env python3
"""
FastAPI auth dependencies — extract and verify JWT from requests.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, Request

from api.auth import decode_jwt

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> str:
    """
    FastAPI dependency: extract Bearer token, verify JWT, return user_id.
    Raises HTTPException(401) if token is missing or invalid.
    """
    auth_header = request.headers.get("authorization", "")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header[7:]  # Strip "Bearer "
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_jwt(token)  # Raises HTTPException(401) on failure
    return payload["user_id"]


async def optional_auth(request: Request) -> Optional[str]:
    """
    Same as get_current_user but returns None instead of raising
    when no token is present. For endpoints that work both ways.
    """
    auth_header = request.headers.get("authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    if not token:
        return None

    try:
        payload = decode_jwt(token)
        return payload["user_id"]
    except HTTPException:
        return None
