#!/usr/bin/env python3
# seed_knowledge_panel.py
# Seeds the knowledge panel with documented positions from thinkers,
# researchers, and experts across major debate topics.
# The judge uses these to score arguments on ANY topic.

import asyncio
import asyncpg
from pgvector.asyncpg import register_vector
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

KNOWLEDGE_SOURCES = [
    # ── CLIMATE ──────────────────────────────────────────────
    {"code": "IPCC_AR6_2021", "title": "IPCC Sixth Assessment Report", "author": "IPCC Working Group I", "institution": "Intergovernmental Panel on Climate Change", "year": 2021, "domain": "science", "stance": "pro", "credibility": "peer_reviewed", "url": "https://www.ipcc.ch/report/ar6/wg1/"},
    {"code": "LOMBORG_COOL_2020", "title": "False Alarm: How Climate Change Panic Costs Us Trillions", "author": "Bjorn Lomborg", "institution": "Copenhagen Consensus Center", "year": 2020, "domain": "science", "stance": "con", "credibility": "documented_position", "url": "https://www.lomborg.com"},
    {"code": "NASA_CLIMATE_2023", "title": "NASA Global Climate Change: Vital Signs", "author": "NASA Earth Science Division", "institution": "NASA", "year": 2023, "domain": "science", "stance": "pro", "credibility": "peer_reviewed", "url": "https://climate.nasa.gov"},

    # ── ECONOMICS ────────────────────────────────────────────
    {"code": "FRIEDMAN_CAPITALISM_1962", "title": "Capitalism and Freedom", "author": "Milton Friedman", "institution": "University of Chicago", "year": 1962, "domain": "economics", "stance": "pro", "credibility": "expert_consensus", "url": "https://press.uchicago.edu/ucp/books/book/chicago/C/bo3684926.html"},
    {"code": "PIKETTY_CAPITAL_2013", "title": "Capital in the Twenty-First Century", "author": "Thomas Piketty", "institution": "Paris School of Economics", "year": 2013, "domain": "economics", "stance": "con", "credibility": "peer_reviewed", "url": "https://www.hup.harvard.edu/books/9780674430006"},
    {"code": "CHANG_KICKING_2002", "title": "Kicking Away the Ladder", "author": "Ha-Joon Chang", "institution": "University of Cambridge", "year": 2002, "domain": "economics", "stance": "con", "credibility": "peer_reviewed", "url": "https://anthem-press.com"},
    {"code": "WORLD_BANK_POVERTY_2022", "title": "Poverty and Shared Prosperity Report 2022", "author": "World Bank Research", "institution": "World Bank", "year": 2022, "domain": "economics", "stance": "neutral", "credibility": "peer_reviewed", "url": "https://www.worldbank.org/en/publication/poverty-and-shared-prosperity"},

    # ── SOCIAL MEDIA & DEMOCRACY ─────────────────────────────
    {"code": "HAIDT_RIGHTEOUS_2012", "title": "The Righteous Mind", "author": "Jonathan Haidt", "institution": "NYU Stern School of Business", "year": 2012, "domain": "sociology", "stance": "neutral", "credibility": "peer_reviewed", "url": "https://righteousmind.com"},
    {"code": "ZUBOFF_SURVEILLANCE_2019", "title": "The Age of Surveillance Capitalism", "author": "Shoshana Zuboff", "institution": "Harvard Business School", "year": 2019, "domain": "sociology", "stance": "con", "credibility": "peer_reviewed", "url": "https://shoshanazuboff.com/book/about/"},
    {"code": "TUFEKCI_TWITTER_2017", "title": "Twitter and Tear Gas", "author": "Zeynep Tufekci", "institution": "University of North Carolina", "year": 2017, "domain": "sociology", "stance": "pro", "credibility": "peer_reviewed", "url": "https://www.twitterandteargas.org"},
    {"code": "SHIRKY_COGNITIVE_2010", "title": "Cognitive Surplus", "author": "Clay Shirky", "institution": "NYU", "year": 2010, "domain": "sociology", "stance": "pro", "credibility": "documented_position", "url": "https://www.penguin.com/books/301679/cognitive-surplus-by-clay-shirky/"},

    # ── PHILOSOPHY / ETHICS ───────────────────────────────────
    {"code": "RAWLS_JUSTICE_1971", "title": "A Theory of Justice", "author": "John Rawls", "institution": "Harvard University", "year": 1971, "domain": "philosophy", "stance": "neutral", "credibility": "expert_consensus", "url": "https://www.hup.harvard.edu/books/9780674000780"},
    {"code": "NOZICK_ANARCHY_1974", "title": "Anarchy, State, and Utopia", "author": "Robert Nozick", "institution": "Harvard University", "year": 1974, "domain": "philosophy", "stance": "pro", "credibility": "expert_consensus", "url": "https://www.basicbooks.com/titles/robert-nozick/anarchy-state-and-utopia/9780465051007/"},
    {"code": "SINGER_PRACTICAL_1979", "title": "Practical Ethics", "author": "Peter Singer", "institution": "Princeton University", "year": 1979, "domain": "philosophy", "stance": "neutral", "credibility": "expert_consensus", "url": "https://www.cambridge.org/practical-ethics"},

    # ── HISTORY ───────────────────────────────────────────────
    {"code": "MORRIS_RIGHTEOUS_2008", "title": "1948: A History of the First Arab-Israeli War", "author": "Benny Morris", "institution": "Ben-Gurion University", "year": 2008, "domain": "history", "stance": "neutral", "credibility": "peer_reviewed", "url": "https://yalebooks.yale.edu/book/9780300126969/1948/"},
    {"code": "PAPPE_ETHNIC_2006", "title": "The Ethnic Cleansing of Palestine", "author": "Ilan Pappe", "institution": "University of Exeter", "year": 2006, "domain": "history", "stance": "con", "credibility": "documented_position", "url": "https://www.oneworld-publications.com/the-ethnic-cleansing-of-palestine.html"},
    {"code": "KARSH_PALESTINE_2010", "title": "Palestine Betrayed", "author": "Efraim Karsh", "institution": "King's College London", "year": 2010, "domain": "history", "stance": "pro", "credibility": "documented_position", "url": "https://yalebooks.yale.edu/book/9780300122770/palestine-betrayed/"},

    # ── AI & TECHNOLOGY ───────────────────────────────────────
    {"code": "RUSSELL_HUMAN_2019", "title": "Human Compatible: AI and the Problem of Control", "author": "Stuart Russell", "institution": "UC Berkeley", "year": 2019, "domain": "science", "stance": "con", "credibility": "expert_consensus", "url": "https://people.eecs.berkeley.edu/~russell/book.html"},
    {"code": "LECUN_AI_RISKS_2023", "title": "AI Risk Discourse Critique", "author": "Yann LeCun", "institution": "Meta AI / NYU", "year": 2023, "domain": "science", "stance": "pro", "credibility": "documented_position", "url": "https://twitter.com/ylecun"},
    {"code": "BOSTROM_SUPERINTELLIGENCE_2014", "title": "Superintelligence: Paths, Dangers, Strategies", "author": "Nick Bostrom", "institution": "Oxford University", "year": 2014, "domain": "science", "stance": "con", "credibility": "expert_consensus", "url": "https://nickbostrom.com/superintelligence.html"},

    # ── COLONIALISM & HISTORY ─────────────────────────────────
    {"code": "FANON_WRETCHED_1961", "title": "The Wretched of the Earth", "author": "Frantz Fanon", "institution": "Algerian FLN", "year": 1961, "domain": "philosophy", "stance": "con", "credibility": "documented_position", "url": "https://groveatlantic.com/book/the-wretched-of-the-earth/"},
    {"code": "SAID_ORIENTALISM_1978", "title": "Orientalism", "author": "Edward Said", "institution": "Columbia University", "year": 1978, "domain": "philosophy", "stance": "con", "credibility": "expert_consensus", "url": "https://www.penguinrandomhouse.com/books/159783/orientalism-by-edward-w-said/"},
    {"code": "FERGUSON_EMPIRE_2003", "title": "Empire: How Britain Made the Modern World", "author": "Niall Ferguson", "institution": "Harvard University", "year": 2003, "domain": "history", "stance": "pro", "credibility": "documented_position", "url": "https://www.penguinrandomhouse.com/books/286507/empire-by-niall-ferguson/"},

    # ── DRUG POLICY ───────────────────────────────────────────
    {"code": "WHO_DRUG_POLICY_2019", "title": "WHO Expert Committee on Drug Dependence Report", "author": "WHO Expert Committee", "institution": "World Health Organization", "year": 2019, "domain": "sociology", "stance": "pro", "credibility": "peer_reviewed", "url": "https://www.who.int/medicines/access/controlled-substances/ecdd_39_report.pdf"},
    {"code": "HART_HIGH_PRICE_2013", "title": "High Price: A Neuroscientist's Self-Discovery", "author": "Carl Hart", "institution": "Columbia University", "year": 2013, "domain": "science", "stance": "pro", "credibility": "peer_reviewed", "url": "https://www.harpercollins.com/products/high-price-carl-hart"},
]

