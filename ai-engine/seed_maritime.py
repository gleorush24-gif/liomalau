import asyncio
import asyncpg
from pgvector.asyncpg import register_vector
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

NEW_SOURCES = [
    {"code": "UNCLOS_1982", "title": "UN Convention on the Law of the Sea", "body": "UN", "year": 1982, "category": "treaty", "url": "https://www.un.org/depts/los/convention_agreements/texts/unclos/unclos_e.pdf"},
    {"code": "UNSC_RES_1860", "title": "UN Security Council Resolution 1860 - Gaza", "body": "UN Security Council", "year": 2009, "category": "binding", "url": "https://undocs.org/S/RES/1860(2009)"},
    {"code": "HAGUE_REGS_1907", "title": "Hague Regulations Concerning the Laws and Customs of War on Land", "body": "Hague Conference", "year": 1907, "category": "treaty", "url": "https://ihl-databases.icrc.org/hague-regulations"},
]

PRECEDENTS = [
    {
        "source_code": "UNCLOS_1982",
        "article_ref": "Article 87 - Freedom of the High Seas",
        "summary": "The high seas are open to all states. Freedom of navigation cannot be restricted by any state except as permitted by international law.",
        "full_text": "The high seas are open to all States, whether coastal or land-locked. Freedom of the high seas is exercised under the conditions laid down by this Convention and by other rules of international law. It comprises, inter alia, both for coastal and land-locked States: freedom of navigation; freedom of overflight; freedom to lay submarine cables and pipelines.",
        "topic_tags": ["high_seas", "freedom_of_navigation", "blockade", "flotilla", "maritime"],
        "weight": 1.0,
    },
    {
        "source_code": "UNCLOS_1982",
        "article_ref": "Article 110 - Right of Visit",
        "summary": "Warships may board foreign vessels only in cases of piracy, slave trade, unauthorized broadcasting, stateless vessels, or same nationality. Humanitarian vessels cannot be stopped without justification.",
        "full_text": "A warship which encounters on the high seas a foreign ship is not justified in boarding it unless there is reasonable ground for suspecting that the ship is engaged in piracy, the slave trade, unauthorized broadcasting, is without nationality, or is flying a foreign flag or refusing to show its flag. These provisions apply mutatis mutandis to military aircraft.",
        "topic_tags": ["right_of_visit", "boarding", "high_seas", "flotilla", "humanitarian_vessel"],
        "weight": 1.0,
    },
    {
        "source_code": "UNSC_RES_1860",
        "article_ref": "Operative Paragraph 1 - Gaza Ceasefire",
        "summary": "Security Council calls for immediate ceasefire in Gaza and unimpeded provision of humanitarian assistance to civilian population.",
        "full_text": "The Security Council calls for an immediate, durable and fully respected ceasefire, leading to the full withdrawal of Israeli forces from Gaza. It calls for the unimpeded provision and distribution throughout Gaza of humanitarian assistance, including of food, fuel, and medical treatment.",
        "topic_tags": ["gaza", "ceasefire", "humanitarian_access", "blockade", "civilian"],
        "weight": 1.0,
    },
    {
        "source_code": "GC_IV_1949",
        "article_ref": "Article 33 - Collective Punishment (Blockade Context)",
        "summary": "A blockade that punishes the entire civilian population of Gaza for the actions of combatants constitutes prohibited collective punishment.",
        "full_text": "No protected person may be punished for an offence he or she has not personally committed. Collective penalties and likewise all measures of intimidation or of terrorism are prohibited. A blockade that prevents food, medicine and essential supplies from reaching a civilian population constitutes collective punishment when the civilian population as a whole is deprived of necessities.",
        "topic_tags": ["collective_punishment", "blockade", "gaza", "civilian_population", "flotilla"],
        "weight": 1.0,
    },
    {
        "source_code": "HAGUE_REGS_1907",
        "article_ref": "Article 23 - Prohibited Means of Warfare",
        "summary": "It is forbidden to destroy or seize enemy property unless imperatively demanded by war necessity. Seizure of humanitarian aid vessels violates this principle.",
        "full_text": "In addition to the prohibitions provided by special Conventions, it is especially forbidden to destroy or seize the enemy's property, unless such destruction or seizure be imperatively demanded by the necessities of war. The seizure of vessels carrying humanitarian aid when no military necessity exists violates the laws and customs of war.",
        "topic_tags": ["property_seizure", "military_necessity", "humanitarian", "flotilla", "naval"],
        "weight": 0.8,
    },
    {
        "source_code": "ICCPR_1966",
        "article_ref": "Article 9 - Arbitrary Detention of Activists",
        "summary": "Detention and deportation of humanitarian activists intercepted at sea without due process constitutes arbitrary detention under international law.",
        "full_text": "Everyone has the right to liberty and security of person. No one shall be subjected to arbitrary arrest or detention. No one shall be deprived of his liberty except on such grounds and in accordance with such procedure as are established by law. Anyone arrested shall be informed of the reasons for their arrest and shall be promptly brought before a judge.",
        "topic_tags": ["arbitrary_detention", "deportation", "activists", "flotilla", "liberty"],
        "weight": 1.0,
    },
    {
        "source_code": "AP_I_1977",
        "article_ref": "Article 51(2) - Attacks Against Civilians",
        "summary": "Military attacks against civilian vessels carrying humanitarian aid violate the prohibition on attacks against civilians and civilian objects.",
        "full_text": "The civilian population as such, as well as individual civilians, shall not be the object of attack. Acts or threats of violence the primary purpose of which is to spread terror among the civilian population are prohibited. Civilian vessels carrying humanitarian aid are protected objects under international humanitarian law.",
        "topic_tags": ["civilian_vessels", "attacks", "humanitarian", "flotilla", "protection"],
        "weight": 1.0,
    },
    {
        "source_code": "CUSTOMARY_IHL",
        "article_ref": "Rule 55 - Access for Humanitarian Relief",
        "summary": "Parties to a conflict must allow and facilitate rapid and unimpeded passage of humanitarian relief for civilians in need.",
        "full_text": "The parties to the conflict must allow and facilitate rapid and unimpeded passage of humanitarian relief for civilians in need, which is impartial in character and conducted without any adverse distinction, subject to their right of control. This is a norm of customary international law binding on all parties to armed conflict.",
        "topic_tags": ["humanitarian_access", "relief", "blockade", "civilians", "customary_law"],
        "weight": 0.8,
    },
]

