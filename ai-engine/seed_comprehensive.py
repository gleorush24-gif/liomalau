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

# ── New legal sources to add ──────────────────────────────────
NEW_SOURCES = [
    {
        "code": "REFUGEE_CONV_1951",
        "title": "Convention Relating to the Status of Refugees",
        "body": "UN General Assembly",
        "year": 1951,
        "category": "treaty",
        "url": "https://www.unhcr.org/1951-refugee-convention.html",
    },
    {
        "code": "CAT_1984",
        "title": "Convention Against Torture and Other Cruel, Inhuman or Degrading Treatment",
        "body": "UN General Assembly",
        "year": 1984,
        "category": "treaty",
        "url": "https://www.ohchr.org/en/instruments-mechanisms/instruments/convention-against-torture",
    },
    {
        "code": "CRC_1989",
        "title": "Convention on the Rights of the Child",
        "body": "UN General Assembly",
        "year": 1989,
        "category": "treaty",
        "url": "https://www.ohchr.org/en/instruments-mechanisms/instruments/convention-rights-child",
    },
    {
        "code": "UN_CHARTER_1945",
        "title": "Charter of the United Nations",
        "body": "United Nations",
        "year": 1945,
        "category": "treaty",
        "url": "https://www.un.org/en/about-us/un-charter",
    },
    {
        "code": "ICESCR_1966",
        "title": "International Covenant on Economic, Social and Cultural Rights",
        "body": "UN General Assembly",
        "year": 1966,
        "category": "treaty",
        "url": "https://www.ohchr.org/en/instruments-mechanisms/instruments/international-covenant-economic-social-and-cultural-rights",
    },
    {
        "code": "GC_I_1949",
        "title": "Geneva Convention I — Wounded and Sick in Armed Forces",
        "body": "ICRC",
        "year": 1949,
        "category": "treaty",
        "url": "https://ihl-databases.icrc.org/gc1",
    },
    {
        "code": "AP_I_1977",
        "title": "Additional Protocol I to the Geneva Conventions",
        "body": "ICRC",
        "year": 1977,
        "category": "treaty",
        "url": "https://ihl-databases.icrc.org/api",
    },
    {
        "code": "UNSC_RES_1373",
        "title": "UN Security Council Resolution 1373 — Counter-Terrorism",
        "body": "UN Security Council",
        "year": 2001,
        "category": "binding",
        "url": "https://undocs.org/S/RES/1373(2001)",
    },
    {
        "code": "UNSC_RES_478",
        "title": "UN Security Council Resolution 478 — Jerusalem",
        "body": "UN Security Council",
        "year": 1980,
        "category": "binding",
        "url": "https://undocs.org/S/RES/478(1980)",
    },
    {
        "code": "UNSC_RES_1701",
        "title": "UN Security Council Resolution 1701 — Lebanon Ceasefire",
        "body": "UN Security Council",
        "year": 2006,
        "category": "binding",
        "url": "https://undocs.org/S/RES/1701(2006)",
    },
    {
        "code": "ICJ_WALL_2004",
        "title": "ICJ Advisory Opinion — Legal Consequences of the Construction of a Wall",
        "body": "International Court of Justice",
        "year": 2004,
        "category": "non_binding",
        "url": "https://www.icj-cij.org/case/131",
    },
    {
        "code": "CUSTOMARY_IHL",
        "title": "ICRC Study on Customary International Humanitarian Law",
        "body": "ICRC",
        "year": 2005,
        "category": "non_binding",
        "url": "https://ihl-databases.icrc.org/customary-ihl",
    },
]

