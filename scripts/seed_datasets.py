"""Fetch a small public OpenStreetMap hotel and attraction sample for a city."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


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
        os.getenv("OVERPASS_API_URL", "https://overpass-api.de/api/interpreter"),
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


def fetch_wikidata_attractions(city_name: str = "Dubai", limit: int = 100) -> list[dict]:
    """Resolve a city in Wikidata, then fetch coordinate-tagged nearby attractions."""
    city = re.sub(r"[^\w .'-]", "", city_name).strip()
    headers = {"User-Agent": "TBO-MultiSupplier-Platform/0.2 (open-data demo)"}
    search = requests.get(
        os.getenv("WIKIDATA_API_URL", "https://www.wikidata.org/w/api.php"),
        params={"action": "wbsearchentities", "search": city, "language": "en", "format": "json", "limit": 1},
        headers=headers,
        timeout=20,
    )
    search.raise_for_status()
    entities = search.json().get("search", [])
    if not entities:
        raise RuntimeError(f"Wikidata did not find a city entity for {city!r}")
    city_id = entities[0]["id"]
    if not re.fullmatch(r"Q\d+", city_id):
        raise RuntimeError("Wikidata returned an invalid entity identifier")
    query = f'''PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX schema: <http://schema.org/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>
SELECT ?item ?itemLabel ?itemDescription ?coordinate WHERE {{
  ?item wdt:P131* wd:{city_id}; wdt:P625 ?coordinate.
  OPTIONAL {{ ?item schema:description ?itemDescription FILTER(LANG(?itemDescription) = "en") }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}} LIMIT {max(1, min(limit, 500))}'''
    response = requests.get(
        os.getenv("WIKIDATA_SPARQL_URL", "https://query.wikidata.org/sparql"),
        params={"query": query, "format": "json"},
        headers={**headers, "Accept": "application/sparql-results+json"},
        timeout=45,
    )
    response.raise_for_status()
    bindings = response.json().get("results", {}).get("bindings", [])
    attractions = []
    for binding in bindings:
        point = re.fullmatch(r"Point\((-?[\d.]+) (-?[\d.]+)\)", binding["coordinate"]["value"])
        if not point:
            continue
        attractions.append(
            {
                "source_id": binding["item"]["value"].rsplit("/", 1)[-1],
                "name": binding.get("itemLabel", {}).get("value", "Unnamed attraction"),
                "latitude": float(point.group(2)),
                "longitude": float(point.group(1)),
                "city": city,
                "description": binding.get("itemDescription", {}).get("value", ""),
                "star_rating": None,
                "amenities": [],
            }
        )
    return attractions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", default="Dubai")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--source", choices=("osm", "wikidata", "both"), default="osm")
    parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "data" / "osm_inventory.json"
    )
    args = parser.parse_args()
    inventory = {"hotels": [], "attractions": []}
    if args.source in {"osm", "both"}:
        osm = fetch_osm_inventory(args.city, args.limit)
        inventory["hotels"].extend(osm["hotels"])
        inventory["attractions"].extend(osm["attractions"])
    if args.source in {"wikidata", "both"}:
        inventory["attractions"].extend(fetch_wikidata_attractions(args.city, args.limit))
    # Keep the first record for each source id when both datasets overlap.
    inventory["attractions"] = list({row["source_id"]: row for row in inventory["attractions"]}.values())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Saved {len(inventory['hotels'])} hotels and "
        f"{len(inventory['attractions'])} attractions to {args.output}"
    )


if __name__ == "__main__":
    main()
