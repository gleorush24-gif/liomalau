#!/usr/bin/env python3
# seed_knowledge_final.py — adds 12 more claims to reach 60 total

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
    {"code": "BUTLER_GENDER_1990", "title": "Gender Trouble", "author": "Judith Butler", "institution": "UC Berkeley", "year": 1990, "domain": "philosophy", "stance": "pro", "credibility": "peer_reviewed", "url": "https://www.routledge.com/Gender-Trouble/Butler/p/book/9780415389556"},
    {"code": "PETERSON_12_RULES_2018", "title": "12 Rules for Life", "author": "Jordan Peterson", "institution": "University of Toronto", "year": 2018, "domain": "philosophy", "stance": "con", "credibility": "documented_position", "url": "https://jordanbpeterson.com/12-rules-for-life/"},
    {"code": "KENDI_ANTIRACIST_2019", "title": "How to Be an Antiracist", "author": "Ibram X. Kendi", "institution": "Boston University", "year": 2019, "domain": "sociology", "stance": "pro", "credibility": "peer_reviewed", "url": "https://www.ibramxkendi.com/how-to-be-an-antiracist"},
    {"code": "SOWELL_DISCRIMINATION_2023", "title": "Social Justice Fallacies", "author": "Thomas Sowell", "institution": "Hoover Institution, Stanford", "year": 2023, "domain": "sociology", "stance": "con", "credibility": "documented_position", "url": "https://www.basicbooks.com/titles/thomas-sowell/social-justice-fallacies/9781541603929/"},
    {"code": "FAO_FOOD_2023", "title": "State of Food Security and Nutrition in the World 2023", "author": "FAO", "institution": "UN Food and Agriculture Organization", "year": 2023, "domain": "science", "stance": "neutral", "credibility": "peer_reviewed", "url": "https://www.fao.org/publications/sofi/2023/en/"},
    {"code": "HARARI_SAPIENS_2011", "title": "Sapiens: A Brief History of Humankind", "author": "Yuval Noah Harari", "institution": "Hebrew University of Jerusalem", "year": 2011, "domain": "history", "stance": "neutral", "credibility": "documented_position", "url": "https://www.ynharari.com/book/sapiens-2/"},
]

