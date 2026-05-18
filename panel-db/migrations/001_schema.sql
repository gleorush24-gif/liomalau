-- ═══════════════════════════════════════════════════════════════
--  lioMalau — Panel Judge Database Schema
--  Runs automatically on first `docker-compose up`
-- ═══════════════════════════════════════════════════════════════

-- pgvector lets us store AI embeddings (1536-float vectors)
-- alongside regular text so we can do semantic search later
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── 1. LEGAL SOURCES ────────────────────────────────────────
--  Every ruling the judge can cite must trace back to a source.
CREATE TABLE legal_sources (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code        TEXT UNIQUE NOT NULL,   -- e.g. 'UNSC_RES_242'
    title       TEXT NOT NULL,          -- e.g. 'UN Security Council Resolution 242'
    body        TEXT NOT NULL,          -- 'UN Security Council'
    year        INT,
    category    TEXT NOT NULL,          -- 'binding' | 'non_binding' | 'treaty'
    url         TEXT,                   -- official document URL
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── 2. LEGAL PRECEDENTS ─────────────────────────────────────
--  Individual articles, clauses, or rulings extracted from sources.
--  These are the atomic units the judge scores against.
CREATE TABLE precedents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id       UUID REFERENCES legal_sources(id) ON DELETE CASCADE,
    article_ref     TEXT,               -- e.g. 'Article 49, Geneva Convention IV'
    summary         TEXT NOT NULL,      -- plain-English summary (for display)
    full_text       TEXT NOT NULL,      -- exact legal text
    topic_tags      TEXT[],             -- e.g. {'occupation', 'civilian_protection'}
    weight          NUMERIC(3,2) DEFAULT 1.0,  -- 1.0 = binding, 0.5 = advisory
    embedding       vector(1536),       -- AI embedding for semantic search
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast semantic search (cosine similarity)
CREATE INDEX precedents_embedding_idx
    ON precedents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ── 3. DEBATE SESSIONS ──────────────────────────────────────
CREATE TABLE sessions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title       TEXT,                   -- e.g. 'Gaza ceasefire arguments – round 1'
    status      TEXT DEFAULT 'active',  -- 'active' | 'completed' | 'archived'
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    ended_at    TIMESTAMPTZ
);

-- ── 4. PARTIES ──────────────────────────────────────────────
--  A session has two (or more) parties — each has a position label.
CREATE TABLE parties (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id  UUID REFERENCES sessions(id) ON DELETE CASCADE,
    label       TEXT NOT NULL,          -- e.g. 'Party A', or a position name
    description TEXT,
    score       NUMERIC(6,2) DEFAULT 0, -- running score
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── 5. ARGUMENTS ────────────────────────────────────────────
--  Each submitted argument, with its AI-parsed claim and evidence links.
CREATE TABLE arguments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID REFERENCES sessions(id) ON DELETE CASCADE,
    party_id        UUID REFERENCES parties(id) ON DELETE CASCADE,
    raw_text        TEXT NOT NULL,      -- what the party submitted
    parsed_claim    TEXT,               -- AI-extracted core claim
    round           INT DEFAULT 1,
    embedding       vector(1536),       -- for semantic matching to precedents
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 6. VERDICTS ─────────────────────────────────────────────
--  For each argument, the judge issues a verdict with citations.
CREATE TABLE verdicts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    argument_id     UUID REFERENCES arguments(id) ON DELETE CASCADE,
    precedent_id    UUID REFERENCES precedents(id),
    stance          TEXT NOT NULL,      -- 'supports' | 'contradicts' | 'inconclusive'
    score_delta     NUMERIC(5,2),       -- points awarded/deducted to that party
    explanation     TEXT,               -- plain-English ruling explanation
    confidence      NUMERIC(3,2),       -- 0.0–1.0 AI confidence
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 7. COUNTER ARGUMENTS ────────────────────────────────────
--  AI-generated rebuttals mapped to the original argument.
CREATE TABLE counter_arguments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    argument_id     UUID REFERENCES arguments(id) ON DELETE CASCADE,
    generated_text  TEXT NOT NULL,
    source_refs     TEXT[],             -- precedent codes cited
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── SEED: legal source examples (enough to test the system) ──
INSERT INTO legal_sources (code, title, body, year, category, url) VALUES
  ('UNSC_RES_242',  'UN Security Council Resolution 242',             'UN Security Council', 1967, 'binding',     'https://undocs.org/S/RES/242(1967)'),
  ('UNSC_RES_2334', 'UN Security Council Resolution 2334',            'UN Security Council', 2016, 'binding',     'https://undocs.org/S/RES/2334(2016)'),
  ('GC_IV_1949',    'Geneva Convention IV — Civilian Protection',     'ICRC',                1949, 'treaty',      'https://ihl-databases.icrc.org/gc4'),
  ('ICC_ROME_1998', 'Rome Statute of the ICC',                        'ICC',                 1998, 'treaty',      'https://www.icc-cpi.int/rome-statute'),
  ('UNGA_181',      'UN General Assembly Resolution 181 (Partition)', 'UN General Assembly', 1947, 'non_binding', 'https://undocs.org/A/RES/181(II)'),
  ('UDHR_1948',     'Universal Declaration of Human Rights',          'UN General Assembly', 1948, 'non_binding', 'https://www.un.org/en/about-us/universal-declaration-of-human-rights'),
  ('ICCPR_1966',    'International Covenant on Civil and Political Rights', 'UN',             1966, 'treaty',      'https://www.ohchr.org/en/instruments-mechanisms/instruments/international-covenant-civil-and-political-rights');
