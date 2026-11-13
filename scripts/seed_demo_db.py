"""Idempotently load the bundled sample inventory into PostgreSQL/PostGIS."""

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


async def main() -> None:
    dsn = os.getenv("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/tbo_inventory")
    rows = json.loads((ROOT / "data" / "sample_inventory.json").read_text(encoding="utf-8"))
    connection = await asyncpg.connect(dsn)
    try:
        async with connection.transaction():
            for item in rows:
                canonical_id = uuid5(NAMESPACE_URL, f"tbo-demo:{item['id']}")
                if item["entity_type"] == "HOTEL":
                    await connection.execute(
                        """INSERT INTO canonical_hotels
                        (id,name,slug,star_rating,address_street,city,country_code,location,description,amenities,canonical_images,content_quality_score)
                        VALUES($1,$2,$3,$4,$5,$6,'AE',ST_SetSRID(ST_MakePoint($7,$8),4326),$9,$10::jsonb,$11::jsonb,$12)
                        ON CONFLICT(slug) DO UPDATE SET name=EXCLUDED.name,star_rating=EXCLUDED.star_rating,
                            location=EXCLUDED.location,description=EXCLUDED.description,amenities=EXCLUDED.amenities,
                            canonical_images=EXCLUDED.canonical_images,updated_at=NOW()""",
                        canonical_id, item["name"], slug(item["id"]), item.get("star_rating"), None,
                        item["destination"], item["longitude"], item["latitude"], item.get("description", ""),
                        json.dumps(item.get("amenities", [])), json.dumps(item.get("images", [])), 75.0,
                    )
                    for offer in item.get("offers", []):
                        supplier_code = slug(offer["supplier_name"]).replace("-", "_").upper()[:32]
                        supplier_id = await connection.fetchval(
                            """INSERT INTO suppliers(code,name,reliability_score) VALUES($1,$2,$3)
                               ON CONFLICT(code) DO UPDATE SET name=EXCLUDED.name,reliability_score=EXCLUDED.reliability_score
                               RETURNING id""",
                            supplier_code, offer["supplier_name"], offer.get("reliability_score", 0.75),
                        )
                        source_id = f"sample:{item['id']}:{supplier_code}"
                        hotel_id = await connection.fetchval(
                            """INSERT INTO supplier_hotels
                               (supplier_id,supplier_hotel_id,raw_name,raw_city,raw_country,raw_star_rating,
                                location,raw_amenities,raw_payload,data_quality_score,canonical_hotel_id,
                                match_confidence,match_status)
                               VALUES($1,$2,$3,$4,'AE',$5,ST_SetSRID(ST_MakePoint($6,$7),4326),$8::jsonb,
                                      $9::jsonb,75,$10,1.0,'AUTO_MATCHED')
                               ON CONFLICT(supplier_id,supplier_hotel_id) DO UPDATE SET
                                 canonical_hotel_id=EXCLUDED.canonical_hotel_id,raw_payload=EXCLUDED.raw_payload,
                                 match_confidence=1.0,match_status='AUTO_MATCHED',updated_at=NOW()
                               RETURNING id""",
                            supplier_id, source_id, item["name"], item["destination"], item.get("star_rating"),
                            item["longitude"], item["latitude"], json.dumps(item.get("amenities", [])),
                            json.dumps(item), canonical_id,
                        )
                        policy = {"type": "FREE_CANCELLATION" if offer.get("cancellation_flexible") else "NON_REFUNDABLE"}
                        await connection.execute(
                            """INSERT INTO supplier_rooms
                               (supplier_hotel_id,supplier_room_name,meal_plan,cancellation_policy,payment_terms,
                                base_net_rate,tax_and_fees,currency,is_available,allotment,match_confidence)
                               VALUES($1,'Standard Room','RO',$2::jsonb,'PAY_NOW',$3,0,$4,$5,5,1.0)
                               ON CONFLICT(supplier_hotel_id,supplier_room_name,meal_plan,currency)
                               DO UPDATE SET base_net_rate=EXCLUDED.base_net_rate,
                                 cancellation_policy=EXCLUDED.cancellation_policy,is_available=EXCLUDED.is_available,
                                 updated_at=NOW()""",
                            hotel_id, json.dumps(policy), offer["price"], offer.get("currency", "USD"), offer.get("available", True),
                        )
                else:
                    await connection.execute(
                        """INSERT INTO canonical_sightseeing_products
                           (id,title,slug,category,primary_landmark,city,country_code,location,description,canonical_images,content_quality_score)
                           VALUES($1,$2,$3,'Attraction Ticket',$2,$4,'AE',ST_SetSRID(ST_MakePoint($5,$6),4326),$7,$8::jsonb,65)
                           ON CONFLICT(slug) DO UPDATE SET title=EXCLUDED.title,location=EXCLUDED.location,
                             description=EXCLUDED.description,updated_at=NOW()""",
                        canonical_id, item["name"], slug(item["id"]), item["destination"],
                        item["longitude"], item["latitude"], item.get("description", ""), json.dumps(item.get("images", [])),
                    )
                    supplier_id = await connection.fetchval(
                        """INSERT INTO suppliers(code,name) VALUES('OPEN_DATA','Open data sample')
                           ON CONFLICT(code) DO UPDATE SET name=EXCLUDED.name RETURNING id"""
                    )
                    await connection.execute(
                        """INSERT INTO supplier_sightseeing_products
                           (supplier_id,supplier_product_id,raw_title,raw_description,location,canonical_sightseeing_id,match_confidence,match_status)
                           VALUES($1,$2,$3,$4,ST_SetSRID(ST_MakePoint($5,$6),4326),$7,1.0,'AUTO_MATCHED')
                           ON CONFLICT(supplier_id,supplier_product_id) DO UPDATE SET
                             canonical_sightseeing_id=EXCLUDED.canonical_sightseeing_id,
                             raw_description=EXCLUDED.raw_description,match_status='AUTO_MATCHED'""",
                        supplier_id, item.get("source_id", item["id"]), item["name"], item.get("description", ""),
                        item["longitude"], item["latitude"], canonical_id,
                    )
    finally:
        await connection.close()
    print(f"Seeded {len(rows)} canonical hotels and attractions.")


if __name__ == "__main__":
    asyncio.run(main())
