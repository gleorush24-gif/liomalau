# services/rag_retrieval.py
#
# LESSON: RAG (Retrieval-Augmented Generation)
#
# Problem: an LLM only knows what was in its training data.
#          It can't cite *specific* UN resolutions reliably.
# Solution: BEFORE asking the LLM to rule on an argument, we:
#   1. Embed the argument → search our panel DB for relevant precedents
#   2. STUFF those precedents into the LLM prompt as context
#   3. The LLM now rules based on real legal text, not memory
#
# This is RAG. The "retrieval" step grounds the AI in facts we control.

from services.database import db_conn
from services.embedder import embed_text
from models.schemas import PrecedentMatch, Stance
from config import get_settings
import uuid

settings = get_settings()


async def retrieve_precedents(argument_text: str) -> list[PrecedentMatch]:
    """
    Find the top-k most legally relevant precedents for a given argument.
    Uses cosine similarity between the argument embedding and stored precedent embeddings.
    """

    # Step 1: embed the incoming argument
    query_vector = await embed_text(argument_text)

    async with db_conn() as conn:
        # Step 2: vector similarity search in Postgres
        #
        # The <=> operator (cosine distance) is provided by pgvector.
        # Lower distance = more similar. We ORDER BY distance ASC, take top-k.
        #
        # We also join legal_sources so we get the source code (e.g. 'UNSC_RES_242')
        # alongside the precedent for citation display in the UI.
        rows = await conn.fetch(
            """
            SELECT
                p.id,
                p.article_ref,
                p.summary,
                p.weight,
                ls.code  AS source_code,
                1 - (p.embedding <=> $1::vector)  AS similarity
            FROM precedents p
            JOIN legal_sources ls ON p.source_id = ls.id
            WHERE p.embedding IS NOT NULL
            ORDER BY p.embedding <=> $1::vector
            LIMIT $2
            """,
            query_vector,
            settings.top_k_precedents,
        )

    if not rows:
        return []

    # Step 3: convert raw DB rows into typed PrecedentMatch objects
    # We don't know the stance yet — that's determined by the LLM in counter_arg.py
    # We set it to inconclusive here and the LLM fills it in later
    return [
        PrecedentMatch(
            id=row["id"],
            source_code=row["source_code"],
            article_ref=row["article_ref"],
            summary=row["summary"],
            weight=float(row["weight"]),
            similarity=float(row["similarity"]),
            stance=Stance.inconclusive,   # placeholder — LLM sets this
        )
        for row in rows
    ]


async def store_argument_embedding(
    argument_id: uuid.UUID,
    embedding: list[float],
    parsed_claim: str,
    conn,   # pass in an existing connection to reuse a transaction
) -> None:
    """Save the embedding and parsed claim back to the arguments table."""
    await conn.execute(
        """
        UPDATE arguments
        SET embedding = $1::vector, parsed_claim = $2
        WHERE id = $3
        """,
        embedding,
        parsed_claim,
        str(argument_id),
    )
