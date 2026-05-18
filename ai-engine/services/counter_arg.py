# services/counter_arg.py
#
# LESSON: structured LLM output (JSON mode)
#
# By default, LLMs produce free-form text. For lioMalau we need
# structured data: stance, score, explanation. We achieve this by:
#   1. Telling the LLM to respond ONLY in JSON (response_format)
#   2. Defining the exact JSON shape in the system prompt
#   3. Parsing and validating with Pydantic
#
# This is the "structured output" pattern — critical for any
# production AI feature that needs to feed data into a database.

import json
from openai import AsyncOpenAI
from models.schemas import PrecedentMatch, Stance, VerdictResponse
from services.embedder import embed_text
from config import get_settings
from datetime import datetime, timezone
import uuid

settings = get_settings()
_client = AsyncOpenAI(api_key=settings.openai_api_key)


# ── System prompt — the judge's instructions ─────────────────
# This is injected once at the start of every LLM call.
# Good system prompts are specific about FORMAT and CONSTRAINTS.

JUDGE_SYSTEM_PROMPT = """
You are the lioMalau Adjudication Engine — a neutral panel judge.
Your ONLY authority is international law and human rights instruments.
You do not have personal opinions. You rule based solely on the legal
precedents provided to you.

For every argument you receive, you must:
1. Extract the core claim (one sentence, plain language)
2. Assess each provided precedent: does it support or contradict the claim?
3. Generate a factual counter-argument that cites specific legal text
4. Compute a score delta: +2.0 (binding law supports), +1.0 (advisory supports),
   -2.0 (binding law contradicts), -1.0 (advisory contradicts), 0.0 (inconclusive)
5. Write a plain-language ruling explanation (2-3 sentences, cite sources)

You MUST respond with valid JSON only. No preamble, no markdown, no explanation
outside the JSON object. Use this exact structure:

{
  "parsed_claim": "string",
  "overall_stance": "supports" | "contradicts" | "inconclusive",
  "score_delta": float,
  "confidence": float between 0.0 and 1.0,
  "explanation": "string",
  "counter_argument": "string",
  "precedent_stances": {
    "<precedent_id>": "supports" | "contradicts" | "inconclusive"
  }
}
""".strip()


async def adjudicate(
    argument_id: uuid.UUID,
    raw_text: str,
    precedents: list[PrecedentMatch],
) -> VerdictResponse:
    """
    Given an argument and retrieved precedents, ask the LLM to:
    - extract the core claim
    - rule on each precedent's stance
    - generate a counter-argument
    - compute a score delta
    Returns a fully typed VerdictResponse.
    """

    # Build the user message — this is the "stuffing" part of RAG
    # We inject the real legal text so the LLM rules on actual law
    precedent_context = "\n\n".join([
        f"[{p.source_code}] {p.article_ref or ''}\n"
        f"Summary: {p.summary}\n"
        f"Weight: {'BINDING' if p.weight >= 1.0 else 'ADVISORY'}\n"
        f"ID: {p.id}"
        for p in precedents
    ])

    user_message = f"""
ARGUMENT SUBMITTED:
{raw_text}

RELEVANT LEGAL PRECEDENTS (retrieved from panel database):
{precedent_context if precedent_context else "No precedents found — rule as inconclusive."}

Rule on this argument now. Respond in JSON only.
""".strip()

    # Call the LLM — response_format forces JSON output (no markdown fences)
    response = await _client.chat.completions.create(
        model=settings.chat_model,
        response_format={"type": "json_object"},  # JSON mode — critical
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.2,   # low temperature = more deterministic / consistent rulings
        max_tokens=1000,
    )

    # Parse the JSON response
    raw_json = response.choices[0].message.content
    data = json.loads(raw_json)

    # Update each precedent's stance from the LLM's ruling
    stances: dict[str, str] = data.get("precedent_stances", {})
    for p in precedents:
        pid = str(p.id)
        if pid in stances:
            p.stance = Stance(stances[pid])

    return VerdictResponse(
        argument_id=argument_id,
        parsed_claim=data["parsed_claim"],
        precedents=precedents,
        counter_argument=data["counter_argument"],
        score_delta=float(data["score_delta"]),
        overall_stance=Stance(data["overall_stance"]),
        confidence=float(data["confidence"]),
        explanation=data["explanation"],
        created_at=datetime.now(timezone.utc),
    )