# ── Comprehensive precedents ──────────────────────────────────
PRECEDENTS = [

    # ════════════════════════════════════════════
    # REFUGEE & ASYLUM LAW
    # ════════════════════════════════════════════
    {
        "source_code": "REFUGEE_CONV_1951",
        "article_ref": "Article 1A(2) — Refugee Definition",
        "summary": "Defines a refugee as a person with well-founded fear of persecution based on race, religion, nationality, political opinion, or membership of a particular social group",
        "full_text": "A person who owing to well-founded fear of being persecuted for reasons of race, religion, nationality, membership of a particular social group or political opinion, is outside the country of his nationality and is unable or, owing to such fear, is unwilling to avail himself of the protection of that country.",
        "topic_tags": ["refugee", "asylum", "persecution", "definition"],
        "weight": 1.0,
    },
    {
        "source_code": "REFUGEE_CONV_1951",
        "article_ref": "Article 33 — Non-Refoulement",
        "summary": "Prohibits states from returning refugees to territories where they face serious threats to their life or freedom",
        "full_text": "No Contracting State shall expel or return a refugee in any manner whatsoever to the frontiers of territories where his life or freedom would be threatened on account of his race, religion, nationality, membership of a particular social group or political opinion.",
        "topic_tags": ["non_refoulement", "deportation", "asylum", "refugee_protection"],
        "weight": 1.0,
    },
    {
        "source_code": "REFUGEE_CONV_1951",
        "article_ref": "Article 31 — Non-Penalisation",
        "summary": "Refugees who enter illegally from territories where their life was threatened shall not be penalised",
        "full_text": "The Contracting States shall not impose penalties, on account of their illegal entry or presence, on refugees who, coming directly from a territory where their life or freedom was threatened in the sense of article 1, enter or are present in their territory without authorization.",
        "topic_tags": ["illegal_entry", "asylum_seekers", "penalties", "refugee"],
        "weight": 1.0,
    },
    {
        "source_code": "CAT_1984",
        "article_ref": "Article 1 — Definition of Torture",
        "summary": "Defines torture as severe pain or suffering intentionally inflicted by or with acquiescence of a public official",
        "full_text": "The term torture means any act by which severe pain or suffering, whether physical or mental, is intentionally inflicted on a person for such purposes as obtaining from him or a third person information or a confession, punishing him for an act he or a third person has committed or is suspected of having committed, or intimidating or coercing him or a third person, or for any reason based on discrimination of any kind, when such pain or suffering is inflicted by or at the instigation of or with the consent or acquiescence of a public official or other person acting in an official capacity.",
        "topic_tags": ["torture", "cruel_treatment", "inhuman_treatment", "state_actors"],
        "weight": 1.0,
    },
    {
        "source_code": "CAT_1984",
        "article_ref": "Article 3 — Non-Refoulement from Torture",
        "summary": "No state shall expel or return a person to a state where there are substantial grounds for believing they would be subjected to torture",
        "full_text": "No State Party shall expel, return or extradite a person to another State where there are substantial grounds for believing that he would be in danger of being subjected to torture. For the purpose of determining whether there are such grounds, the competent authorities shall take into account all relevant considerations including, where applicable, the existence in the State concerned of a consistent pattern of gross, flagrant or mass violations of human rights.",
        "topic_tags": ["torture", "non_refoulement", "extradition", "deportation"],
        "weight": 1.0,
    },
    {
        "source_code": "ICCPR_1966",
        "article_ref": "Article 9 — Liberty and Security of Person",
        "summary": "Everyone has the right to liberty. No one shall be subjected to arbitrary arrest or detention",
        "full_text": "Everyone has the right to liberty and security of person. No one shall be subjected to arbitrary arrest or detention. No one shall be deprived of his liberty except on such grounds and in accordance with such procedure as are established by law.",
        "topic_tags": ["arbitrary_detention", "liberty", "security", "arrest", "immigration_detention"],
        "weight": 1.0,
    },
    {
        "source_code": "ICCPR_1966",
        "article_ref": "Article 7 — Prohibition of Torture",
        "summary": "No one shall be subjected to torture or to cruel, inhuman or degrading treatment or punishment",
        "full_text": "No one shall be subjected to torture or to cruel, inhuman or degrading treatment or punishment. In particular, no one shall be subjected without his free consent to medical or scientific experimentation.",
        "topic_tags": ["torture", "cruel_treatment", "inhuman_treatment", "degrading_treatment"],
        "weight": 1.0,
    },

    # ════════════════════════════════════════════
    # COLLECTIVE PUNISHMENT & BLOCKADES
    # ════════════════════════════════════════════
    {
        "source_code": "GC_IV_1949",
        "article_ref": "Article 33 — Collective Punishment",
        "summary": "Collective punishment of civilians and all reprisals against protected persons and their property are prohibited",
        "full_text": "No protected person may be punished for an offence he or she has not personally committed. Collective penalties and likewise all measures of intimidation or of terrorism are prohibited. Pillage is prohibited. Reprisals against protected persons and their property are prohibited.",
        "topic_tags": ["collective_punishment", "reprisals", "civilian_protection", "blockade"],
        "weight": 1.0,
    },
    {
        "source_code": "AP_I_1977",
        "article_ref": "Article 51 — Protection of Civilian Population",
        "summary": "Civilians shall not be the object of attack. Indiscriminate attacks are prohibited. Acts of violence spread terror among civilians are prohibited",
        "full_text": "The civilian population and individual civilians shall enjoy general protection against dangers arising from military operations. The civilian population as such, as well as individual civilians, shall not be the object of attack. Acts or threats of violence the primary purpose of which is to spread terror among the civilian population are prohibited. Indiscriminate attacks are prohibited.",
        "topic_tags": ["civilian_protection", "indiscriminate_attacks", "terror", "proportionality"],
        "weight": 1.0,
    },
    {
        "source_code": "AP_I_1977",
        "article_ref": "Article 54 — Protection of Objects Indispensable to Survival",
        "summary": "Starvation of civilians as a method of warfare is prohibited. Objects indispensable to survival such as food and water must not be destroyed",
        "full_text": "Starvation of civilians as a method of warfare is prohibited. It is prohibited to attack, destroy, remove or render useless objects indispensable to the survival of the civilian population, such as foodstuffs, agricultural areas for the production of foodstuffs, crops, livestock, drinking water installations and supplies and irrigation works.",
        "topic_tags": ["starvation", "civilian_survival", "food_security", "blockade", "humanitarian"],
        "weight": 1.0,
    },
    {
        "source_code": "CUSTOMARY_IHL",
        "article_ref": "Rule 53 — Starvation as Method of Warfare",
        "summary": "The use of starvation of the civilian population as a method of warfare is prohibited under customary international law",
        "full_text": "The use of starvation of the civilian population as a method of warfare is prohibited. This rule is a norm of customary international law applicable in both international and non-international armed conflicts. A total blockade that causes starvation of civilians violates this prohibition.",
        "topic_tags": ["starvation", "blockade", "customary_law", "siege", "civilian_population"],
        "weight": 0.8,
    },

    # ════════════════════════════════════════════
    # USE OF FORCE & SELF-DEFENCE
    # ════════════════════════════════════════════
    {
        "source_code": "UN_CHARTER_1945",
        "article_ref": "Article 2(4) — Prohibition on Use of Force",
        "summary": "All UN members shall refrain from the threat or use of force against the territorial integrity or political independence of any state",
        "full_text": "All Members shall refrain in their international relations from the threat or use of force against the territorial integrity or political independence of any state, or in any other manner inconsistent with the Purposes of the United Nations.",
        "topic_tags": ["use_of_force", "territorial_integrity", "sovereignty", "aggression"],
        "weight": 1.0,
    },
    {
        "source_code": "UN_CHARTER_1945",
        "article_ref": "Article 51 — Right of Self-Defence",
        "summary": "Nothing impairs the inherent right of individual or collective self-defence if an armed attack occurs against a UN member",
        "full_text": "Nothing in the present Charter shall impair the inherent right of individual or collective self-defence if an armed attack occurs against a Member of the United Nations, until the Security Council has taken measures necessary to maintain international peace and security.",
        "topic_tags": ["self_defence", "armed_attack", "collective_defence", "military_force"],
        "weight": 1.0,
    },
    {
        "source_code": "UN_CHARTER_1945",
        "article_ref": "Article 1(1) — Purpose: Peace and Security",
        "summary": "The UN's primary purpose is to maintain international peace and security and suppress acts of aggression",
        "full_text": "To maintain international peace and security, and to that end: to take effective collective measures for the prevention and removal of threats to the peace, and for the suppression of acts of aggression or other breaches of the peace, and to bring about by peaceful means, and in conformity with the principles of justice and international law, adjustment or settlement of international disputes.",
        "topic_tags": ["peace", "security", "aggression", "collective_measures"],
        "weight": 1.0,
    },

    # ════════════════════════════════════════════
    # CHILDREN'S RIGHTS
    # ════════════════════════════════════════════
    {
        "source_code": "CRC_1989",
        "article_ref": "Article 3 — Best Interests of the Child",
        "summary": "In all actions concerning children, the best interests of the child shall be a primary consideration",
        "full_text": "In all actions concerning children, whether undertaken by public or private social welfare institutions, courts of law, administrative authorities or legislative bodies, the best interests of the child shall be a primary consideration.",
        "topic_tags": ["children", "best_interests", "child_protection", "immigration", "detention"],
        "weight": 1.0,
    },
    {
        "source_code": "CRC_1989",
        "article_ref": "Article 37 — Prohibition of Child Detention",
        "summary": "No child shall be subjected to torture. Detention of children shall be used only as a measure of last resort",
        "full_text": "No child shall be subjected to torture or other cruel, inhuman or degrading treatment or punishment. No child shall be deprived of his or her liberty unlawfully or arbitrarily. The arrest, detention or imprisonment of a child shall be in conformity with the law and shall be used only as a measure of last resort and for the shortest appropriate period of time.",
        "topic_tags": ["child_detention", "torture", "last_resort", "liberty", "immigration"],
        "weight": 1.0,
    },
    {
        "source_code": "CRC_1989",
        "article_ref": "Article 22 — Refugee Children",
        "summary": "States shall take appropriate measures to ensure refugee children receive appropriate protection and humanitarian assistance",
        "full_text": "States Parties shall take appropriate measures to ensure that a child who is seeking refugee status or who is considered a refugee in accordance with applicable international or domestic law and procedures shall, whether unaccompanied or accompanied by his or her parents or by any other person, receive appropriate protection and humanitarian assistance in the enjoyment of applicable rights.",
        "topic_tags": ["refugee_children", "unaccompanied_minors", "asylum", "protection"],
        "weight": 1.0,
    },

    # ════════════════════════════════════════════
    # OCCUPATION & ANNEXATION
    # ════════════════════════════════════════════
    {
        "source_code": "ICJ_WALL_2004",
        "article_ref": "Para 120 — Wall in Occupied Territory",
        "summary": "The ICJ found the construction of the wall in the occupied Palestinian territory violated international law including the right to self-determination",
        "full_text": "The construction of the wall being built by Israel, the occupying Power, in the Occupied Palestinian Territory, including in and around East Jerusalem, and its associated regime, are contrary to international law.",
        "topic_tags": ["wall", "barrier", "occupied_territory", "self_determination", "icj"],
        "weight": 0.7,
    },
    {
        "source_code": "UNSC_RES_478",
        "article_ref": "Operative Paragraph 2 — Jerusalem",
        "summary": "Security Council censures Israel's declaration that Jerusalem is its capital and affirms such measures are null and void",
        "full_text": "The Security Council censures in the strongest terms the enactment by Israel of the Basic Law on Jerusalem, considers that all legislative and administrative measures and actions taken by Israel which have altered or purport to alter the character and status of the Holy City of Jerusalem, and in particular the recent Basic Law on Jerusalem, are null and void and must be rescinded forthwith.",
        "topic_tags": ["jerusalem", "annexation", "null_void", "capital", "holy_city"],
        "weight": 1.0,
    },

    # ════════════════════════════════════════════
    # ECONOMIC & SOCIAL RIGHTS
    # ════════════════════════════════════════════
    {
        "source_code": "ICESCR_1966",
        "article_ref": "Article 11 — Right to Adequate Standard of Living",
        "summary": "Everyone has the right to an adequate standard of living including adequate food, clothing and housing",
        "full_text": "The States Parties to the present Covenant recognize the right of everyone to an adequate standard of living for himself and his family, including adequate food, clothing and housing, and to the continuous improvement of living conditions. The States Parties will take appropriate steps to ensure the realization of this right.",
        "topic_tags": ["standard_of_living", "food", "housing", "economic_rights", "humanitarian"],
        "weight": 1.0,
    },
    {
        "source_code": "ICESCR_1966",
        "article_ref": "Article 12 — Right to Health",
        "summary": "Everyone has the right to the enjoyment of the highest attainable standard of physical and mental health",
        "full_text": "The States Parties to the present Covenant recognize the right of everyone to the enjoyment of the highest attainable standard of physical and mental health. The steps to be taken by the States Parties to the present Covenant to achieve the full realization of this right shall include those necessary for the reduction of the stillbirth-rate and of infant mortality.",
        "topic_tags": ["right_to_health", "healthcare", "medical", "occupation", "humanitarian"],
        "weight": 1.0,
    },

    # ════════════════════════════════════════════
    # BORDER CONTROL & SOVEREIGNTY
    # ════════════════════════════════════════════
    {
        "source_code": "UN_CHARTER_1945",
        "article_ref": "Article 2(1) — Sovereign Equality",
        "summary": "The UN is based on the principle of the sovereign equality of all its members",
        "full_text": "The Organization is based on the principle of the sovereign equality of all its Members.",
        "topic_tags": ["sovereignty", "equality", "statehood", "border_control", "immigration"],
        "weight": 1.0,
    },
    {
        "source_code": "ICCPR_1966",
        "article_ref": "Article 12(3) — Restrictions on Movement",
        "summary": "Freedom of movement may be restricted by law where necessary to protect national security or public order",
        "full_text": "The above-mentioned rights shall not be subject to any restrictions except those which are provided by law, are necessary to protect national security, public order, public health or morals or the rights and freedoms of others, and are consistent with the other rights recognized in the present Covenant.",
        "topic_tags": ["freedom_of_movement", "restrictions", "national_security", "public_order", "border"],
        "weight": 1.0,
    },
    {
        "source_code": "CUSTOMARY_IHL",
        "article_ref": "Rule 1 — Distinction between Civilians and Combatants",
        "summary": "The parties to a conflict must at all times distinguish between civilians and combatants. Attacks may only be directed against combatants",
        "full_text": "The parties to a conflict must at all times distinguish between civilians and combatants. Attacks may only be directed against combatants. Attacks must not be directed against civilians. This rule is a norm of customary international law applicable in both international and non-international armed conflicts.",
        "topic_tags": ["distinction", "civilians", "combatants", "targeting", "attacks"],
        "weight": 0.8,
    },

    # ════════════════════════════════════════════
    # TERRORISM & COUNTER-TERRORISM
    # ════════════════════════════════════════════
    {
        "source_code": "UNSC_RES_1373",
        "article_ref": "Operative Paragraph 2(a) — Counter-Terrorism Obligations",
        "summary": "All states must refrain from providing support to those involved in terrorist acts and deny safe haven to terrorists",
        "full_text": "All States shall refrain from providing any form of support, active or passive, to entities or persons involved in terrorist acts, including by suppressing recruitment of members of terrorist groups and eliminating the supply of weapons to terrorists. Take the necessary steps to prevent the commission of terrorist acts.",
        "topic_tags": ["terrorism", "counter_terrorism", "state_obligations", "safe_haven"],
        "weight": 1.0,
    },
    {
        "source_code": "ICCPR_1966",
        "article_ref": "Article 4 — Derogation in Public Emergency",
        "summary": "States may derogate from certain ICCPR obligations in time of public emergency, but cannot derogate from the right to life or prohibition of torture",
        "full_text": "In time of public emergency which threatens the life of the nation and the existence of which is officially proclaimed, the States Parties to the present Covenant may take measures derogating from their obligations under the present Covenant to the extent strictly required by the exigencies of the situation, provided that such measures are not inconsistent with their other obligations under international law.",
        "topic_tags": ["derogation", "emergency", "security", "limitations", "terrorism"],
        "weight": 1.0,
    },

    # ════════════════════════════════════════════
    # MEDICAL & HUMANITARIAN ACCESS
    # ════════════════════════════════════════════
    {
        "source_code": "GC_I_1949",
        "article_ref": "Article 12 — Protection of Wounded and Sick",
        "summary": "Members of the armed forces who are wounded or sick shall be respected and protected. Medical establishments shall not be attacked",
        "full_text": "Members of the armed forces and other persons mentioned in the following Article, who are wounded or sick, shall be respected and protected in all circumstances. They shall be treated humanely and cared for by the Party to the conflict in whose power they may be, without any adverse distinction founded on sex, race, nationality, religion, political opinions, or any other similar criteria.",
        "topic_tags": ["wounded", "sick", "medical_protection", "hospitals", "humanitarian"],
        "weight": 1.0,
    },
    {
        "source_code": "GC_IV_1949",
        "article_ref": "Article 23 — Medical Supplies and Relief",
        "summary": "States must allow free passage of medical and hospital stores and objects necessary for religious worship intended only for civilians",
        "full_text": "Each High Contracting Party shall allow the free passage of all consignments of medical and hospital stores and objects necessary for religious worship intended only for civilians of another High Contracting Party, even if the latter is its adversary. It shall likewise allow the free passage of all consignments of essential foodstuffs, clothing and tonics intended for children under fifteen, expectant mothers and maternity cases.",
        "topic_tags": ["humanitarian_access", "medical_supplies", "food", "children", "blockade"],
        "weight": 1.0,
    },
]


