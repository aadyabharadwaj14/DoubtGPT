from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    ANSWER = "answer"
    CLARIFY = "clarify"
    ABSTAIN = "abstain"


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    include_debug: bool = False


class ChatResponse(BaseModel):
    decision: DecisionType
    confidence: float = Field(..., ge=0.0, le=1.0)
    response: str
    reason: str
    session_id: str
    debug: Optional[dict[str, Any]] = None


class StoredMessage(BaseModel):
    session_id: str
    role: str
    content: str
    decision: Optional[str] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None
    debug: Optional[dict[str, Any]] = None
    created_at: str


class SessionSummary(BaseModel):
    session_id: str
    title: Optional[str] = None
    preview: str
    last_updated: str
    message_count: int


class SessionRenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=80)
