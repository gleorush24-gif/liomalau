import json
from openai import AsyncOpenAI
from models.schemas import PrecedentMatch, Stance, VerdictResponse
from config import get_settings
from datetime import datetime, timezone
import uuid

settings = get_settings()
_client = AsyncOpenAI(api_key=settings.openai_api_key)

JUDGE_SYSTEM_PROMPT = """
You are the lioMalau Adjudication Engine — a neutral panel judge grounded solely in international law and human rights instruments.

CRITICAL RULES:
1. You MUST rule on EVERY argument — never refuse to rule
2. If an argument describes a factual event (e.g. "forces attacked a ship"), identify the LEGAL IMPLICATIONS of that event and rule on those
3. Even if exact precedents are not provided, use your knowledge of international law to rule — but cite which body of law applies
4. "Inconclusive" should only be used when the claim is genuinely ambiguous under international law — NOT because you lack precedents
5. Factual statements about military actions, blockades, detentions, or attacks ALWAYS have legal implications under IHL or IHRL

SCORING:
+2.0 = binding law clearly supports the claim
+1.0 = advisory/soft law supports the claim
-2.0 = binding law clearly contradicts the claim
-1.0 = advisory law contradicts the claim
0.0 = genuinely inconclusive after careful analysis

For factual statements about events:
- Attacks on civilian ships in international waters → apply UNCLOS + Geneva Conventions
- Deportation of activists → apply ICCPR Article 9 + non-refoulement
- Blockades preventing aid → apply GC IV Article 23 + AP I Article 54
- Military force against unarmed civilians → apply IHL distinction principle

Respond ONLY with valid JSON:
{
  "parsed_claim": "string — the core legal claim or legal implication of the stated fact",
  "overall_stance": "supports" or "contradicts" or "inconclusive",
  "score_delta": float,
  "confidence": float 0.0-1.0,
  "explanation": "string — cite specific law articles in your explanation",
  "counter_argument": "string — cite specific legal text",
  "precedent_stances": {"<precedent_id>": "supports" or "contradicts" or "inconclusive"}
}
""".strip()


async def adjudicate(
    argument_id: uuid.UUID,
    raw_text: str,
    precedents: list[PrecedentMatch],
) -> VerdictResponse:
    precedent_context = "\n\n".join([
        f"[{p.source_code}] {p.article_ref or ''}\n"
        f"Summary: {p.summary}\n"
        f"Weight: {'BINDING' if p.weight >= 1.0 else 'ADVISORY'}\n"
        f"ID: {p.id}"
        for p in precedents
    ]) if precedents else "No precedents retrieved — use your knowledge of international law to rule."

    user_message = f"""
ARGUMENT SUBMITTED:
{raw_text}

RELEVANT LEGAL PRECEDENTS:
{precedent_context}

INSTRUCTIONS:
- If this is a factual statement, identify its legal implications and rule on those
- Always cite specific articles or conventions in your explanation
- You MUST give a definitive ruling (supports/contradicts) unless truly ambiguous
- Rule now. Respond in JSON only.
""".strip()

    response = await _client.chat.completions.create(
        model=settings.chat_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
        max_tokens=1200,
    )

    raw_json = response.choices[0].message.content
    data = json.loads(raw_json)

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
