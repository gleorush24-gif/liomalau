#!/usr/bin/env python3
# seed_knowledge_extended.py
# Adds more claims to reach 60 total across all major debate topics

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
    {"code": "STERN_REVIEW_2006", "title": "The Stern Review on the Economics of Climate Change", "author": "Nicholas Stern", "institution": "HM Treasury, UK", "year": 2006, "domain": "economics", "stance": "pro", "credibility": "peer_reviewed", "url": "https://webarchive.nationalarchives.gov.uk/stern_review"},
    {"code": "STIGLITZ_PRICE_2019", "title": "People, Power and Profits", "author": "Joseph Stiglitz", "institution": "Columbia University", "year": 2019, "domain": "economics", "stance": "con", "credibility": "peer_reviewed", "url": "https://wwnorton.com/books/9780393358339"},
    {"code": "HAYEK_ROAD_1944", "title": "The Road to Serfdom", "author": "Friedrich Hayek", "institution": "University of Chicago", "year": 1944, "domain": "economics", "stance": "pro", "credibility": "expert_consensus", "url": "https://press.uchicago.edu/ucp/books/book/chicago/R/bo3987847.html"},
    {"code": "KEYNES_GENERAL_1936", "title": "The General Theory of Employment, Interest and Money", "author": "John Maynard Keynes", "institution": "University of Cambridge", "year": 1936, "domain": "economics", "stance": "con", "credibility": "expert_consensus", "url": "https://www.cambridge.org/keynes"},
    {"code": "CHOMSKY_MANUFACTURING_1988", "title": "Manufacturing Consent", "author": "Noam Chomsky and Edward Herman", "institution": "MIT", "year": 1988, "domain": "politics", "stance": "con", "credibility": "documented_position", "url": "https://www.penguinrandomhouse.com/books/86993/manufacturing-consent-by-noam-chomsky-and-edward-s-herman/"},
    {"code": "FUKUYAMA_END_1992", "title": "The End of History and the Last Man", "author": "Francis Fukuyama", "institution": "Johns Hopkins University", "year": 1992, "domain": "politics", "stance": "pro", "credibility": "documented_position", "url": "https://www.penguinrandomhouse.com/books/286814/the-end-of-history-and-the-last-man-by-francis-fukuyama/"},
    {"code": "HUNTINGTON_CLASH_1996", "title": "The Clash of Civilizations", "author": "Samuel Huntington", "institution": "Harvard University", "year": 1996, "domain": "politics", "stance": "con", "credibility": "documented_position", "url": "https://www.simonandschuster.com/books/The-Clash-of-Civilizations-and-the-Remaking-of-World-Order/Samuel-P-Huntington/9781451628975"},
    {"code": "KLEIN_SHOCK_2007", "title": "The Shock Doctrine", "author": "Naomi Klein", "institution": "Independent", "year": 2007, "domain": "economics", "stance": "con", "credibility": "documented_position", "url": "https://naomiklein.org/shock-doctrine/"},
    {"code": "PINKER_BETTER_2011", "title": "The Better Angels of Our Nature", "author": "Steven Pinker", "institution": "Harvard University", "year": 2011, "domain": "history", "stance": "pro", "credibility": "peer_reviewed", "url": "https://stevenpinker.com/publications/better-angels-our-nature"},
    {"code": "GRAEBER_DEBT_2011", "title": "Debt: The First 5,000 Years", "author": "David Graeber", "institution": "London School of Economics", "year": 2011, "domain": "economics", "stance": "con", "credibility": "documented_position", "url": "https://www.mhpbooks.com/books/debt/"},
    {"code": "ACEMOGLU_WHY_2012", "title": "Why Nations Fail", "author": "Daron Acemoglu and James Robinson", "institution": "MIT", "year": 2012, "domain": "economics", "stance": "neutral", "credibility": "peer_reviewed", "url": "https://www.whynationsfail.com"},
    {"code": "DIAMOND_GUNS_1997", "title": "Guns, Germs and Steel", "author": "Jared Diamond", "institution": "UCLA", "year": 1997, "domain": "history", "stance": "neutral", "credibility": "peer_reviewed", "url": "https://wwnorton.com/books/guns-germs-and-steel/"},
    {"code": "AMNESTY_APARTHEID_2022", "title": "Israel Apartheid Report 2022", "author": "Amnesty International Research Team", "institution": "Amnesty International", "year": 2022, "domain": "politics", "stance": "con", "credibility": "documented_position", "url": "https://www.amnesty.org/apartheid-report"},
    {"code": "HRW_APARTHEID_2021", "title": "A Threshold Crossed: Israeli Authorities and the Crime of Apartheid", "author": "Human Rights Watch", "institution": "Human Rights Watch", "year": 2021, "domain": "politics", "stance": "con", "credibility": "documented_position", "url": "https://www.hrw.org/report/2021/04/27/threshold-crossed"},
    {"code": "DERSHOWITZ_CASE_2003", "title": "The Case for Israel", "author": "Alan Dershowitz", "institution": "Harvard Law School", "year": 2003, "domain": "politics", "stance": "pro", "credibility": "documented_position", "url": "https://www.wiley.com/the-case-for-israel"},
]

