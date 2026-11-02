"""
Pydantic schemas for the RAG pipeline request/response models.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, field_validator


VALID_SERVICES = {"aadhaar", "pan", "passport"}


class ChatRequest(BaseModel):
    message: str
    service: Optional[str] = None  # "aadhaar" | "pan" | "passport" | None (all)

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message cannot be empty")
        if len(v) > 1000:
            raise ValueError("message exceeds maximum length of 1000 characters")
        return v

    @field_validator("service")
    @classmethod
    def service_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().lower()
        if v not in VALID_SERVICES:
            raise ValueError(f"service must be one of {VALID_SERVICES} or null")
        return v


class Citation(BaseModel):
    id: str
    title: str
    service: str
    official_url: str
    filename: str
    page_range: str
    chunk_index: int


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    suggestions: list[str]
    source: str  # "chroma_rag" | "keyword_fallback"
