"""Optional PostgreSQL/PostGIS repository. JSON sample mode stays self-contained."""

from __future__ import annotations

import json
import os
from typing import Any

_pool = None


async def open_pool() -> None:
    global _pool
    import asyncpg

    _pool = await asyncpg.create_pool(
        dsn=os.getenv("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/tbo_inventory"),
        min_size=int(os.getenv("DB_POOL_MIN_SIZE", "2")),
        max_size=int(os.getenv("DB_POOL_MAX_SIZE", "10")),
        command_timeout=float(os.getenv("DB_TIMEOUT_SECONDS", "20")),
    )


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def database_health() -> dict[str, Any]:
    if _pool is None:
        return {"configured": False, "connected": False}
    try:
        async with _pool.acquire() as connection:
            await connection.fetchval("SELECT 1")
            return {"configured": True, "connected": True}
    except Exception as error:
        return {"configured": True, "connected": False, "error": type(error).__name__}


def _json_value(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


async def load_inventory() -> list[dict[str, Any]]:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    hotel_query = """
        SELECT h.id::text AS id, h.name, 'HOTEL' AS entity_type, h.city AS destination,
               h.country_code,
               ST_Y(h.location::geometry) AS latitude, ST_X(h.location::geometry) AS longitude,
               h.star_rating, COALESCE(h.description, '') AS description,
               COALESCE(h.amenities, '[]'::jsonb) AS amenities,
               COALESCE(h.canonical_images, '[]'::jsonb) AS images,
               COALESCE(jsonb_agg(jsonb_build_object(
                   'supplier_name', s.name,
                   'price', r.base_net_rate + r.tax_and_fees,
                   'currency', r.currency,
                   'available', r.is_available,
                   'cancellation_flexible', COALESCE(r.cancellation_policy->>'type' LIKE 'FREE%', FALSE),
                   'reliability_score', s.reliability_score,
                   'meal_plan', r.meal_plan,
                   'payment_terms', r.payment_terms,
                   'cancellation_policy', r.cancellation_policy,
                   'tax_and_fees', r.tax_and_fees
               )) FILTER (WHERE r.id IS NOT NULL), '[]'::jsonb) AS offers
        FROM canonical_hotels h
        LEFT JOIN supplier_hotels sh ON sh.canonical_hotel_id = h.id
        LEFT JOIN suppliers s ON s.id = sh.supplier_id
        LEFT JOIN supplier_rooms r ON r.supplier_hotel_id = sh.id
        GROUP BY h.id
    """
    attraction_query = """
        SELECT c.id::text AS id, c.title AS name, 'ATTRACTION' AS entity_type,
               c.city AS destination, c.country_code, ST_Y(c.location::geometry) AS latitude,
               ST_X(c.location::geometry) AS longitude, NULL::numeric AS star_rating,
               COALESCE(c.description, '') AS description, '[]'::jsonb AS amenities,
               COALESCE(c.canonical_images, '[]'::jsonb) AS images,
               COALESCE(jsonb_agg(jsonb_build_object(
                   'supplier_name', s.name,
                   'price', o.net_price,
                   'currency', o.currency,
                   'available', o.is_available,
                   'cancellation_flexible', COALESCE(o.cancellation_policy->>'type' LIKE 'FREE%', FALSE),
                   'reliability_score', s.reliability_score,
                   'meal_plan', o.meal_included,
                   'payment_terms', o.payment_terms,
                   'cancellation_policy', o.cancellation_policy
               )) FILTER (WHERE o.id IS NOT NULL), '[]'::jsonb) AS offers
        FROM canonical_sightseeing_products c
        LEFT JOIN supplier_sightseeing_products sp ON sp.canonical_sightseeing_id = c.id
        LEFT JOIN suppliers s ON s.id = sp.supplier_id
        LEFT JOIN supplier_sightseeing_offers o ON o.supplier_sightseeing_id = sp.id
        GROUP BY c.id
    """
    async with _pool.acquire() as connection:
        hotels = await connection.fetch(hotel_query)
        attractions = await connection.fetch(attraction_query)
    rows = []
    for row in [*hotels, *attractions]:
        record = dict(row)
        record["amenities"] = _json_value(record["amenities"], [])
        record["images"] = _json_value(record["images"], [])
        record["images"] = [image.get("url", "") if isinstance(image, dict) else image for image in record["images"]]
        record["offers"] = _json_value(record["offers"], [])
        rows.append(record)
    return rows
