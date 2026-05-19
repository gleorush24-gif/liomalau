# routers/argument.py
#
# LESSON: FastAPI routers
#
# A "router" groups related endpoints together, like a mini-app.
# main.py mounts routers with a prefix, so this file owns everything
# under /arguments/... without knowing about the rest of the app.
# This keeps each feature in its own file — easy to find, easy to test.

from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.schemas import ArgumentRequest, VerdictResponse, SessionCreateRequest, SessionResponse
from services.rag_retrieval import retrieve_all, store_argument_embedding
from services.counter_arg import adjudicate
from services.embedder import embed_text
from services.database import db_conn
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/arguments", tags=["arguments"])


@router.post("/", response_model=VerdictResponse, status_code=201)
async def submit_argument(
    payload: ArgumentRequest,
    background_tasks: BackgroundTasks,  # FastAPI injects this automatically
):
    """
    Main endpoint — submit an argument, get back a verdict.

    Flow:
      1. Save the raw argument to DB
      2. Embed the argument text
      3. Retrieve matching precedents via vector search
      4. Ask LLM to adjudicate + generate counter-argument
      5. Save verdict to DB
      6. Update party score (in background — doesn't block the response)
    """

    # ── Step 1: insert the argument row ──────────────────────
    async with db_conn() as conn:
        argument_id = uuid.uuid4()

        await conn.execute(
            """
            INSERT INTO arguments (id, session_id, party_id, raw_text, round)
            VALUES ($1, $2, $3, $4, $5)
            """,
            str(argument_id),
            str(payload.session_id),
            str(payload.party_id),
            payload.raw_text,
            payload.round,
        )

    # ── Step 2: embed the argument ────────────────────────────
    # We do this OUTSIDE the db_conn block so the DB connection
    # is freed while we wait for the OpenAI API (which takes ~200ms)
    embedding = await embed_text(payload.raw_text)

    # ── Step 3: retrieve matching precedents ──────────────────
    legal, knowledge = await retrieve_all(payload.raw_text)

    # ── Step 4: adjudicate ────────────────────────────────────
    verdict = await adjudicate(argument_id, payload.raw_text, legal, knowledge)

    # ── Step 5: persist verdict + embedding ───────────────────
    async with db_conn() as conn:
        # Save embedding + parsed claim to the argument row
        await store_argument_embedding(argument_id, embedding, verdict.parsed_claim, conn)

        # Save each precedent verdict
        for p in verdict.precedents:
            await conn.execute(
                """
                INSERT INTO verdicts
                    (argument_id, precedent_id, stance, score_delta, explanation, confidence)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                str(argument_id),
                str(p.id),
                p.stance.value,
                verdict.score_delta / max(len(verdict.precedents), 1),  # split score across precedents
                verdict.explanation,
                verdict.confidence,
            )

        # Save the counter-argument
        await conn.execute(
            """
            INSERT INTO counter_arguments (argument_id, generated_text, source_refs)
            VALUES ($1, $2, $3)
            """,
            str(argument_id),
            verdict.counter_argument,
            [p.source_code for p in verdict.precedents],
        )

    # ── Step 6: update party score in the background ──────────
    # BackgroundTasks runs AFTER the response is sent to the client.
    # The user gets their verdict instantly; score update happens behind the scenes.
    background_tasks.add_task(
        _update_party_score,
        party_id=str(payload.party_id),
        score_delta=verdict.score_delta,
    )

    return verdict


async def _update_party_score(party_id: str, score_delta: float) -> None:
    """Background task — update the running score for a party."""
    async with db_conn() as conn:
        await conn.execute(
            "UPDATE parties SET score = score + $1 WHERE id = $2",
            score_delta,
            party_id,
        )


# ── Session management endpoints ─────────────────────────────

session_router = APIRouter(prefix="/sessions", tags=["sessions"])


@session_router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(payload: SessionCreateRequest):
    """Create a new debate session with two parties."""
    async with db_conn() as conn:
        session_id = uuid.uuid4()

        await conn.execute(
            "INSERT INTO sessions (id, title) VALUES ($1, $2)",
            str(session_id), payload.title,
        )

        parties = []
        for label in payload.party_labels:
            party_id = uuid.uuid4()
            await conn.execute(
                "INSERT INTO parties (id, session_id, label) VALUES ($1, $2, $3)",
                str(party_id), str(session_id), label,
            )
            parties.append({"id": str(party_id), "label": label, "score": 0.0})

    return SessionResponse(
        session_id=session_id,
        title=payload.title,
        parties=parties,
        status="active",
        created_at=datetime.now(timezone.utc),
    )


@session_router.get("/{session_id}/scores")
async def get_scores(session_id: uuid.UUID):
    """Get the current scores for all parties in a session."""
    async with db_conn() as conn:
        rows = await conn.fetch(
            "SELECT id, label, score FROM parties WHERE session_id = $1",
            str(session_id),
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Session not found")

        return [{"id": str(r["id"]), "label": r["label"], "score": float(r["score"])} for r in rows]