async def get_or_create_source(conn, source: dict) -> str:
    row = await conn.fetchrow(
        "SELECT id FROM legal_sources WHERE code = $1", source["code"]
    )
    if row:
        return str(row["id"])

    row = await conn.fetchrow(
        """
        INSERT INTO legal_sources (code, title, body, year, category, url)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
        """,
        source["code"], source["title"], source["body"],
        source["year"], source["category"], source["url"],
    )
    print(f"  + Added source: {source['code']}")
    return str(row["id"])


async def embed_text(text: str) -> list[float]:
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text.strip().replace("\n", " "),
    )
    return response.data[0].embedding


async def seed():
    print("Connecting to database...")
    conn = await asyncpg.connect(dsn=DATABASE_URL)
    await register_vector(conn)

    # Add new sources
    print(f"\nAdding {len(NEW_SOURCES)} new legal sources...")
    source_ids = {}
    for s in NEW_SOURCES:
        source_ids[s["code"]] = await get_or_create_source(conn, s)

    # Also load existing source IDs
    rows = await conn.fetch("SELECT id, code FROM legal_sources")
    for row in rows:
        source_ids[row["code"]] = str(row["id"])

    print(f"\nSeeding {len(PRECEDENTS)} new precedents...\n")

    added = 0
    skipped = 0

    for i, p in enumerate(PRECEDENTS):
        source_id = source_ids.get(p["source_code"])
        if not source_id:
            print(f"  WARNING: source not found: {p['source_code']}")
            skipped += 1
            continue

        # Check if this precedent already exists
        existing = await conn.fetchrow(
            "SELECT id FROM precedents WHERE source_id = $1 AND article_ref = $2",
            source_id, p["article_ref"]
        )
        if existing:
            print(f"  [{i+1}/{len(PRECEDENTS)}] SKIP (exists): {p['article_ref']}")
            skipped += 1
            continue

        print(f"  [{i+1}/{len(PRECEDENTS)}] Embedding: {p['article_ref']}...")
        embedding = await embed_text(p["full_text"])

        await conn.execute(
            """
            INSERT INTO precedents
                (source_id, article_ref, summary, full_text, topic_tags, weight, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            source_id, p["article_ref"], p["summary"],
            p["full_text"], p["topic_tags"],
            p["weight"], embedding,
        )
        print(f"      + {p['source_code']} -- {p['summary'][:55]}...")
        added += 1

    # Rebuild the vector index now that we have more data
    print("\nRebuilding vector search index...")
    await conn.execute("REINDEX INDEX precedents_embedding_idx;")

    total = await conn.fetchval("SELECT COUNT(*) FROM precedents")
    print(f"\nDone!")
    print(f"  Added:   {added} new precedents")
    print(f"  Skipped: {skipped} (already existed)")
    print(f"  Total:   {total} precedents in panel database")
    print("\nTopics now covered:")
    print("  Refugee law (non-refoulement, asylum, detention)")
    print("  Torture and cruel treatment")
    print("  Collective punishment and blockades")
    print("  Use of force and self-defence")
    print("  Children's rights")
    print("  Occupation and annexation")
    print("  Economic and social rights")
    print("  Border control and sovereignty")
    print("  Counter-terrorism")
    print("  Medical and humanitarian access")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
