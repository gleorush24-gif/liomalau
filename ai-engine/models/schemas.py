# models/schemas.py
#
# LESSON: Pydantic models
# These are Python dataclasses on steroids. When FastAPI receives a JSON
# request, it automatically validates it against these models — wrong type,
# missing field, or bad value = a clear 422 error back to the caller,
# before your code even runs. This replaces mountains of manual validation.

from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime
from enum import Enum


# ── Enums ────────────────────────────────────────────────────
# An Enum is a fixed set of allowed string values.
# Using Enum means a typo like "Supports" or "SUPPORTS" is caught instantly.

class Stance(str, Enum):
    supports      = "supports"
    contradicts   = "contradicts"
    inconclusive  = "inconclusive"

class Category(str, Enum):
    binding     = "binding"
    non_binding = "non_binding"
    treaty      = "treaty"


# ── Inbound requests (what Flutter/Gateway sends us) ─────────

class ArgumentRequest(BaseModel):
    session_id: UUID4
    party_id:   UUID4
    raw_text:   str = Field(..., min_length=10, max_length=5000)
    round:      int = Field(default=1, ge=1)  # ge=1 means "greater or equal to 1"

    # Example shown in the auto-generated /docs page
    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "party_id":   "987fcdeb-51a2-43f7-b123-123456789abc",
                "raw_text":   "The settlements in the West Bank are legal under international law.",
                "round": 1
            }
        }
    }


# ── Outbound responses (what we send back) ───────────────────

class PrecedentMatch(BaseModel):
    """A single legal precedent that matched the argument."""
    id:          UUID4
    source_code: str           # e.g. 'UNSC_RES_2334'
    article_ref: Optional[str] # e.g. 'Paragraph 1'
    summary:     str
    stance:      Stance
    weight:      float         # 1.0 binding, 0.5 advisory
    similarity:  float         # 0.0–1.0 how closely it matched


class VerdictResponse(BaseModel):
    """Full verdict for one argument — what gets sent back to the gateway."""
    argument_id:       UUID4
    parsed_claim:      str              # AI-extracted core claim
    precedents:        list[PrecedentMatch]
    counter_argument:  str              # AI-generated rebuttal text
    score_delta:       float            # points to add/subtract from this party
    overall_stance:    Stance
    confidence:        float
    explanation:       str              # plain-English ruling for the UI
    created_at:        datetime


class SessionCreateRequest(BaseModel):
    title:       str = Field(..., min_length=3, max_length=200)
    party_labels: list[str] = Field(..., min_length=2, max_length=2)
    # e.g. ["Advocate A", "Advocate B"]

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Settlements legality — Round 1",
                "party_labels": ["Position A", "Position B"]
            }
        }
    }


class SessionResponse(BaseModel):
    session_id: UUID4
    title:      str
    parties:    list[dict]   # [{id, label, score}]
    status:     str
    created_at: datetime
