from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime
from enum import Enum


class Stance(str, Enum):
    supports      = "supports"
    contradicts   = "contradicts"
    inconclusive  = "inconclusive"

class Category(str, Enum):
    binding     = "binding"
    non_binding = "non_binding"
    treaty      = "treaty"


class ArgumentRequest(BaseModel):
    session_id: UUID4
    party_id:   UUID4
    raw_text:   str = Field(..., min_length=10, max_length=5000)
    round:      int = Field(default=1, ge=1)

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


class PrecedentMatch(BaseModel):
    id:          UUID4
    source_code: str
    article_ref: Optional[str]
    summary:     str
    stance:      Stance
    weight:      float
    similarity:  float
    url:         Optional[str] = ""


class VerdictResponse(BaseModel):
    argument_id:       UUID4
    parsed_claim:      str
    precedents:        list[PrecedentMatch]
    counter_argument:  str
    score_delta:       float
    overall_stance:    Stance
    confidence:        float
    explanation:       str
    created_at:        datetime


class SessionCreateRequest(BaseModel):
    title:       str = Field(..., min_length=3, max_length=200)
    party_labels: list[str] = Field(..., min_length=2, max_length=2)

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
    parties:    list[dict]
    status:     str
    created_at: datetime