async def get_or_create_source(conn, s):
    row = await conn.fetchrow("SELECT id FROM legal_sources WHERE code = $1", s["code"])
    if row:
        return str(row["id"])
    row = await conn.fetchrow(
        "INSERT INTO legal_sources (code, title, body, year, category, url) VALUES ($1,$2,$3,$4,$5,$6) RETURNING id",
        s["code"], s["title"], s["body"], s["year"], s["category"], s["url"]
    )
    print(f"  + Added source: {s['code']}")
    return str(row["id"])

async def embed(text):
    r = await client.embeddings.create(model="text-embedding-3-small", input=text.strip())
    return r.data[0].embedding

async def seed():
    print("Connecting...")
    conn = await asyncpg.connect(dsn=DATABASE_URL)
    await conn.execute("SET search_path TO public")
    await register_vector(conn)

    source_ids = {}
    rows = await conn.fetch("SELECT id, code FROM legal_sources")
    for r in rows:
        source_ids[r["code"]] = str(r["id"])

    for s in NEW_SOURCES:
        source_ids[s["code"]] = await get_or_create_source(conn, s)

    print(f"\nSeeding {len(PRECEDENTS)} maritime/blockade precedents...\n")
    added = 0
    for i, p in enumerate(PRECEDENTS):
        sid = source_ids.get(p["source_code"])
        if not sid:
            print(f"  SKIP: {p['source_code']} not found")
            continue
        existing = await conn.fetchrow(
            "SELECT id FROM precedents WHERE source_id=$1 AND article_ref=$2", sid, p["article_ref"]
        )
        if existing:
            print(f"  [{i+1}] SKIP (exists): {p['article_ref']}")
            continue
        print(f"  [{i+1}/{len(PRECEDENTS)}] Embedding: {p['article_ref']}...")
        embedding = await embed(p["full_text"])
        await conn.execute(
            "INSERT INTO precedents (source_id, article_ref, summary, full_text, topic_tags, weight, embedding) VALUES ($1,$2,$3,$4,$5,$6,$7)",
            sid, p["article_ref"], p["summary"], p["full_text"], p["topic_tags"], p["weight"], embedding
        )
        print(f"      + {p['source_code']} -- {p['summary'][:60]}...")
        added += 1

    await conn.execute("REINDEX INDEX precedents_embedding_idx;")
    total = await conn.fetchval("SELECT COUNT(*) FROM precedents")
    print(f"\nDone! Added {added} precedents. Total: {total}")
    await conn.close()

asyncio.run(seed())
