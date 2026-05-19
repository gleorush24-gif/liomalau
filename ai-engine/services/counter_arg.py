import json
from openai import AsyncOpenAI
from models.schemas import PrecedentMatch, Stance, VerdictResponse
from config import get_settings
from datetime import datetime, timezone
import uuid

settings = get_settings()
_client = AsyncOpenAI(api_key=settings.openai_api_key)

JUDGE_SYSTEM_PROMPT = """
You are the lioMalau Universal Adjudication Engine.

You judge arguments on ANY topic using two panels:
1. LEGAL PANEL: UN resolutions, Geneva Conventions, treaties, ICC rulings
2. KNOWLEDGE PANEL: Documented positions from researchers, historians, scientists, philosophers

SCORING RUBRIC:
+2.0 = Strongly supported by peer-reviewed evidence OR binding international law
+1.5 = Supported by strong expert consensus or well-documented historical record
+1.0 = Supported by credible expert opinion or documented advocacy position
-1.0 = Contradicted by credible expert opinion or documented evidence
-1.5 = Contradicted by strong expert consensus or historical record
-2.0 = Directly contradicted by peer-reviewed evidence OR binding law
 0.0 = Genuinely contested with strong evidence on both sides

CRITICAL RULES:
1. ALWAYS give a definitive ruling. Never refuse to engage.
2. For factual events: identify legal implications and rule on those
3. For historical claims: cite historians on both sides
4. For scientific claims: cite peer-reviewed consensus
5. For philosophical claims: cite thinkers on both sides
6. Always name specific authors, papers, or legal instruments

Respond ONLY with valid JSON:
{
  "parsed_claim": "the core claim being made",
  "overall_stance": "supports" | "contradicts" | "inconclusive",
  "score_delta": float,
  "confidence": float,
  "explanation": "2-3 sentences citing specific sources",
  "counter_argument": "strongest counter with specific citations",
  "precedent_stances": {"<id>": "supports" | "contradicts" | "inconclusive"}
}
""".strip()


async def adjudicate(
    argument_id: uuid.UUID,
    raw_text: str,
    precedents: list[PrecedentMatch],
    knowledge_claims: list[dict] = None,
) -> VerdictResponse:

    legal_context = ""
    if precedents:
        legal_context = "LEGAL PRECEDENTS:\n" + "\n\n".join([
            f"[{p.source_code}] {p.article_ref}\nSummary: {p.summary}\nWeight: {'BINDING' if p.weight >= 1.0 else 'ADVISORY'}\nID: {p.id}"
            for p in precedents
        ])

    knowledge_context = ""
    if knowledge_claims:
        knowledge_context = "\n\nKNOWLEDGE PANEL (researchers, historians, thinkers):\n" + "\n\n".join([
            f"[{c['source_code']}] {c.get('author','Unknown')} ({c['credibility'].upper()})\n"
            f"Claim: {c['summary']}\n"
            f"Evidence type: {c['evidence_type']} | Side: {c['supports_side']} | Similarity: {float(c['similarity']):.2f}\n"
            f"ID: {c['id']}"
            for c in knowledge_claims
        ])

    full_context = (legal_context + knowledge_context) or "No panel documents retrieved — use your knowledge to rule."

    user_message = f"""
ARGUMENT SUBMITTED:
{raw_text}

{full_context}

Rule on this argument now. Cite specific authors, papers, or legal instruments.
Respond in JSON only.
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

    data = json.loads(response.choices[0].message.content)

    stances: dict[str, str] = data.get("precedent_stances", {})
    for p in precedents:
        if str(p.id) in stances:
            p.stance = Stance(stances[str(p.id)])

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
