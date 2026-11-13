"""Fetch a small public OpenStreetMap hotel and attraction sample for a city."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def fetch_osm_inventory(city_name: str = "Dubai", limit: int = 100) -> dict[str, list[dict]]:
    city = re.sub(r"[^\w .'-]", "", city_name).strip()
    if not city:
        raise ValueError("Enter a city name containing letters or numbers.")
    if not 1 <= limit <= 500:
        raise ValueError("Limit must be between 1 and 500.")
    query = f'''[out:json][timeout:45];
area["name"="{city}"]["boundary"="administrative"]->.searchArea;
(
  nwr["tourism"~"hotel|attraction"](area.searchArea);
  nwr["historic"~"monument|museum|castle"](area.searchArea);
);
out center tags {limit};'''
    response = requests.post(
        "https://overpass-api.de/api/interpreter",
        data={"data": query},
        headers={"User-Agent": "TBO-MultiSupplier-Platform/0.1 (local demo)"},
        timeout=60,
    )
    response.raise_for_status()
    elements = response.json().get("elements", [])
    result: dict[str, list[dict]] = {"hotels": [], "attractions": []}
    for element in elements:
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        center = element.get("center", {})
        latitude = element.get("lat", center.get("lat"))
        longitude = element.get("lon", center.get("lon"))
        if latitude is None or longitude is None:
            continue
        bucket = "hotels" if tags.get("tourism") == "hotel" else "attractions"
        try:
            stars = float(tags["stars"]) if tags.get("stars") else None
        except ValueError:
            stars = None
        result[bucket].append(
            {
                "source_id": f"osm/{element.get('type', 'object')}/{element['id']}",
                "name": name,
                "latitude": latitude,
                "longitude": longitude,
                "city": city,
                "street": tags.get("addr:street", ""),
                "star_rating": stars,
                "amenities": sorted(
                    key
                    for key in ("internet_access", "swimming_pool", "air_conditioning")
                    if tags.get(key) not in (None, "no")
                ),
            }
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", default="Dubai")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "data" / "osm_inventory.json"
    )
    args = parser.parse_args()
    inventory = fetch_osm_inventory(args.city, args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Saved {len(inventory['hotels'])} hotels and "
        f"{len(inventory['attractions'])} attractions to {args.output}"
    )


if __name__ == "__main__":
    main()
