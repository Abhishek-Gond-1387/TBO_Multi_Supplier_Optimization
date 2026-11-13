-- Enable Spatial and Vector Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. Suppliers Registry
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(32) UNIQUE NOT NULL, -- e.g., 'HOTELBEDS', 'VIATOR', 'AGODA', 'DIRECT'
    name VARCHAR(128) NOT NULL,
    api_endpoint VARCHAR(255),
    protocol VARCHAR(16) DEFAULT 'REST_JSON', -- 'REST_JSON', 'XML_SOAP', 'CSV_BATCH'
    reliability_score NUMERIC(5, 4) DEFAULT 0.9500, -- Updated dynamically based on booking success
    avg_response_time_ms INTEGER DEFAULT 250,
    credentials_encrypted JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Canonical Hotels (Consolidated Master Property)
CREATE TABLE canonical_hotels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    star_rating NUMERIC(2, 1) CHECK (star_rating >= 0 AND star_rating <= 5),
    address_street VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    country_code VARCHAR(2) NOT NULL,
    postal_code VARCHAR(32),
    location GEOMETRY(Point, 4326) NOT NULL, -- Spatial Indexing
    description TEXT,
    amenities JSONB DEFAULT '[]'::jsonb, -- e.g. ["wifi", "pool", "spa", "gym", "airport_shuttle"]
    canonical_images JSONB DEFAULT '[]'::jsonb, -- Curated, deduplicated image URLs with quality scores
    content_quality_score NUMERIC(5, 2) DEFAULT 0.00, -- 0 to 100
    embedding vector(384), -- MiniLM-L6-v2 dense vector of (name + city + amenities)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Supplier Raw Hotel Listings (Ingested Staging & Lineage)
CREATE TABLE supplier_hotels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    supplier_hotel_id VARCHAR(128) NOT NULL,
    raw_name VARCHAR(255) NOT NULL,
    raw_address TEXT,
    raw_city VARCHAR(100),
    raw_country VARCHAR(64),
    raw_star_rating NUMERIC(2, 1),
    location GEOMETRY(Point, 4326),
    raw_amenities JSONB DEFAULT '[]'::jsonb,
    raw_images JSONB DEFAULT '[]'::jsonb,
    raw_payload JSONB,
    data_quality_score NUMERIC(5, 2) DEFAULT 0.00,
    canonical_hotel_id UUID REFERENCES canonical_hotels(id) ON DELETE SET NULL,
    match_confidence NUMERIC(5, 4),
    match_status VARCHAR(32) DEFAULT 'PENDING', -- 'AUTO_MATCHED', 'MANUAL_OVERRIDE', 'FLAGGED_REVIEW', 'UNMATCHED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_supplier_hotel UNIQUE (supplier_id, supplier_hotel_id)
);

-- 4. Canonical Room Types (Standardized Category Definitions)
CREATE TABLE canonical_room_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_hotel_id UUID NOT NULL REFERENCES canonical_hotels(id) ON DELETE CASCADE,
    room_class VARCHAR(64) NOT NULL, -- 'Standard', 'Deluxe', 'Executive', 'Suite', 'Villa'
    bed_type VARCHAR(64) NOT NULL, -- 'Single', 'Twin', 'Queen', 'King', 'Multiple'
    view_type VARCHAR(64) DEFAULT 'Standard', -- 'City View', 'Ocean View', 'Garden View', 'Pool View'
    max_occupancy_adults INTEGER DEFAULT 2,
    max_occupancy_children INTEGER DEFAULT 1,
    size_sqm NUMERIC(6, 2),
    amenities JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Supplier Room Listings & Rates (Real-Time Bookable Options)
CREATE TABLE supplier_rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_hotel_id UUID NOT NULL REFERENCES supplier_hotels(id) ON DELETE CASCADE,
    canonical_room_type_id UUID REFERENCES canonical_room_types(id) ON DELETE SET NULL,
    supplier_room_name VARCHAR(255) NOT NULL,
    meal_plan VARCHAR(64) NOT NULL, -- 'RO' (Room Only), 'BB' (Bed & Breakfast), 'HB', 'FB', 'AI' (All Inclusive)
    cancellation_policy JSONB NOT NULL, -- e.g. {"type": "FREE_CANCELLATION", "deadline": "2026-12-01T00:00:00Z"}
    payment_terms VARCHAR(32) DEFAULT 'PAY_NOW', -- 'PAY_NOW', 'PAY_AT_HOTEL'
    base_net_rate NUMERIC(10, 2) NOT NULL,
    tax_and_fees NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    is_available BOOLEAN DEFAULT TRUE,
    allotment INTEGER DEFAULT 5,
    match_confidence NUMERIC(5, 4),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_supplier_room_rate UNIQUE (supplier_hotel_id, supplier_room_name, meal_plan, currency)
);