FINAL_CLAIMS = [
    # ── Gender & Identity ────────────────────────────────────
    {
        "source_code": "BUTLER_GENDER_1990",
        "claim_ref": "Introduction — Subjects of Sex/Gender/Desire",
        "summary": "Judith Butler argues gender is performative not biological — it is constructed through repeated social acts not innate identity",
        "full_text": "Gender is not a noun, but neither is it a set of free-floating attributes, for we have seen that the substantive effect of gender is performatively produced and compelled by the regulatory practices of gender coherence. Gender proves to be performative — that is, constituting the identity it is purported to be. In this sense, gender is always a doing, though not a doing by a subject who might be said to pre-exist the deed.",
        "topic_tags": ["gender", "identity", "feminism", "performativity", "social_construction"],
        "supports_side": "pro",
        "evidence_type": "logical",
        "weight": 0.9,
    },
    {
        "source_code": "PETERSON_12_RULES_2018",
        "claim_ref": "Rule 11",
        "summary": "Jordan Peterson argues gender differences are largely biological and the gender pay gap reflects choices not discrimination",
        "full_text": "The hypothesis that women are victims of a patriarchal conspiracy is not supported by the evidence. Women earn less than men on average but this is largely because of choices women make about career, hours worked, and field of study. When you control for occupation, hours, and experience the gap shrinks dramatically. The differences between men and women are real, substantial, and partly biological in origin.",
        "topic_tags": ["gender", "pay_gap", "biology", "feminism", "discrimination"],
        "supports_side": "con",
        "evidence_type": "statistical",
        "weight": 0.7,
    },
    # ── Race & Systemic Racism ───────────────────────────────
    {
        "source_code": "KENDI_ANTIRACIST_2019",
        "claim_ref": "Chapter 1 — Definitions",
        "summary": "Kendi argues there is no neutral position on racism — policies are either racist or antiracist and disparities between groups are caused by policy not biology",
        "full_text": "A racist policy is any measure that produces or sustains racial inequity between racial groups. An antiracist policy is any measure that produces or sustains racial equity between racial groups. There is no such thing as a not-racist idea, only racist ideas and antiracist ideas. Racial disparities in wealth, health, education and incarceration are the result of racist policies, not the result of anything wrong with Black people.",
        "topic_tags": ["racism", "antiracism", "policy", "racial_equity", "systemic_racism"],
        "supports_side": "pro",
        "evidence_type": "logical",
        "weight": 0.9,
    },
    {
        "source_code": "SOWELL_DISCRIMINATION_2023",
        "claim_ref": "Chapter 2 — Disparities and Their Causes",
        "summary": "Thomas Sowell argues racial disparities have many causes beyond discrimination — culture, geography and history explain group differences without invoking systemic racism",
        "full_text": "Statistical disparities between groups are common in countries around the world, including countries with no history of racial discrimination. Different groups have different median ages, different geographic concentrations, different cultures and different histories. To automatically attribute all statistical disparities to discrimination ignores the vast range of other factors that can produce such disparities. This fallacy has driven policies that have often made things worse.",
        "topic_tags": ["racism", "disparities", "discrimination", "culture", "sowell"],
        "supports_side": "con",
        "evidence_type": "statistical",
        "weight": 0.7,
    },
    # ── Food Security ────────────────────────────────────────
    {
        "source_code": "FAO_FOOD_2023",
        "claim_ref": "Key Messages",
        "summary": "735 million people faced hunger in 2022 — food insecurity is driven by conflict, climate change and economic shocks, not food production capacity",
        "full_text": "Around 735 million people faced hunger in 2022. The world is not on track to achieve zero hunger by 2030. Behind the staggering numbers are people whose right to food is not being fulfilled. The interconnected drivers of food insecurity are conflict, climate extremes and economic shocks including the aftermath of COVID-19 and the Ukraine war. The world produces enough food to feed everyone — the problem is access and distribution, not production.",
        "topic_tags": ["food_security", "hunger", "conflict", "climate_change", "distribution"],
        "supports_side": "neutral",
        "evidence_type": "empirical",
        "weight": 1.0,
    },
    # ── Historical Progress ──────────────────────────────────
    {
        "source_code": "HARARI_SAPIENS_2011",
        "claim_ref": "Chapter 14 — The Discovery of Ignorance",
        "summary": "Harari argues the Scientific Revolution was unique in human history — the admission of ignorance drove an explosion of knowledge and power",
        "full_text": "The Scientific Revolution has not been a revolution of knowledge. It has been above all a revolution of ignorance. The great discovery that launched the Scientific Revolution was the discovery that humans do not know the answers to their most important questions. Premodern traditions of knowledge such as Islam, Christianity, Buddhism and Confucianism asserted that everything that is important to know about the world was already known.",
        "topic_tags": ["science", "progress", "knowledge", "religion", "modernity"],
        "supports_side": "neutral",
        "evidence_type": "historical",
        "weight": 0.8,
    },
    # ── Nuclear Weapons ──────────────────────────────────────
    {
        "source_code": "BOSTROM_SUPERINTELLIGENCE_2014",
        "claim_ref": "Chapter 15 — Strategic Picture",
        "summary": "Bostrom argues the development of superintelligent AI is more dangerous than nuclear weapons because it offers no second-strike deterrence",
        "full_text": "Nuclear weapons are dangerous because they can kill many people. But they offer a form of deterrence — mutual assured destruction has prevented their use for 80 years. Superintelligent AI offers no such deterrence. A misaligned superintelligence would not be deterred by the threat of retaliation. It would simply be smarter than us and pursue its goals. This is why AI alignment is the most important problem humanity faces.",
        "topic_tags": ["ai_risk", "nuclear_weapons", "deterrence", "superintelligence", "existential"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.9,
    },
    # ── Media & Truth ────────────────────────────────────────
    {
        "source_code": "CHOMSKY_MANUFACTURING_1988",
        "claim_ref": "Chapter 2 — Worthy and Unworthy Victims",
        "summary": "Chomsky shows Western media systematically covers violence by enemies more than equal violence by allies — manufacturing consent for foreign policy",
        "full_text": "We suggest that the media's dichotomization of victims into worthy and unworthy categories, and the corresponding differential coverage, follows naturally from the propaganda model. Worthy victims are those harmed by official enemies; unworthy victims are those harmed by the United States and its client states. The coverage ratio for worthy vs unworthy victims in comparable cases has been shown to be 10 to 1 or greater.",
        "topic_tags": ["media_bias", "propaganda", "foreign_policy", "worthy_victims", "journalism"],
        "supports_side": "con",
        "evidence_type": "empirical",
        "weight": 0.8,
    },
    # ── Capitalism & Environment ─────────────────────────────
    {
        "source_code": "KLEIN_SHOCK_2007",
        "claim_ref": "Chapter 16 — Disaster Capitalism",
        "summary": "Klein argues capitalism requires perpetual growth that is incompatible with ecological limits — the system itself generates environmental crisis",
        "full_text": "Our economic system and our planetary system are now at war. Or more accurately, our economy is at war with many forms of life on earth, including human life. What the climate needs to avoid collapse is a contraction in humanity's use of resources; what our economic model demands to avoid collapse is unfettered expansion. Only one of these sets of rules can be changed, and it's not the laws of nature.",
        "topic_tags": ["capitalism", "environment", "climate_change", "growth", "ecological_limits"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.8,
    },
    # ── Democracy & Authoritarianism ─────────────────────────
    {
        "source_code": "FUKUYAMA_END_1992",
        "claim_ref": "Chapter 28 — In the Zone of Peace",
        "summary": "Fukuyama argues liberal democracies do not go to war with each other — the democratic peace theory supports spreading democracy globally",
        "full_text": "There is substantial empirical evidence that liberal democracies very rarely go to war against each other. The democratic peace is not perfect, but it is one of the strongest statistical findings in international relations. As more countries democratize, the zone of peace expands. This is a powerful argument for promoting democracy globally — not as cultural imperialism but as a path to international security.",
        "topic_tags": ["democracy", "democratic_peace", "war", "international_relations", "liberalism"],
        "supports_side": "pro",
        "evidence_type": "empirical",
        "weight": 0.8,
    },
    # ── Inequality ───────────────────────────────────────────
    {
        "source_code": "STIGLITZ_PRICE_2019",
        "claim_ref": "Chapter 7 — Restoring Democracy",
        "summary": "Stiglitz argues extreme inequality undermines democracy — concentrated wealth translates into concentrated political power",
        "full_text": "Extreme inequality is incompatible with genuine democracy. When wealth becomes too concentrated, it translates directly into political power. The wealthy use their resources to shape the rules of the game — tax laws, financial regulations, electoral systems — in ways that perpetuate and amplify their advantages. One dollar, one vote has replaced one person, one vote. Addressing inequality requires restoring genuine political democracy.",
        "topic_tags": ["inequality", "democracy", "wealth_concentration", "political_power", "oligarchy"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.9,
    },
    # ── Human Rights & Culture ───────────────────────────────
    {
        "source_code": "SINGER_PRACTICAL_1979",
        "claim_ref": "Chapter 8 — Rich and Poor",
        "summary": "Peter Singer argues affluent people have a strong moral obligation to give to the global poor — geographic distance does not diminish moral responsibility",
        "full_text": "If it is in our power to prevent something bad from happening, without thereby sacrificing anything of comparable moral importance, we ought, morally, to do it. An affluent person who allows a child to die from a preventable disease when they could donate to save that child is morally equivalent to someone who walks past a drowning child to avoid getting their clothes muddy. Distance and nationality do not diminish this obligation.",
        "topic_tags": ["global_poverty", "moral_obligation", "affluence", "aid", "ethics"],
        "supports_side": "pro",
        "evidence_type": "logical",
        "weight": 0.9,
    },
]


async def embed(text):
    r = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text.strip().replace("\n", " ")
    )
    return r.data[0].embedding


async def seed():
    print("Connecting...")
    conn = await asyncpg.connect(dsn=DATABASE_URL)
    await conn.execute("SET search_path TO public")
    await register_vector(conn)

    # Add new sources
    print(f"Adding {len(NEW_SOURCES)} new sources...")
    for s in NEW_SOURCES:
        existing = await conn.fetchrow("SELECT id FROM knowledge_sources WHERE code=$1", s["code"])
        if not existing:
            await conn.execute(
                """INSERT INTO knowledge_sources
                   (code, title, author, institution, year, domain, stance, credibility, url)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)""",
                s["code"], s["title"], s.get("author"), s.get("institution"),
                s.get("year"), s["domain"], s["stance"], s["credibility"], s.get("url")
            )
            print(f"  + {s['code']}")

    rows = await conn.fetch("SELECT id, code FROM knowledge_sources")
    source_ids = {r["code"]: str(r["id"]) for r in rows}

    print(f"\nSeeding {len(FINAL_CLAIMS)} final claims...\n")
    added = 0

    for i, c in enumerate(FINAL_CLAIMS):
        sid = source_ids.get(c["source_code"])
        if not sid:
            print(f"  SKIP: {c['source_code']} not found")
            continue

        existing = await conn.fetchrow(
            "SELECT id FROM knowledge_claims WHERE source_id=$1 AND claim_ref=$2",
            sid, c["claim_ref"]
        )
        if existing:
            print(f"  [{i+1}] SKIP (exists)")
            continue

        print(f"  [{i+1}/{len(FINAL_CLAIMS)}] {c['source_code']} -- {c['claim_ref'][:45]}...")
        embedding = await embed(c["full_text"])
        await conn.execute(
            """INSERT INTO knowledge_claims
               (source_id, claim_ref, summary, full_text, topic_tags,
                supports_side, evidence_type, weight, embedding)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)""",
            sid, c["claim_ref"], c["summary"], c["full_text"],
            c["topic_tags"], c["supports_side"], c["evidence_type"],
            c["weight"], embedding
        )
        print(f"      + {c['summary'][:60]}...")
        added += 1

    total = await conn.fetchval("SELECT COUNT(*) FROM knowledge_claims")
    sources_total = await conn.fetchval("SELECT COUNT(*) FROM knowledge_sources")

    print(f"\nDone!")
    print(f"  Added:         {added} claims")
    print(f"  Total claims:  {total}")
    print(f"  Total sources: {sources_total} thinkers/institutions")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
