# routers/exchange.py
#
# Takes a raw pasted social media exchange and:
# 1. Uses GPT-4o to identify speakers and extract their arguments
# 2. Maps speakers to Party A / Party B
# 3. Returns structured turns ready for adjudication

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import AsyncOpenAI
from services.database import db_conn
from services.rag_retrieval import retrieve_precedents
from services.counter_arg import adjudicate
from services.embedder import embed_text
from models.schemas import VerdictResponse
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/exchange", tags=["exchange"])

client = AsyncOpenAI()

# ── Request / Response models ─────────────────────────────────

class ParseExchangeRequest(BaseModel):
    raw_exchange: str       # the pasted social media thread
    session_id: str
    party_a_id: str
    party_b_id: str
    party_a_label: str
    party_b_label: str

class ParsedTurn(BaseModel):
    speaker_label: str      # who said it (as detected)
    party_id: str           # mapped to party_a or party_b
    text: str               # the extracted argument text
    turn_order: int

class ParseExchangeResponse(BaseModel):
    turns: list[ParsedTurn]
    detected_speakers: list[str]
    total_turns: int

class RunExchangeRequest(BaseModel):
    session_id: str
    party_a_id: str
    party_b_id: str
    turns: list[ParsedTurn]

class RunExchangeResponse(BaseModel):
    verdicts: list[VerdictResponse]
    total_processed: int


# ── Parse endpoint ────────────────────────────────────────────

PARSE_SYSTEM_PROMPT = """
You are an argument extraction engine. Given a raw social media exchange
(Twitter/X thread, Facebook argument, Reddit thread, WhatsApp chat, etc.),
extract the individual arguments made by each participant.

Rules:
- Identify the TWO main opposing parties (ignore moderators, bystanders)
- Extract only substantive argumentative claims (skip greetings, reactions, memes)
- Clean up the text: remove @mentions, hashtags, URLs, emoji, retweet prefixes
- Preserve the argument substance faithfully
- Maintain the original turn order
- If more than 2 speakers, group them into 2 sides based on their position

Respond ONLY with valid JSON in this exact format:
{
  "detected_speakers": ["Speaker A name", "Speaker B name"],
  "turns": [
    {
      "speaker": "Speaker A name",
      "side": "A",
      "text": "cleaned argument text",
      "turn_order": 1
    },
    ...
  ]
}
""".strip()


@router.post("/parse", response_model=ParseExchangeResponse)
async def parse_exchange(payload: ParseExchangeRequest):
    """
    Parse a raw social media exchange into structured debate turns.
    Uses GPT-4o to identify speakers and extract clean arguments.
    """
    if len(payload.raw_exchange.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Exchange too short — paste a fuller thread"
        )

    response = await client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PARSE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract arguments from this exchange:\n\n{payload.raw_exchange}"},
        ],
        temperature=0.1,
        max_tokens=2000,
    )

    data = json.loads(response.choices[0].message.content)
    raw_turns = data.get("turns", [])
    detected = data.get("detected_speakers", [])

    if not raw_turns:
        raise HTTPException(
            status_code=422,
            detail="Could not extract any arguments from the exchange"
        )

    # Map detected speakers to party A / party B
    structured_turns = []
    for t in raw_turns:
        side = t.get("side", "A")
        party_id = payload.party_a_id if side == "A" else payload.party_b_id
        speaker = t.get("speaker", payload.party_a_label if side == "A" else payload.party_b_label)

        structured_turns.append(ParsedTurn(
            speaker_label=speaker,
            party_id=party_id,
            text=t.get("text", ""),
            turn_order=t.get("turn_order", len(structured_turns) + 1),
        ))

    return ParseExchangeResponse(
        turns=structured_turns,
        detected_speakers=detected,
        total_turns=len(structured_turns),
    )


# ── Run endpoint ──────────────────────────────────────────────

@router.post("/run", response_model=RunExchangeResponse)
async def run_exchange(payload: RunExchangeRequest):
    """
    Take parsed turns and run each through the full adjudication pipeline.
    Processes turns sequentially and returns all verdicts.
    """
    verdicts = []

    for turn in sorted(payload.turns, key=lambda t: t.turn_order):
        if not turn.text.strip():
            continue

        # Save argument to DB
        argument_id = uuid.uuid4()
        async with db_conn() as conn:
            await conn.execute(
                """
                INSERT INTO arguments (id, session_id, party_id, raw_text, round)
                VALUES ($1, $2, $3, $4, $5)
                """,
                str(argument_id),
                payload.session_id,
                turn.party_id,
                turn.text,
                turn.turn_order,
            )

        # Embed + retrieve precedents
        embedding = await embed_text(turn.text)
        precedents = await retrieve_precedents(turn.text)

        # Adjudicate
        verdict = await adjudicate(argument_id, turn.text, precedents)

        # Persist verdict
        async with db_conn() as conn:
            await conn.execute(
                "UPDATE arguments SET embedding = $1::vector, parsed_claim = $2 WHERE id = $3",
                embedding, verdict.parsed_claim, str(argument_id),
            )
            for p in verdict.precedents:
                await conn.execute(
                    """
                    INSERT INTO verdicts
                        (argument_id, precedent_id, stance, score_delta, explanation, confidence)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    str(argument_id), str(p.id), p.stance.value,
                    verdict.score_delta / max(len(verdict.precedents), 1),
                    verdict.explanation, verdict.confidence,
                )
            await conn.execute(
                "INSERT INTO counter_arguments (argument_id, generated_text, source_refs) VALUES ($1, $2, $3)",
                str(argument_id), verdict.counter_argument,
                [p.source_code for p in verdict.precedents],
            )
            # Update party score
            await conn.execute(
                "UPDATE parties SET score = score + $1 WHERE id = $2",
                verdict.score_delta, turn.party_id,
            )

        verdicts.append(verdict)

    return RunExchangeResponse(
        verdicts=verdicts,
        total_processed=len(verdicts),
    )