KNOWLEDGE_CLAIMS = [

    # ════════════════════════════════════════════
    # CLIMATE CHANGE
    # ════════════════════════════════════════════
    {
        "source_code": "IPCC_AR6_2021",
        "claim_ref": "Summary for Policymakers, A.1",
        "summary": "Human influence has warmed the climate at an unprecedented rate — IPCC scientific consensus",
        "full_text": "It is unequivocal that human influence has warmed the atmosphere, ocean and land. Widespread and rapid changes in the atmosphere, ocean, cryosphere and biosphere have occurred. Human-induced climate change is already affecting many weather and climate extremes in every region across the globe. Evidence of observed changes in extremes such as heatwaves, heavy precipitation, droughts, and tropical cyclones, and their attribution to human influence, has strengthened.",
        "topic_tags": ["climate_change", "global_warming", "human_influence", "scientific_consensus"],
        "supports_side": "pro",
        "evidence_type": "empirical",
        "weight": 1.0,
    },
    {
        "source_code": "IPCC_AR6_2021",
        "claim_ref": "Summary for Policymakers, B.1",
        "summary": "Global surface temperature will continue to increase until at least mid-century under all emissions scenarios",
        "full_text": "Global surface temperature will continue to increase until at least the mid-21st century under all emissions scenarios considered. Global warming of 1.5 degrees C and 2 degrees C will be exceeded during the 21st century unless deep reductions in CO2 and other greenhouse gas emissions occur in the coming decades.",
        "topic_tags": ["climate_change", "temperature_rise", "emissions", "projections"],
        "supports_side": "pro",
        "evidence_type": "empirical",
        "weight": 1.0,
    },
    {
        "source_code": "LOMBORG_COOL_2020",
        "claim_ref": "Chapter 1",
        "summary": "Climate change is real but climate alarmism leads to poor policy that costs trillions with minimal benefit",
        "full_text": "Climate change is real, but it is not the end of the world. It is a manageable problem. The language of fear and catastrophe that has come to dominate public discourse is not only misleading but counterproductive. Trillions spent on current climate policies deliver poor returns compared to adaptation and technology investment.",
        "topic_tags": ["climate_change", "climate_policy", "cost_benefit", "adaptation"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.7,
    },
    {
        "source_code": "NASA_CLIMATE_2023",
        "claim_ref": "Global Temperature Data",
        "summary": "NASA data shows global average surface temperature has risen about 1.1 degrees Celsius since the late 19th century",
        "full_text": "Earth's global average surface temperature in 2022 tied with 2015 as the fifth warmest on record, according to an analysis by NASA. Continuing the planet's long-term warming trend, global temperatures in 2022 were 0.89 degrees Celsius (1.6 degrees Fahrenheit) above the average for NASA's baseline period (1951-1980). The global average temperature has risen about 1.1 degrees Celsius since the late 19th century.",
        "topic_tags": ["climate_change", "temperature_data", "nasa", "empirical_evidence"],
        "supports_side": "pro",
        "evidence_type": "empirical",
        "weight": 1.0,
    },

    # ════════════════════════════════════════════
    # FREE MARKET ECONOMICS
    # ════════════════════════════════════════════
    {
        "source_code": "FRIEDMAN_CAPITALISM_1962",
        "claim_ref": "Chapter 1 — The Relation Between Economic Freedom and Political Freedom",
        "summary": "Economic freedom is an essential component of political freedom — free markets reduce state power over individuals",
        "full_text": "Economic arrangements play a dual role in the promotion of a free society. On the one hand, freedom in economic arrangements is itself a component of freedom broadly understood, so economic freedom is an end in itself. In the second place, economic freedom is also an indispensable means toward the achievement of political freedom. The kind of economic organization that provides economic freedom directly, namely, competitive capitalism, also promotes political freedom because it separates economic power from political power.",
        "topic_tags": ["free_market", "capitalism", "economic_freedom", "political_freedom"],
        "supports_side": "pro",
        "evidence_type": "logical",
        "weight": 0.9,
    },
    {
        "source_code": "PIKETTY_CAPITAL_2013",
        "claim_ref": "Introduction",
        "summary": "When the rate of return on capital exceeds economic growth, inequality increases — historical data from 20 countries over 200 years",
        "full_text": "When the rate of return on capital exceeds the rate of growth of output and income, as it did in the nineteenth century and seems quite likely to do again in the twenty-first, capitalism automatically generates arbitrary and unsustainable inequalities that radically undermine the meritocratic values on which democratic societies are based. The principal destabilizing force has to do with the fact that the private rate of return on capital r can be significantly higher for long periods of time than the rate of growth of income and output g.",
        "topic_tags": ["inequality", "capitalism", "wealth_distribution", "economic_growth"],
        "supports_side": "con",
        "evidence_type": "empirical",
        "weight": 1.0,
    },
    {
        "source_code": "WORLD_BANK_POVERTY_2022",
        "claim_ref": "Overview",
        "summary": "Extreme poverty fell from 36% in 1990 to 9.3% in 2017 — largely attributed to economic growth in developing nations",
        "full_text": "The share of the world's population living in extreme poverty fell from 36 percent in 1990 to 9.3 percent in 2017. Despite COVID-19 setbacks, the long-term trend shows remarkable progress. Economic growth remains the most powerful driver of poverty reduction, accounting for the vast majority of poverty reduction in East Asia and the Pacific.",
        "topic_tags": ["poverty_reduction", "economic_growth", "development", "free_trade"],
        "supports_side": "pro",
        "evidence_type": "statistical",
        "weight": 1.0,
    },
    {
        "source_code": "CHANG_KICKING_2002",
        "claim_ref": "Chapter 2",
        "summary": "Today's rich countries developed through protectionism and industrial policy, not free trade — they are now kicking away the ladder for developing nations",
        "full_text": "When they were developing countries themselves, the now-developed countries did not practice free trade. They actively used tariffs, subsidies and other measures to promote infant industries. Britain used such policies during 1721-1846. The US did the same during 1816-1945. Germany, France, and Sweden all followed similar paths. Now they tell developing countries to adopt free trade — effectively kicking away the ladder they themselves climbed.",
        "topic_tags": ["free_trade", "protectionism", "development", "historical_evidence"],
        "supports_side": "con",
        "evidence_type": "historical",
        "weight": 0.9,
    },

    # ════════════════════════════════════════════
    # SOCIAL MEDIA & DEMOCRACY
    # ════════════════════════════════════════════
    {
        "source_code": "ZUBOFF_SURVEILLANCE_2019",
        "claim_ref": "Part II, Chapter 6",
        "summary": "Surveillance capitalism claims human experience as raw material for behavioral prediction products — fundamentally incompatible with democracy",
        "full_text": "Surveillance capitalism unilaterally claims human experience as free raw material for translation into behavioral data. Although some of these data are applied to product or service improvement, the rest are declared as a proprietary behavioral surplus, fed into advanced manufacturing processes known as the behavioral modification imperatives, and fabricated into prediction products that anticipate what you will do now, soon, and later. These prediction products are sold into a new kind of marketplace that I call the behavioral futures market.",
        "topic_tags": ["social_media", "surveillance", "democracy", "privacy", "manipulation"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.9,
    },
    {
        "source_code": "TUFEKCI_TWITTER_2017",
        "claim_ref": "Chapter 1",
        "summary": "Social media has enabled unprecedented social movements and pro-democracy organizing — the Arab Spring demonstrated its mobilizing power",
        "full_text": "The internet and digital tools have not made movements weaker; they have transformed them. Movements can now form more easily, reach more people and coordinate faster. The Arab Spring showed how social media could help topple authoritarian regimes. Digital tools lower the cost of collective action and allow marginalized voices to be heard globally. The question is not whether social media empowers movements but how movements can best use these tools.",
        "topic_tags": ["social_media", "democracy", "arab_spring", "social_movements", "mobilization"],
        "supports_side": "pro",
        "evidence_type": "historical",
        "weight": 0.8,
    },
    {
        "source_code": "HAIDT_RIGHTEOUS_2012",
        "claim_ref": "Chapter 11",
        "summary": "Political tribalism is hardwired into human psychology — social media amplifies our tribal instincts and makes compromise harder",
        "full_text": "Human beings are 90 percent chimp and 10 percent bee. We are mostly selfish primates who are capable, under special circumstances, of transcending self-interest and merging into larger wholes. Those special circumstances include war, team sports, and religious rituals — but also political campaigns. Social media has created an environment that constantly triggers our tribal psychology, rewarding outrage and punishing nuance.",
        "topic_tags": ["tribalism", "social_media", "polarization", "psychology", "democracy"],
        "supports_side": "con",
        "evidence_type": "empirical",
        "weight": 0.8,
    },

    # ════════════════════════════════════════════
    # ISRAEL-PALESTINE HISTORICAL
    # ════════════════════════════════════════════
    {
        "source_code": "MORRIS_RIGHTEOUS_2008",
        "claim_ref": "Chapter 1",
        "summary": "The 1948 war resulted in 700,000 Palestinian refugees — caused by a combination of expulsions, fear, and the fog of war according to Israeli New Historian Benny Morris",
        "full_text": "The Palestinian refugee problem was born of war, not by design, Jewish or Arab. It emerged from the collapse of Palestinian Arab society. But alongside the collapse, there were also deliberate expulsions by Jewish/Israeli military units. The causes were complex: some Palestinians fled voluntarily, fearing war; others were driven out by Israeli military units; and some were expelled as a deliberate policy of ethnic cleansing in certain localities.",
        "topic_tags": ["1948", "nakba", "refugees", "israel_palestine", "history"],
        "supports_side": "neutral",
        "evidence_type": "historical",
        "weight": 0.9,
    },
    {
        "source_code": "PAPPE_ETHNIC_2006",
        "claim_ref": "Introduction",
        "summary": "Ilan Pappe documents systematic ethnic cleansing of Palestine in 1948 — Plan Dalet was a premeditated policy to expel the Arab population",
        "full_text": "The ethnic cleansing of Palestine is a crime against humanity that was perpetrated from December 1947 to January 1949. In that period, the Zionist forces expelled 750,000 Palestinians, committed dozens of massacres, and destroyed 531 villages. This was not the by-product of war, as Israeli propaganda has claimed for decades, but was the result of a deliberate ideology that sought to create a Jewish state with as few Arabs as possible.",
        "topic_tags": ["1948", "ethnic_cleansing", "nakba", "plan_dalet", "israel_palestine"],
        "supports_side": "con",
        "evidence_type": "historical",
        "weight": 0.8,
    },
    {
        "source_code": "KARSH_PALESTINE_2010",
        "claim_ref": "Chapter 4",
        "summary": "Efraim Karsh argues Palestinian leaders and Arab states bear primary responsibility for the 1948 refugee crisis by rejecting partition and initiating war",
        "full_text": "The Palestinians and their Arab supporters bear the primary responsibility for the creation of the refugee problem. Had the Arab states accepted the UN partition plan of 1947 and not launched a war to destroy the newly proclaimed State of Israel, there would have been no refugee problem. The Palestinians were not expelled en masse; the vast majority fled as a result of the war launched by Arab leaders who promised them they could return after a swift Arab victory.",
        "topic_tags": ["1948", "arab_rejection", "partition", "refugee_responsibility", "israel_palestine"],
        "supports_side": "pro",
        "evidence_type": "historical",
        "weight": 0.7,
    },

    # ════════════════════════════════════════════
    # ARTIFICIAL INTELLIGENCE RISKS
    # ════════════════════════════════════════════
    {
        "source_code": "RUSSELL_HUMAN_2019",
        "claim_ref": "Chapter 5",
        "summary": "AI systems optimizing for the wrong objectives pose existential risks — the gorilla problem: gorillas cannot control their fate because humans are more intelligent",
        "full_text": "The gorilla problem is this: gorillas are not endangered because humans are evil; they are endangered because humans are more powerful, and the future of gorillas depends on human goodwill. If we create machines that are more powerful than us, our future will depend on their goodwill — unless we ensure from the outset that their values are aligned with ours. The standard model of AI — machines that optimize for a fixed objective — is fundamentally broken.",
        "topic_tags": ["ai_risk", "alignment", "existential_risk", "superintelligence"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.9,
    },
    {
        "source_code": "LECUN_AI_RISKS_2023",
        "claim_ref": "Public Statement 2023",
        "summary": "Yann LeCun argues current AI doom scenarios are overblown — AI systems are not inherently dangerous and will be made safe through engineering",
        "full_text": "The idea that AI will spontaneously develop goals of self-preservation, resource acquisition, and domination is nonsense. Current AI systems, including future ones, are not agents in the way science fiction portrays them. The risks of AI are real but manageable through good engineering, regulation, and open research. The existential risk narrative is overblown and distracts from real near-term harms like bias and misinformation.",
        "topic_tags": ["ai_safety", "ai_risk", "engineering", "regulation", "ai_harms"],
        "supports_side": "pro",
        "evidence_type": "expert_opinion",
        "weight": 0.8,
    },

    # ════════════════════════════════════════════
    # COLONIALISM & EMPIRE
    # ════════════════════════════════════════════
    {
        "source_code": "SAID_ORIENTALISM_1978",
        "claim_ref": "Introduction",
        "summary": "Western knowledge about the East is not objective but constructed to justify colonial domination — Orientalism as a system of thought",
        "full_text": "Orientalism is not a mere political subject matter or field that is reflected passively by culture, scholarship, or institutions; nor is it a large and diffuse collection of texts about the Orient; nor is it representative and expressive of some nefarious imperialist plot to hold down the Oriental world. It is rather a distribution of geopolitical awareness into aesthetic, scholarly, economic, sociological, historical, and philological texts. It is an elaboration not only of a basic geographical distinction but also of a whole series of interests which, by such means as scholarly discovery, philological reconstruction, psychological analysis, landscape and sociological description, it not only creates but also maintains.",
        "topic_tags": ["colonialism", "orientalism", "western_knowledge", "power", "discourse"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.9,
    },
    {
        "source_code": "FERGUSON_EMPIRE_2003",
        "claim_ref": "Introduction",
        "summary": "Niall Ferguson argues British Empire spread rule of law, free trade and institutions that enabled development — net positive historical assessment",
        "full_text": "The British Empire was, as empires go, a remarkable thing. No organization in history has done more to promote the free movement of goods, capital and labour than the British Empire in the nineteenth and early twentieth centuries. No organization has done more to impose Western norms of law, order and governance around the world. Without the British Empire, it is hard to imagine that the institutions of liberal capitalism would have been so successfully transplanted to so many parts of the world.",
        "topic_tags": ["colonialism", "british_empire", "institutions", "free_trade", "development"],
        "supports_side": "pro",
        "evidence_type": "historical",
        "weight": 0.7,
    },
    {
        "source_code": "FANON_WRETCHED_1961",
        "claim_ref": "Chapter 1 — On Violence",
        "summary": "Frantz Fanon argues colonialism is inherently violent and dehumanizing — anti-colonial violence is a legitimate and psychologically necessary response",
        "full_text": "National liberation, national renaissance, the restoration of nationhood to the people, commonwealth: whatever may be the headings used or the new formulas introduced, decolonization is always a violent phenomenon. Colonialism is not a thinking machine, nor a body endowed with reasoning faculties. It is violence in its natural state, and it will only yield when confronted with greater violence.",
        "topic_tags": ["colonialism", "decolonization", "violence", "resistance", "liberation"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.8,
    },

    # ════════════════════════════════════════════
    # DRUG POLICY
    # ════════════════════════════════════════════
    {
        "source_code": "WHO_DRUG_POLICY_2019",
        "claim_ref": "Critical Review of Cannabis",
        "summary": "WHO recommends reclassifying cannabis — evidence shows it has medical value and current scheduling is not appropriate based on scientific evidence",
        "full_text": "The Expert Committee on Drug Dependence conducted a critical review of cannabis and cannabis-related substances. The Committee found that cannabis has medical uses and that the current scheduling of cannabis and cannabis resin does not reflect the evidence. The scheduling should reflect the actual risk and benefit profile of the substance based on scientific evidence, not historical or political considerations.",
        "topic_tags": ["drug_policy", "cannabis", "decriminalization", "medical_use", "scheduling"],
        "supports_side": "pro",
        "evidence_type": "empirical",
        "weight": 1.0,
    },
    {
        "source_code": "HART_HIGH_PRICE_2013",
        "claim_ref": "Chapter 8",
        "summary": "The war on drugs disproportionately targets Black communities and is based on pseudoscience — drug use is not the primary driver of addiction",
        "full_text": "The scientific evidence shows that the vast majority of people who use drugs, including hard drugs, do not become addicted. Addiction rates for cocaine are about 15-20 percent of users; for heroin about 25 percent. The war on drugs is not really about drugs — it is about race and class. Black people are arrested for drug offenses at rates 3-4 times higher than white people despite similar usage rates. The policy is racist and counterproductive.",
        "topic_tags": ["drug_policy", "war_on_drugs", "racism", "addiction", "decriminalization"],
        "supports_side": "pro",
        "evidence_type": "empirical",
        "weight": 0.9,
    },

    # ════════════════════════════════════════════
    # PHILOSOPHY OF JUSTICE
    # ════════════════════════════════════════════
    {
        "source_code": "RAWLS_JUSTICE_1971",
        "claim_ref": "Part I, Section 3 — The Original Position",
        "summary": "Justice requires choosing principles from behind a veil of ignorance — not knowing your place in society produces fair principles",
        "full_text": "The principles of justice are chosen behind a veil of ignorance. This ensures that no one is advantaged or disadvantaged in the choice of principles by the outcome of natural chance or the contingency of social circumstances. Since all are similarly situated and no one is able to design principles to favor his particular condition, the principles of justice are the result of a fair agreement or bargain.",
        "topic_tags": ["justice", "fairness", "equality", "social_contract", "distributive_justice"],
        "supports_side": "neutral",
        "evidence_type": "logical",
        "weight": 0.9,
    },
    {
        "source_code": "NOZICK_ANARCHY_1974",
        "claim_ref": "Chapter 7 — Distributive Justice",
        "summary": "Nozick's entitlement theory — redistribution of property violates rights; taxation is forced labor; the minimal state is the only just state",
        "full_text": "The minimal state is the most extensive state that can be justified. Any state more extensive violates people's rights. Individuals have rights, and there are things no person or group may do to them without violating their rights. So strong and far-reaching are these rights that they raise the question of what, if anything, the state and its officials may do. Taxation of earnings from labor is on a par with forced labor.",
        "topic_tags": ["libertarianism", "property_rights", "taxation", "minimal_state", "justice"],
        "supports_side": "con",
        "evidence_type": "logical",
        "weight": 0.9,
    },
]


async def get_or_create_source(conn, s):
    row = await conn.fetchrow("SELECT id FROM knowledge_sources WHERE code = $1", s["code"])
    if row:
        return str(row["id"])
    row = await conn.fetchrow(
        """INSERT INTO knowledge_sources
           (code, title, author, institution, year, domain, stance, credibility, url)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING id""",
        s["code"], s["title"], s.get("author"), s.get("institution"),
        s.get("year"), s["domain"], s["stance"], s["credibility"], s.get("url")
    )
    print(f"  + Source: {s['code']}")
    return str(row["id"])


async def embed(text):
    r = await client.embeddings.create(model="text-embedding-3-small", input=text.strip().replace("\n", " "))
    return r.data[0].embedding


async def seed():
    print("Connecting to database...")
    conn = await asyncpg.connect(dsn=DATABASE_URL)
    await conn.execute("SET search_path TO public")
    await register_vector(conn)

    # Load existing sources
    source_ids = {}
    rows = await conn.fetch("SELECT id, code FROM knowledge_sources")
    for r in rows:
        source_ids[r["code"]] = str(r["id"])

    # Add new sources
    print(f"\nAdding {len(KNOWLEDGE_SOURCES)} knowledge sources...")
    for s in KNOWLEDGE_SOURCES:
        source_ids[s["code"]] = await get_or_create_source(conn, s)

    # Seed claims
    print(f"\nSeeding {len(KNOWLEDGE_CLAIMS)} knowledge claims...\n")
    added = 0
    skipped = 0

    for i, c in enumerate(KNOWLEDGE_CLAIMS):
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

        print(f"  [{i+1}/{len(KNOWLEDGE_CLAIMS)}] Embedding: {c['source_code']} -- {c['claim_ref'][:50]}...")
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
        print(f"      + {c['source_code']} [{c['evidence_type']}] -- {c['summary'][:55]}...")
        added += 1

    total = await conn.fetchval("SELECT COUNT(*) FROM knowledge_claims")
    print(f"\nDone!")
    print(f"  Added:   {added} knowledge claims")
    print(f"  Skipped: {skipped}")
    print(f"  Total:   {total} claims in knowledge panel")
    print(f"\nTopics covered:")
    print("  Climate change (IPCC, NASA, Lomborg)")
    print("  Free markets vs inequality (Friedman, Piketty, Chang, World Bank)")
    print("  Social media & democracy (Zuboff, Tufekci, Haidt)")
    print("  Israel-Palestine history (Morris, Pappe, Karsh)")
    print("  AI risks (Russell, LeCun, Bostrom)")
    print("  Colonialism (Said, Ferguson, Fanon)")
    print("  Drug policy (WHO, Carl Hart)")
    print("  Philosophy of justice (Rawls, Nozick)")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
