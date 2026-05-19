import uuid
from services.database import db_conn
from services.embedder import embed_text
from models.schemas import PrecedentMatch, Stance
from config import get_settings
import asyncio
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


async def retrieve_precedents(argument_text: str) -> list[PrecedentMatch]:
    query_vector = await embed_text(argument_text)
    async with db_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT p.id, p.article_ref, p.summary, p.weight,
                   ls.code AS source_code, ls.url AS source_url,
                   1 - (p.embedding <=> $1::vector) AS similarity
            FROM precedents p
            JOIN legal_sources ls ON p.source_id = ls.id
            WHERE p.embedding IS NOT NULL
            AND 1 - (p.embedding <=> $1::vector) > 0.25
            ORDER BY p.embedding <=> $1::vector
            LIMIT $2
            """,
            query_vector, settings.top_k_precedents,
        )
    return [
        PrecedentMatch(
            id=row["id"], source_code=row["source_code"],
            article_ref=row["article_ref"] or "", summary=row["summary"],
            weight=float(row["weight"]), similarity=float(row["similarity"]),
            stance=Stance.inconclusive,
            url=row["source_url"] or "",
        )
        for row in rows
    ]


async def retrieve_knowledge_claims(argument_text: str) -> list[dict]:
    try:
        query_vector = await embed_text(argument_text)
        async with db_conn() as conn:
            rows = await conn.fetch(
                """
                SELECT kc.id, kc.claim_ref, kc.summary, kc.full_text,
                       kc.supports_side, kc.evidence_type, kc.weight,
                       ks.code AS source_code, ks.author, ks.title,
                       ks.credibility, ks.domain, ks.url AS source_url,
                       1 - (kc.embedding <=> $1::vector) AS similarity
                FROM knowledge_claims kc
                JOIN knowledge_sources ks ON kc.source_id = ks.id
                WHERE kc.embedding IS NOT NULL
                ORDER BY kc.embedding <=> $1::vector
                LIMIT $2
                """,
                query_vector, settings.top_k_precedents,
            )
        return [dict(row) for row in rows]
    except Exception as e:
        logger.warning(f"Knowledge claims retrieval failed: {e}")
        return []


async def retrieve_all(argument_text: str) -> tuple[list[PrecedentMatch], list[dict]]:
    try:
        legal, knowledge = await asyncio.gather(
            retrieve_precedents(argument_text),
            retrieve_knowledge_claims(argument_text),
        )
        return legal, knowledge
    except Exception as e:
        logger.error(f"retrieve_all failed: {e}")
        try:
            legal = await retrieve_precedents(argument_text)
            return legal, []
        except Exception as e2:
            logger.error(f"retrieve_precedents also failed: {e2}")
            return [], []


async def store_argument_embedding(argument_id, embedding, parsed_claim, conn):
    await conn.execute(
        "UPDATE arguments SET embedding=$1::vector, parsed_claim=$2 WHERE id=$3",
        embedding, parsed_claim, str(argument_id),
    )
