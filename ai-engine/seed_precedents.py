# seed_precedents.py
#
# Run this ONCE to populate the precedents table with real legal text + embeddings.
# The judge uses these as its knowledge base for ruling on arguments.
#
# Usage (run inside the ai-engine container):
#   docker exec liomalau_ai python seed_precedents.py

import asyncio
import asyncpg
from pgvector.asyncpg import register_vector
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ── Real legal precedents ─────────────────────────────────────────────────────
# Each entry maps to a legal_source by its code.
# full_text = the actual legal language (what the judge cites)
# summary   = plain English (what the UI shows users)
# topic_tags = for filtering later

PRECEDENTS = [

    # ── Geneva Convention IV ──────────────────────────────────
    {
        "source_code": "GC_IV_1949",
        "article_ref": "Article 49, Paragraph 6",
        "summary": "Occupying power prohibited from transferring civilian population into occupied territory",
        "full_text": (
            "The Occupying Power shall not deport or transfer parts of its own civilian population "
            "into the territory it occupies. It shall not deport or transfer parts of the population "
            "of the occupied territory within or outside this territory."
        ),
        "topic_tags": ["occupation", "settlements", "civilian_transfer", "occupied_territory"],
        "weight": 1.0,
    },
    {
        "source_code": "GC_IV_1949",
        "article_ref": "Article 47",
        "summary": "Protected persons in occupied territory cannot be deprived of rights by annexation",
        "full_text": (
            "Protected persons who are in occupied territory shall not be deprived, in any case "
            "or in any manner whatsoever, of the benefits of the present Convention by any change "
            "introduced, as the result of the occupation of a territory, into the institutions or "
            "government of the said territory, nor by any agreement concluded between the authorities "
            "of the occupied territories and the Occupying Power, nor by any annexation by the latter "
            "of the whole or part of the occupied territory."
        ),
        "topic_tags": ["occupation", "annexation", "protected_persons", "rights"],
        "weight": 1.0,
    },
    {
        "source_code": "GC_IV_1949",
        "article_ref": "Article 53",
        "summary": "Occupying power prohibited from destroying property except where absolutely necessary",
        "full_text": (
            "Any destruction by the Occupying Power of real or personal property belonging individually "
            "or collectively to private persons, or to the State, or to other public authorities, or to "
            "social or cooperative organizations, is prohibited, except where such destruction is rendered "
            "absolutely necessary by military operations."
        ),
        "topic_tags": ["property_destruction", "occupation", "civilian_property"],
        "weight": 1.0,
    },

    # ── UN Security Council Resolutions ──────────────────────
    {
        "source_code": "UNSC_RES_242",
        "article_ref": "Paragraph 1(i)",
        "summary": "Requires withdrawal of Israeli armed forces from occupied territories",
        "full_text": (
            "The Security Council, emphasizing the inadmissibility of the acquisition of territory by war "
            "and the need to work for a just and lasting peace in which every State in the area can live "
            "in security, affirms that the fulfillment of Charter principles requires the withdrawal of "
            "Israeli armed forces from territories occupied in the recent conflict."
        ),
        "topic_tags": ["withdrawal", "occupied_territories", "1967_war", "land_for_peace"],
        "weight": 1.0,
    },
    {
        "source_code": "UNSC_RES_2334",
        "article_ref": "Paragraph 1",
        "summary": "Security Council reaffirms Israeli settlements have no legal validity and constitute flagrant violation of international law",
        "full_text": (
            "The Security Council reaffirms that the establishment by Israel of settlements in the Palestinian "
            "territory occupied since 1967, including East Jerusalem, has no legal validity and constitutes "
            "a flagrant violation under international law and a major obstacle to the achievement of the "
            "two-State solution and a just, lasting and comprehensive peace."
        ),
        "topic_tags": ["settlements", "legal_validity", "international_law", "two_state_solution"],
        "weight": 1.0,
    },
    {
        "source_code": "UNSC_RES_2334",
        "article_ref": "Paragraph 2",
        "summary": "Demands Israel immediately cease all settlement activities in occupied Palestinian territory",
        "full_text": (
            "The Security Council demands that Israel immediately and completely cease all settlement "
            "activities in the occupied Palestinian territory, including East Jerusalem, and that it "
            "fully respect all of its legal obligations in this regard."
        ),
        "topic_tags": ["settlements", "cease", "occupied_territory", "east_jerusalem"],
        "weight": 1.0,
    },

    # ── Rome Statute / ICC ────────────────────────────────────
    {
        "source_code": "ICC_ROME_1998",
        "article_ref": "Article 8(2)(b)(viii)",
        "summary": "Transfer of civilian population into occupied territory constitutes a war crime",
        "full_text": (
            "The transfer, directly or indirectly, by the Occupying Power of parts of its own civilian "
            "population into the territory it occupies, or the deportation or transfer of all or parts "
            "of the population of the occupied territory within or outside this territory, constitutes "
            "a war crime."
        ),
        "topic_tags": ["war_crimes", "settlements", "civilian_transfer", "icc", "occupied_territory"],
        "weight": 1.0,
    },
    {
        "source_code": "ICC_ROME_1998",
        "article_ref": "Article 7(1)(d)",
        "summary": "Deportation or forcible transfer of population constitutes a crime against humanity",
        "full_text": (
            "Deportation or forcible transfer of population — meaning forced displacement of the persons "
            "concerned by expulsion or other coercive acts from the area in which they are lawfully present, "
            "without grounds permitted under international law — constitutes a crime against humanity when "
            "committed as part of a widespread or systematic attack directed against any civilian population."
        ),
        "topic_tags": ["crimes_against_humanity", "deportation", "forcible_transfer", "civilian"],
        "weight": 1.0,
    },

    # ── Universal Declaration / ICCPR ─────────────────────────
    {
        "source_code": "UDHR_1948",
        "article_ref": "Article 13",
        "summary": "Everyone has the right to freedom of movement and to choose their residence",
        "full_text": (
            "Everyone has the right to freedom of movement and residence within the borders of each State. "
            "Everyone has the right to leave any country, including his own, and to return to his country."
        ),
        "topic_tags": ["freedom_of_movement", "residence", "right_to_return"],
        "weight": 0.5,
    },
    {
        "source_code": "ICCPR_1966",
        "article_ref": "Article 1 — Self-determination",
        "summary": "All peoples have the right to self-determination and to freely determine their political status",
        "full_text": (
            "All peoples have the right of self-determination. By virtue of that right they freely determine "
            "their political status and freely pursue their economic, social and cultural development. "
            "All peoples may, for their own ends, freely dispose of their natural wealth and resources without "
            "prejudice to any obligations arising out of international economic co-operation, based upon the "
            "principle of mutual benefit, and international law. In no case may a people be deprived of its "
            "own means of subsistence."
        ),
        "topic_tags": ["self_determination", "political_status", "peoples_rights"],
        "weight": 1.0,
    },
    {
        "source_code": "ICCPR_1966",
        "article_ref": "Article 6 — Right to Life",
        "summary": "Every human being has the inherent right to life protected by law",
        "full_text": (
            "Every human being has the inherent right to life. This right shall be protected by law. "
            "No one shall be arbitrarily deprived of his life."
        ),
        "topic_tags": ["right_to_life", "arbitrary_killing", "civilian_protection"],
        "weight": 1.0,
    },
    {
        "source_code": "UNGA_181",
        "article_ref": "Resolution 181 — Partition Plan",
        "summary": "UN General Assembly recommended partition of Palestine into Jewish and Arab states in 1947",
        "full_text": (
            "The General Assembly recommends to the United Kingdom, as the mandatory Power for Palestine, "
            "and to all other Members of the United Nations the adoption and implementation, with regard "
            "to the future government of Palestine, of the Plan of Partition with Economic Union as set "
            "out below. The boundaries of the Arab and Jewish States and the City of Jerusalem shall be "
            "as described in Parts II and III below."
        ),
        "topic_tags": ["partition", "1947", "statehood", "borders", "two_state"],
        "weight": 0.5,
    },
]


