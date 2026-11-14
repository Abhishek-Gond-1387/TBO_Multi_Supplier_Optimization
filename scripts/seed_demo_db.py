"""Load source-backed Delhi OSM records into the optional PostgreSQL catalog.

This import creates no supplier, room-rate, availability, or review data.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import asyncpg

ROOT = Path(__file__).resolve().parents[1]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def completeness(values: list[bool]) -> float:
    return round(sum(values) / max(1, len(values)) * 100, 2)


async def main() -> None:
    dsn = os.getenv("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/tbo_inventory")
    snapshot = json.loads((ROOT / "data" / "osm_inventory.json").read_text(encoding="utf-8"))
    connection = await asyncpg.connect(dsn)
    try:
        async with connection.transaction():
            for entity_type, records in (("HOTEL", snapshot.get("hotels", [])), ("ATTRACTION", snapshot.get("attractions", []))):
                for record in records:
                    source_id = record["source_id"]
                    canonical_id = uuid5(NAMESPACE_URL, f"tbo-osm:{source_id}")
                    item_slug = slug(source_id)
                    name = record["name"]
                    city = record.get("city") or "Delhi"
                    country = record.get("country_code") or "IN"
                    latitude, longitude = record["latitude"], record["longitude"]
                    description = record.get("description") or ""
                    amenities = record.get("amenities") or []
                    images = []  # License-checked images are resolved through the enrichment endpoint.
                    if entity_type == "HOTEL":
                        present = [bool(name), bool(city), bool(description), bool(amenities), bool(images), record.get("property_classification") is not None]
                        await connection.execute(
                            """INSERT INTO canonical_hotels
                            (id,name,slug,star_rating,address_street,city,country_code,location,description,amenities,canonical_images,content_quality_score)
                            VALUES($1,$2,$3,$4,$5,$6,$7,ST_SetSRID(ST_MakePoint($8,$9),4326),$10,$11::jsonb,$12::jsonb,$13)
                            ON CONFLICT(slug) DO UPDATE SET name=EXCLUDED.name,star_rating=EXCLUDED.star_rating,
                                location=EXCLUDED.location,description=EXCLUDED.description,amenities=EXCLUDED.amenities,
                                canonical_images=EXCLUDED.canonical_images,content_quality_score=EXCLUDED.content_quality_score,updated_at=NOW()""",
                            canonical_id, name, item_slug, record.get("property_classification", record.get("star_rating")),
                            record.get("street"), city, country, longitude, latitude, description,
                            json.dumps(amenities), json.dumps(images), completeness(present),
                        )
                    else:
                        category = (record.get("source_category") or "OpenStreetMap visitor place")[:64]
                        present = [bool(name), bool(city), bool(description), bool(category), bool(images)]
                        await connection.execute(
                            """INSERT INTO canonical_sightseeing_products
                            (id,title,slug,category,primary_landmark,city,country_code,location,description,canonical_images,content_quality_score)
                            VALUES($1,$2,$3,$4,$2,$5,$6,ST_SetSRID(ST_MakePoint($7,$8),4326),$9,$10::jsonb,$11)
                            ON CONFLICT(slug) DO UPDATE SET title=EXCLUDED.title,category=EXCLUDED.category,
                                location=EXCLUDED.location,description=EXCLUDED.description,
                                canonical_images=EXCLUDED.canonical_images,content_quality_score=EXCLUDED.content_quality_score,updated_at=NOW()""",
                            canonical_id, name, item_slug, category, city, country, longitude, latitude,
                            description, json.dumps(images), completeness(present),
                        )
    finally:
        await connection.close()
    print("Loaded Delhi OpenStreetMap source records. No supplier offers or reviews were created.")


if __name__ == "__main__":
    asyncio.run(main())