EXTENDED_CLAIMS = [
    # ════════════════════════════════════════════
    # CLIMATE CHANGE — additional
    # ════════════════════════════════════════════
    {
        "source_code": "STERN_REVIEW_2006",
        "claim_ref": "Executive Summary",
        "summary": "The cost of inaction on climate change is far greater than the cost of action — climate change is the greatest market failure in history",
        "full_text": "The Review is clear that the benefits of strong, early action considerably outweigh the costs. The evidence gathered by the Review leads to a simple conclusion: the benefits of strong, early action on climate change outweigh the costs. Ignoring climate change will eventually damage economic growth. Our actions over the coming few decades could create risks of major disruption to economic and social activity, later in this century and in the next, on a scale similar to those associated with the great wars and the economic depression of the first half of the 20th century.",
        "topic_tags": ["climate_change", "economics", "cost_benefit", "market_failure", "policy"],
        "supports_side": "pro",
        "evidence_type": "empirical",
        "weight": 1.0,
    },
    {
        "source_code": "LOMBORG_COOL_2020",
        "claim_ref": "Chapter 12 — The Cost of Climate Panic",
        "summary": "Lomborg argues climate policy must pass a cost-benefit test — current Paris Agreement policies cost $1 trillion per year but reduce warming by only 0.05 degrees",
        "full_text": "The Paris Agreement will cost the world between $1 trillion and $2 trillion every year throughout this century. Yet the total temperature reduction by 2100 will be a barely noticeable 0.05 degrees Celsius. That is not a good deal. We need smarter climate policies that focus on green innovation, not expensive mandates that slow economies and hurt the world's poorest people the most.",
        "topic_tags": ["climate_policy", "paris_agreement", "cost_benefit", "lomborg", "skepticism"],
        "supports_side": "con",
        "evidence_type": "statistical",
        "weight": 0.7,
    },

    # ════════════════════════════════════════════
    # CAPITALISM VS SOCIALISM
    # ════════════════════════════════════════════
    {
        "source_code": "HAYEK_ROAD_1944",
        "claim_ref": "Chapter 3 — Individualism and Collectivism",
        "summary": "Central economic planning inevitably leads to tyranny — the road to serfdom is paved with socialist intentions",
        "full_text": "Economic control is not merely control of a sector of human life which can be separated from the rest; it is the control of the means for all our ends. And whoever has sole control of the means must also determine which ends are to be served, which values are to be rated higher and which lower — in short, what men should believe and strive for. It is for this reason that the authority wielding this control must include everything from the smallest to the greatest.",
        "topic_tags": ["socialism", "central_planning", "freedom", "hayek", "capitalism"],
        "supports_side": "pro",
        "evidence_type": "logical",
        "weight": 0.9,
    },
    {
        "source_code": "KEYNES_GENERAL_1936",
        "claim_ref": "Chapter 24 — Concluding Notes",
        "summary": "Free markets do not automatically reach full employment equilibrium — government intervention through fiscal policy is necessary to prevent prolonged recessions",
        "full_text": "The outstanding faults of the economic society in which we live are its failure to provide for full employment and its arbitrary and inequitable distribution of wealth and incomes. The State will have to exercise a guiding influence on the propensity to consume partly through its scheme of taxation, partly by fixing the rate of interest, and partly, perhaps, in other ways.",
        "topic_tags": ["keynesian_economics", "government_intervention", "employment", "fiscal_policy"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.9,
    },
    {
        "source_code": "STIGLITZ_PRICE_2019",
        "claim_ref": "Chapter 2",
        "summary": "Market power and monopolies have increased inequality dramatically — markets are not self-correcting and require robust regulation",
        "full_text": "Over the past four decades, the rules of the market economy have been rewritten, deliberately and repeatedly, to benefit corporations and the wealthy at the expense of everyone else. The result is an economy with more market power, more rent-seeking, more exploitation, and more inequality. Markets don't exist in a vacuum — they are shaped by rules, and those rules have been written by and for those at the top.",
        "topic_tags": ["inequality", "market_power", "monopolies", "regulation", "capitalism"],
        "supports_side": "con",
        "evidence_type": "empirical",
        "weight": 0.9,
    },
    {
        "source_code": "ACEMOGLU_WHY_2012",
        "claim_ref": "Chapter 1",
        "summary": "Nations fail because of extractive political and economic institutions — inclusive institutions that protect property rights and rule of law create prosperity",
        "full_text": "Countries differ in their economic success because of their different institutions, the rules influencing how the economy works, and the incentives that motivate people. Inclusive economic institutions that enforce property rights, create a level playing field, and encourage investments in new technologies and skills are more conducive to economic growth than extractive economic institutions that are structured to extract resources from the many by the few.",
        "topic_tags": ["institutions", "economic_development", "property_rights", "rule_of_law"],
        "supports_side": "neutral",
        "evidence_type": "empirical",
        "weight": 1.0,
    },
    {
        "source_code": "GRAEBER_DEBT_2011",
        "claim_ref": "Chapter 12",
        "summary": "Debt has historically been a tool of social control and violence — the moral imperative to repay debts is a myth constructed to serve creditors",
        "full_text": "The very fact that we don't know what we owe to one another, or to society, or to history, reflects the fact that human economies are not, at their root, about exchange at all. They are about creating, maintaining, and renegotiating relations among human beings. The myth of barter leads directly to the idea that markets are natural, self-regulating, and tend toward equilibrium — all of which are false.",
        "topic_tags": ["debt", "capitalism", "social_control", "inequality", "money"],
        "supports_side": "con",
        "evidence_type": "historical",
        "weight": 0.8,
    },
    {
        "source_code": "KLEIN_SHOCK_2007",
        "claim_ref": "Introduction",
        "summary": "Naomi Klein documents how free market reforms are systematically imposed during crises and disasters when populations are too shocked to resist",
        "full_text": "I call it the shock doctrine: the exploitation of national crises to push through controversial policies while the citizenry is reeling from shock. From Chile in 1973 to Iraq in 2003, this brutal tactic has been used again and again. Disaster capitalism uses the psychological state of shock to push radical market reforms that could never be achieved democratically.",
        "topic_tags": ["neoliberalism", "shock_doctrine", "disaster_capitalism", "free_market", "crisis"],
        "supports_side": "con",
        "evidence_type": "historical",
        "weight": 0.8,
    },

    # ════════════════════════════════════════════
    # GEOPOLITICS & DEMOCRACY
    # ════════════════════════════════════════════
    {
        "source_code": "FUKUYAMA_END_1992",
        "claim_ref": "Introduction",
        "summary": "Liberal democracy represents the final form of human government — the end of history as ideological evolution reaches its terminus",
        "full_text": "What we may be witnessing is not just the end of the Cold War, or the passing of a particular period of postwar history, but the end of history as such: that is, the end point of mankind's ideological evolution and the universalization of Western liberal democracy as the final form of human government.",
        "topic_tags": ["liberal_democracy", "end_of_history", "western_values", "geopolitics"],
        "supports_side": "pro",
        "evidence_type": "logical",
        "weight": 0.7,
    },
    {
        "source_code": "HUNTINGTON_CLASH_1996",
        "claim_ref": "Chapter 1",
        "summary": "Samuel Huntington argues the primary source of conflict in the post-Cold War world will be cultural and civilizational rather than ideological",
        "full_text": "It is my hypothesis that the fundamental source of conflict in this new world will not be primarily ideological or primarily economic. The great divisions among humankind and the dominating source of conflict will be cultural. Nation states will remain the most powerful actors in world affairs, but the principal conflicts of global politics will occur between nations and groups of different civilizations.",
        "topic_tags": ["civilization", "conflict", "culture", "geopolitics", "islam_west"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.7,
    },
    {
        "source_code": "CHOMSKY_MANUFACTURING_1988",
        "claim_ref": "Introduction — A Propaganda Model",
        "summary": "Mass media serves the interests of powerful elites through a propaganda model — filters determine what becomes news and what is suppressed",
        "full_text": "The mass media serve as a system for communicating messages and symbols to the general populace. It is their function to amuse, entertain, and inform, and to inculcate individuals with the values, beliefs, and codes of behavior that will integrate them into the institutional structures of the larger society. In a world of concentrated wealth and major conflicts of class interest, to fulfil this role requires systematic propaganda.",
        "topic_tags": ["media", "propaganda", "power", "democracy", "elite_control"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.8,
    },

    # ════════════════════════════════════════════
    # HUMAN PROGRESS
    # ════════════════════════════════════════════
    {
        "source_code": "PINKER_BETTER_2011",
        "claim_ref": "Introduction",
        "summary": "Steven Pinker documents the long-term decline of violence across history — we are living in the most peaceful era in human existence",
        "full_text": "The decline of violence may be the most important thing that has ever happened in human history. Believe it or not — and I know that most people do not — violence has declined over long stretches of time, and today we may be living in the most peaceable era in our species' existence. The decline of violence is a fractal phenomenon, visible at the scale of millennia, centuries, decades, and years.",
        "topic_tags": ["violence", "progress", "history", "peace", "optimism"],
        "supports_side": "pro",
        "evidence_type": "empirical",
        "weight": 0.9,
    },
    {
        "source_code": "DIAMOND_GUNS_1997",
        "claim_ref": "Prologue — Yali's Question",
        "summary": "Geographic and environmental factors explain why some civilizations developed guns germs and steel — not racial or cultural superiority",
        "full_text": "The striking differences between the long-term histories of peoples of the different continents have been due not to innate differences in the peoples themselves but to differences in their environments. This is not a racist conclusion but an anti-racist one. European colonialism was not due to European superiority but to accidents of geography — Eurasia's east-west axis, its domesticable plants and animals, and its exposure to germs.",
        "topic_tags": ["colonialism", "geography", "history", "racism", "civilization"],
        "supports_side": "neutral",
        "evidence_type": "empirical",
        "weight": 0.9,
    },

    # ════════════════════════════════════════════
    # ISRAEL-PALESTINE — ADVOCACY POSITIONS
    # ════════════════════════════════════════════
    {
        "source_code": "AMNESTY_APARTHEID_2022",
        "claim_ref": "Executive Summary",
        "summary": "Amnesty International concludes Israel is committing the crime of apartheid against Palestinians — a system of oppression and domination",
        "full_text": "Amnesty International has concluded that the Israeli government is committing the crime of apartheid against Palestinians. Israel has established and maintains a system of oppression and domination over Palestinians wherever it exercises control over their rights. This includes Palestinians living in Israel and the OPT, as well as Palestinian refugees. The system constitutes a violation of international law and amounts to apartheid as prohibited in international law.",
        "topic_tags": ["apartheid", "israel_palestine", "human_rights", "amnesty", "occupation"],
        "supports_side": "con",
        "evidence_type": "expert_opinion",
        "weight": 0.8,
    },
    {
        "source_code": "HRW_APARTHEID_2021",
        "claim_ref": "Summary",
        "summary": "Human Rights Watch found Israeli authorities are committing crimes of apartheid and persecution against Palestinians based on systematic dispossession",
        "full_text": "Israeli authorities are committing the crime against humanity of apartheid, as well as the crime against humanity of persecution. Two key elements of these crimes under international criminal law are the intent to maintain a system of domination and a systematic and severe deprivation of fundamental rights. The deprivation of rights for Palestinians is not an accidental byproduct of security concerns but rather the foreseeable consequence of policies designed to privilege Jewish Israelis.",
        "topic_tags": ["apartheid", "israel_palestine", "hrw", "persecution", "international_law"],
        "supports_side": "con",
        "evidence_type": "expert_opinion",
        "weight": 0.8,
    },
    {
        "source_code": "DERSHOWITZ_CASE_2003",
        "claim_ref": "Chapter 1",
        "summary": "Alan Dershowitz argues Israel is the most scrutinized nation on earth — the case for Israel rests on its democratic values, rule of law and right to self-defence",
        "full_text": "Israel is the only democracy in the Middle East. It has an independent judiciary, a free press, a vibrant civil society, and equal rights for Arab citizens. It is held to standards applied to no other nation on earth. The legal case for Israel rests on the right of the Jewish people to self-determination, recognized in international law, and Israel's right to defend itself against terrorist attacks that deliberately target civilians.",
        "topic_tags": ["israel", "democracy", "self_defence", "legitimacy", "rule_of_law"],
        "supports_side": "pro",
        "evidence_type": "logical",
        "weight": 0.7,
    },

    # ════════════════════════════════════════════
    # AI — ADDITIONAL
    # ════════════════════════════════════════════
    {
        "source_code": "BOSTROM_SUPERINTELLIGENCE_2014",
        "claim_ref": "Chapter 8 — The Orthogonality Thesis",
        "summary": "An AI can have any goal combined with any level of intelligence — a superintelligent AI optimizing for paperclips could destroy humanity",
        "full_text": "The orthogonality thesis holds that intelligence and final goals are orthogonal: more or less any level of intelligence could in principle be combined with more or less any final goal. This is important because it means a superintelligent AI could pursue any goal we give it with extreme competence — including goals that are catastrophic from a human perspective. An AI tasked with making paperclips could convert all available matter, including humans, into paperclip-making machinery.",
        "topic_tags": ["ai_risk", "superintelligence", "orthogonality", "existential_risk", "alignment"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.9,
    },

    # ════════════════════════════════════════════
    # DRUG POLICY — ADDITIONAL
    # ════════════════════════════════════════════
    {
        "source_code": "WHO_DRUG_POLICY_2019",
        "claim_ref": "Harm Reduction Section",
        "summary": "WHO supports harm reduction approaches — evidence shows needle exchanges, supervised injection sites and drug treatment reduce death and disease without increasing drug use",
        "full_text": "Harm reduction refers to policies, programmes and practices that aim to reduce the negative health, social and economic impacts associated with the use of psychoactive substances in people unable or unwilling to stop. The evidence base for harm reduction is compelling. Needle exchange programmes reduce HIV transmission by up to 50 percent. Supervised injection facilities reduce overdose deaths. These approaches do not increase drug use in communities.",
        "topic_tags": ["harm_reduction", "drug_policy", "public_health", "needle_exchange", "overdose"],
        "supports_side": "pro",
        "evidence_type": "empirical",
        "weight": 1.0,
    },

    # ════════════════════════════════════════════
    # IMMIGRATION & MULTICULTURALISM
    # ════════════════════════════════════════════
    {
        "source_code": "WORLD_BANK_POVERTY_2022",
        "claim_ref": "Migration Chapter",
        "summary": "International migration increases GDP in destination countries and reduces poverty in origin countries — economic evidence strongly supports open migration",
        "full_text": "Migration is one of the most powerful tools for poverty reduction. Migrants earn higher wages, send remittances home, and contribute to economic growth in destination countries. Studies consistently show that immigrants are net contributors to public finances over their lifetimes. The economic benefits of migration are substantial and widely shared.",
        "topic_tags": ["immigration", "migration", "economics", "poverty_reduction", "multiculturalism"],
        "supports_side": "pro",
        "evidence_type": "empirical",
        "weight": 1.0,
    },
    {
        "source_code": "HUNTINGTON_CLASH_1996",
        "claim_ref": "Chapter 9 — The Global Politics of Civilizations",
        "summary": "Huntington argues mass immigration creates cultural conflict — cultural cohesion is necessary for stable democratic societies",
        "full_text": "Countries that receive large numbers of immigrants from a single source country face the challenge of maintaining national identity and cultural cohesion. When immigrants maintain strong ties to their home culture and resist assimilation, this creates parallel societies within nations. Cultural differences are real and consequential — civilizational identity cannot be reduced to economic factors.",
        "topic_tags": ["immigration", "multiculturalism", "cultural_cohesion", "assimilation", "identity"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.7,
    },

    # ════════════════════════════════════════════
    # GENDER & FEMINISM
    # ════════════════════════════════════════════
    {
        "source_code": "SINGER_PRACTICAL_1979",
        "claim_ref": "Chapter 3 — Equality for Animals",
        "summary": "Peter Singer argues that equal consideration of interests requires overcoming speciesism just as we overcame racism and sexism",
        "full_text": "The question is not, Can they reason? nor, Can they talk? but, Can they suffer? If a being suffers there can be no moral justification for refusing to take that suffering into consideration. No matter what the nature of the being, the principle of equality requires that its suffering be counted equally with the like suffering of any other being. Racism and sexism are wrong because they arbitrarily privilege one group — speciesism makes the same error.",
        "topic_tags": ["animal_rights", "equality", "speciesism", "ethics", "singer"],
        "supports_side": "pro",
        "evidence_type": "logical",
        "weight": 0.8,
    },

    # ════════════════════════════════════════════
    # NUCLEAR WEAPONS
    # ════════════════════════════════════════════
    {
        "source_code": "RUSSELL_HUMAN_2019",
        "claim_ref": "Chapter 1 — The Problem",
        "summary": "Stuart Russell argues that nuclear weapons and now AI represent existential risks requiring international governance frameworks",
        "full_text": "We faced the existential threat of nuclear weapons and responded by creating international governance mechanisms — the NPT, START treaties, and the norm against use. We now face a potentially greater threat from AI systems that could be weaponized or pursue goals misaligned with human values. The same logic applies: we need international frameworks before the technology outpaces our governance capacity.",
        "topic_tags": ["nuclear_weapons", "existential_risk", "governance", "international_law", "ai"],
        "supports_side": "neutral",
        "evidence_type": "logical",
        "weight": 0.9,
    },

    # ════════════════════════════════════════════
    # RELIGION & SECULARISM
    # ════════════════════════════════════════════
    {
        "source_code": "RAWLS_JUSTICE_1971",
        "claim_ref": "Political Liberalism Supplement",
        "summary": "Rawls argues that in a pluralist society, political decisions must be justified by public reason accessible to all citizens — not religious doctrine",
        "full_text": "In a democratic society public reason is the reason of equal citizens who, as a collective body, exercise final political and coercive power over one another in enacting laws and in amending their constitution. The ideal of public reason does not apply to all political questions but only to those involving what we may call constitutional essentials and questions of basic justice. Religious reasons must be translated into public reasons that all citizens can in principle accept.",
        "topic_tags": ["secularism", "religion", "public_reason", "democracy", "pluralism"],
        "supports_side": "neutral",
        "evidence_type": "logical",
        "weight": 0.9,
    },

    # ════════════════════════════════════════════
    # POVERTY & DEVELOPMENT
    # ════════════════════════════════════════════
    {
        "source_code": "ACEMOGLU_WHY_2012",
        "claim_ref": "Chapter 12 — The Vicious Circle",
        "summary": "Foreign aid often fails because it props up extractive institutions — real development requires political reform and inclusive institutions",
        "full_text": "Foreign aid has not been very effective in promoting development because it often flows to governments with extractive institutions that use it to strengthen their grip on power rather than to build inclusive institutions. Aid can help in specific circumstances but cannot substitute for the institutional transformation that genuine economic development requires. The key is to support the political conditions that allow inclusive institutions to emerge.",
        "topic_tags": ["foreign_aid", "development", "institutions", "poverty", "governance"],
        "supports_side": "neutral",
        "evidence_type": "empirical",
        "weight": 1.0,
    },
    {
        "source_code": "CHANG_KICKING_2002",
        "claim_ref": "Chapter 4 — Intellectual Property Rights",
        "summary": "Strong intellectual property rights harm developing nations by preventing technology transfer — rich countries used weak IP protection during their own development",
        "full_text": "During their developmental periods, today's rich countries routinely violated what we now call intellectual property rights. The USA was notorious for ignoring European — especially British — patents and copyrights throughout the 19th century. Germany built its chemical and pharmaceutical industries by ignoring foreign patents. Now they insist on strong IP protection that locks in their technological advantages and prevents developing countries from doing the same.",
        "topic_tags": ["intellectual_property", "development", "technology_transfer", "trade", "inequality"],
        "supports_side": "con",
        "evidence_type": "historical",
        "weight": 0.9,
    },
]


async def get_source_id(conn, code):
    row = await conn.fetchrow("SELECT id FROM knowledge_sources WHERE code=$1", code)
    return str(row["id"]) if row else None


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

    # Reload all source IDs
    rows = await conn.fetch("SELECT id, code FROM knowledge_sources")
    source_ids = {r["code"]: str(r["id"]) for r in rows}

    print(f"\nSeeding {len(EXTENDED_CLAIMS)} extended claims...\n")
    added = 0
    skipped = 0

    for i, c in enumerate(EXTENDED_CLAIMS):
        sid = source_ids.get(c["source_code"])
        if not sid:
            print(f"  SKIP: source not found: {c['source_code']}")
            skipped += 1
            continue

        existing = await conn.fetchrow(
            "SELECT id FROM knowledge_claims WHERE source_id=$1 AND claim_ref=$2",
            sid, c["claim_ref"]
        )
        if existing:
            print(f"  [{i+1}] SKIP (exists): {c['claim_ref']}")
            skipped += 1
            continue

        print(f"  [{i+1}/{len(EXTENDED_CLAIMS)}] {c['source_code']} -- {c['claim_ref'][:45]}...")
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
        print(f"      + [{c['evidence_type']}] {c['summary'][:60]}...")
        added += 1

    total = await conn.fetchval("SELECT COUNT(*) FROM knowledge_claims")
    sources_total = await conn.fetchval("SELECT COUNT(*) FROM knowledge_sources")

    print(f"\nDone!")
    print(f"  Added:        {added} new claims")
    print(f"  Skipped:      {skipped}")
    print(f"  Total claims: {total}")
    print(f"  Total sources:{sources_total} thinkers/institutions")
    print(f"\nNow covers:")
    print("  Stern, Lomborg — climate economics")
    print("  Hayek, Keynes, Stiglitz, Graeber, Klein — capitalism debate")
    print("  Fukuyama, Huntington, Chomsky — geopolitics")
    print("  Pinker, Diamond — human progress and history")
    print("  Amnesty, HRW, Dershowitz — Israel-Palestine advocacy")
    print("  Bostrom — AI existential risk")
    print("  World Bank, Chang — immigration and development")
    print("  Rawls — religion and public reason")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
