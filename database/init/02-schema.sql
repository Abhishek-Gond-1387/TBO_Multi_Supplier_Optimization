CREATE TABLE IF NOT EXISTS suppliers (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    reliability_score REAL NOT NULL DEFAULT 0.5 CHECK (reliability_score BETWEEN 0 AND 1),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS canonical_entities (
    id UUID PRIMARY KEY,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('HOTEL', 'ATTRACTION')),
    name TEXT NOT NULL,
    destination TEXT NOT NULL,
    location GEOGRAPHY(POINT, 4326),
    star_rating REAL,
    amenities JSONB NOT NULL DEFAULT '[]'::jsonb,
    content_embedding VECTOR(384),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS canonical_entities_location_gix
    ON canonical_entities USING GIST (location);
CREATE INDEX IF NOT EXISTS canonical_entities_embedding_hnsw
    ON canonical_entities USING HNSW (content_embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS supplier_listings (
    id BIGSERIAL PRIMARY KEY,
    supplier_id BIGINT NOT NULL REFERENCES suppliers(id),
    canonical_entity_id UUID REFERENCES canonical_entities(id),
    source_id TEXT NOT NULL,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('HOTEL', 'ATTRACTION')),
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    price NUMERIC(12, 2),
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    available BOOLEAN NOT NULL DEFAULT TRUE,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (supplier_id, source_id)
);
CREATE INDEX IF NOT EXISTS supplier_listings_entity_idx
    ON supplier_listings (canonical_entity_id);

CREATE TABLE IF NOT EXISTS match_review_queue (
    id BIGSERIAL PRIMARY KEY,
    left_listing_id BIGINT NOT NULL REFERENCES supplier_listings(id),
    right_listing_id BIGINT NOT NULL REFERENCES supplier_listings(id),
    similarity_score REAL NOT NULL CHECK (similarity_score BETWEEN 0 AND 1),
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    UNIQUE (left_listing_id, right_listing_id)
);