-- 6. Canonical Sightseeing Products (Consolidated Master Experiences)
CREATE TABLE canonical_sightseeing_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(64) NOT NULL, -- 'Attraction Ticket', 'Day Tour', 'Adventure', 'Cruises', 'Cultural'
    primary_landmark VARCHAR(128),
    city VARCHAR(100) NOT NULL,
    country_code VARCHAR(2) NOT NULL,
    location GEOMETRY(Point, 4326) NOT NULL,
    description TEXT,
    canonical_images JSONB DEFAULT '[]'::jsonb,
    content_quality_score NUMERIC(5, 2) DEFAULT 0.00,
    embedding vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Supplier Sightseeing Listings (Ingested Staging)
CREATE TABLE supplier_sightseeing_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    supplier_product_id VARCHAR(128) NOT NULL,
    raw_title VARCHAR(255) NOT NULL,
    raw_description TEXT,
    location GEOMETRY(Point, 4326),
    canonical_sightseeing_id UUID REFERENCES canonical_sightseeing_products(id) ON DELETE SET NULL,
    match_confidence NUMERIC(5, 4),
    match_status VARCHAR(32) DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_supplier_sightseeing UNIQUE (supplier_id, supplier_product_id)
);

-- 8. Sightseeing Bookable Offers & Inclusions (Differentiating Layer)
CREATE TABLE supplier_sightseeing_offers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_sightseeing_id UUID NOT NULL REFERENCES supplier_sightseeing_products(id) ON DELETE CASCADE,
    variant_name VARCHAR(255) NOT NULL,
    duration_minutes INTEGER NOT NULL,
    has_transfer VARCHAR(32) NOT NULL DEFAULT 'NONE', -- 'NONE', 'SHARED', 'PRIVATE'
    meal_included VARCHAR(32) NOT NULL DEFAULT 'NONE', -- 'NONE', 'BREAKFAST', 'LUNCH', 'DINNER', 'SNACKS'
    access_type VARCHAR(32) NOT NULL DEFAULT 'STANDARD', -- 'STANDARD', 'SKIP_THE_LINE', 'VIP_LOUNGE', 'EARLY_ACCESS'
    guide_language VARCHAR(32) DEFAULT 'ENGLISH',
    cancellation_policy JSONB NOT NULL,
    payment_terms VARCHAR(32) DEFAULT 'PREPAID',
    net_price NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    is_available BOOLEAN DEFAULT TRUE,
    inclusions JSONB DEFAULT '[]'::jsonb,
    exclusions JSONB DEFAULT '[]'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Human Review & Audit Trail (Discrepancies & Low-Confidence Matches)
CREATE TABLE human_review_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(32) NOT NULL, -- 'HOTEL', 'SIGHTSEEING', 'ROOM'
    supplier_entity_id UUID NOT NULL,
    old_canonical_id UUID,
    new_canonical_id UUID,
    reviewer_user_id VARCHAR(64) NOT NULL,
    action VARCHAR(32) NOT NULL, -- 'CONFIRMED', 'REASSIGNED', 'UNLINKED_NEW_CANONICAL'
    review_notes TEXT,
    feature_contributions JSONB, -- Explainability snapshot (e.g. {"name_sim": 0.72, "geo_dist_m": 45})
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. Ranking & Conversion Event Logs
CREATE TABLE ranking_conversion_telemetry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_session_id UUID NOT NULL,
    entity_type VARCHAR(32) NOT NULL, -- 'HOTEL', 'SIGHTSEEING'
    canonical_id UUID NOT NULL,
    selected_supplier_id UUID NOT NULL,
    displayed_position INTEGER NOT NULL,
    ranking_score NUMERIC(8, 4) NOT NULL,
    feature_vector JSONB, -- Ranking weights and signals during calculation
    event_type VARCHAR(32) NOT NULL, -- 'IMPRESSION', 'DETAIL_VIEW', 'BOOKING_INTENT', 'BOOKED'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Spatial & Vector Indexes for Sub-Millisecond Search
CREATE INDEX idx_canonical_hotels_location ON canonical_hotels USING GIST(location);
CREATE INDEX idx_canonical_hotels_embedding ON canonical_hotels USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_canonical_sightseeing_location ON canonical_sightseeing_products USING GIST(location);
CREATE INDEX idx_canonical_sightseeing_embedding ON canonical_sightseeing_products USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_supplier_hotels_canonical ON supplier_hotels(canonical_hotel_id);
CREATE INDEX idx_supplier_rooms_canonical ON supplier_rooms(canonical_room_type_id);
CREATE INDEX idx_supplier_sightseeing_canonical ON supplier_sightseeing_products(canonical_sightseeing_id);
