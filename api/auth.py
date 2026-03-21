#!/usr/bin/env python3
"""
Authentication module — Google token verification + JWT issuance.

Dev mode: When JWT_SECRET=dev-secret and GOOGLE_CLIENT_ID is not set,
accepts a mock token for local development without Google OAuth.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Dict

import jwt
from fastapi import HTTPException

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 30

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# Production safety: fail fast if running with default secret + real Google auth
if JWT_SECRET == "dev-secret" and GOOGLE_CLIENT_ID:
    raise RuntimeError(
        "FATAL: JWT_SECRET is 'dev-secret' but GOOGLE_CLIENT_ID is set. "
        "Set a real JWT_SECRET in production — tokens are forgeable with the default."
    )


def verify_google_token(id_token: str) -> Dict[str, str]:
    """
    Verify a Google ID token and return user info.

    Returns: {sub, email, name, picture}

    In dev mode (no GOOGLE_CLIENT_ID set), accepts any token and returns
    mock user data for testing.
    """
    # Dev mode bypass
    if not GOOGLE_CLIENT_ID:
        logger.warning("Dev mode: accepting mock Google token (GOOGLE_CLIENT_ID not set)")
        return {
            "sub": "dev-user",
            "email": "dev@test.com",
            "name": "Dev User",
            "picture": None,
        }

    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        idinfo = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )

        return {
            "sub": idinfo["sub"],
            "email": idinfo.get("email", ""),
            "name": idinfo.get("name", ""),
            "picture": idinfo.get("picture"),
        }
    except ValueError as e:
        logger.warning("Invalid Google token: %s", e)
        raise HTTPException(status_code=401, detail="Invalid Google token") from e
    except Exception as e:
        logger.error("Google token verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Token verification failed") from e


def create_jwt(user_id: str, email: str) -> str:
    """Create an app JWT with 30-day expiry."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": int(time.time()) + (JWT_EXPIRY_DAYS * 86400),
        "iat": int(time.time()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> Dict[str, str]:
    """
    Decode and verify an app JWT.

    Returns: {user_id, email}
    Raises HTTPException(401) on invalid/expired tokens.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"user_id": payload["user_id"], "email": payload["email"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