async def get_source_id(conn, code: str) -> str | None:
    row = await conn.fetchrow("SELECT id FROM legal_sources WHERE code = $1", code)
    return str(row["id"]) if row else None


async def embed_text(text: str) -> list[float]:
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text.strip().replace("\n", " "),
    )
    return response.data[0].embedding


async def seed():
    print("🔌 Connecting to database...")
    conn = await asyncpg.connect(dsn=DATABASE_URL)
    await register_vector(conn)

    # Clear existing precedents so we can re-run safely
    await conn.execute("DELETE FROM precedents")
    print("🗑️  Cleared existing precedents")

    print(f"📚 Seeding {len(PRECEDENTS)} precedents...\n")

    for i, p in enumerate(PRECEDENTS):
        source_id = await get_source_id(conn, p["source_code"])
        if not source_id:
            print(f"  ⚠️  Source not found: {p['source_code']} — skipping")
            continue

        # Embed the full legal text (this is what gets searched)
        print(f"  [{i+1}/{len(PRECEDENTS)}] Embedding: {p['article_ref']}...")
        embedding = await embed_text(p["full_text"])

        await conn.execute(
            """
            INSERT INTO precedents
                (source_id, article_ref, summary, full_text, topic_tags, weight, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            source_id,
            p["article_ref"],
            p["summary"],
            p["full_text"],
            p["topic_tags"],
            p["weight"],
            embedding,
        )
        print(f"      ✅ {p['source_code']} — {p['summary'][:60]}...")

    count = await conn.fetchval("SELECT COUNT(*) FROM precedents")
    print(f"\n🎉 Done! {count} precedents seeded with embeddings.")
    print("The panel judge is now ready to rule.\n")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
