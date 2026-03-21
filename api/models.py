#!/usr/bin/env python3
"""
Pydantic request/response models — AI Prabhupada RAG API
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=1)


class UserInfo(BaseModel):
    id: str
    email: str
    name: str
    photo_url: Optional[str] = None
    text_quota: int
    voice_quota: int


class AuthResponse(BaseModel):
    token: str
    user: UserInfo


class HistoryEntry(BaseModel):
    id: str
    question: str
    answer_text: str
    answer_mode: str
    audio_id: Optional[str] = None
    created_at: str


class HistoryResponse(BaseModel):
    entries: List[HistoryEntry]
    total: int


class WaitlistRequest(BaseModel):
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class QuotaError(BaseModel):
    detail: str
    quota_type: str
    remaining: int
