"""Model data Pydantic untuk REST API dan Exporter."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ServiceStatusEnum(str, Enum):
    """Status kesiapan browser engine."""

    INITIALIZING = "initializing"
    READY = "ready"
    HUMAN_INTERVENTION_REQUIRED = "human_intervention_required"
    ERROR = "error"


class ChatRequest(BaseModel):
    """Request payload untuk API /chat."""

    prompt: str = Field(
        ..., min_length=1, description="Pesan prompt yang dikirim ke DeepSeek"
    )


class ChatResponse(BaseModel):
    """Response payload dari API /chat."""

    status: str = Field(..., description="Status eksekusi chat")
    session_id: str
    prompt: str
    response: str
    human_intervention_required: bool = False
    message: str | None = None


class RawInteractionData(BaseModel):
    """Dataset mentah untuk keperluan analisis data."""

    session_id: str
    sequence_index: int
    prompt: str
    raw_response: str
    prompt_length: int
    response_length: int
    created_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )