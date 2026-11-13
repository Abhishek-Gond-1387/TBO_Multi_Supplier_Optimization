"""Fetch up to 500 named hotel and visitor-place records from OpenStreetMap."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def fetch_osm_inventory(city_name: str = "Delhi", limit: int = 100, country_code: str = "IN") -> dict[str, list[dict]]:
    city = re.sub(r"[^\w .'-]", "", city_name).strip()
    if not city:
        raise ValueError("Enter a city name containing letters or numbers.")
    if not 1 <= limit <= 500:
        raise ValueError("Limit must be between 1 and 500.")
    query = f'''[out:json][timeout:60];
area["name"="{city}"]["boundary"="administrative"]->.searchArea;
(
  nwr["tourism"~"^(hotel|guest_house|hostel|motel|resort|apartment|bed_and_breakfast|attraction|museum|viewpoint|zoo|gallery|theme_park|aquarium|artwork)$"][~"^(name|name:en|name:hi)$"~"."](area.searchArea);
  nwr["historic"~"^(monument|memorial|archaeological_site|fort|castle|ruins|heritage)$"][~"^(name|name:en|name:hi)$"~"."](area.searchArea);
  nwr["amenity"~"^(restaurant|cafe|fast_food|food_court|pub|bar|marketplace|place_of_worship|arts_centre|cinema|theatre|library|community_centre|spa|public_bath)$"][~"^(name|name:en|name:hi)$"~"."](area.searchArea);
  nwr["leisure"~"^(park|garden|sports_centre|stadium|water_park|nature_reserve|marina|golf_course|playground)$"][~"^(name|name:en|name:hi)$"~"."](area.searchArea);
  nwr["shop"~"^(mall|department_store|supermarket|gift|books|clothes|marketplace)$"][~"^(name|name:en|name:hi)$"~"."](area.searchArea);
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
        name = tags.get("name") or tags.get("name:en") or tags.get("name:hi")
        if not name:
            continue
        center = element.get("center", {})
        latitude = element.get("lat", center.get("lat"))
        longitude = element.get("lon", center.get("lon"))
        if latitude is None or longitude is None:
            continue
        tourism_type = tags.get("tourism", "")
        hospitality_types = {"hotel", "guest_house", "hostel", "motel", "resort", "apartment", "bed_and_breakfast"}
        bucket = "hotels" if tourism_type in hospitality_types else "attractions"
        category_key = next((key for key in ("tourism", "historic", "amenity", "leisure", "shop") if tags.get(key)), "place")
        category_value = tags.get(category_key, "place").replace("_", " ").title()
        category_group = {
            "tourism": "Accommodation" if bucket == "hotels" else "Tourism",
            "historic": "Historic site",
            "amenity": "Food, culture & services",
            "leisure": "Parks & recreation",
            "shop": "Shopping",
            "place": "Place",
        }[category_key]
        try:
            stars = float(tags["stars"]) if tags.get("stars") else None
        except ValueError:
            stars = None
        result[bucket].append(
            {
                "source_id": f"osm/{element.get('type', 'object')}/{element['id']}",
                "source": "OpenStreetMap",
                "name": name,
                "latitude": latitude,
                "longitude": longitude,
                "city": city,
                "country_code": country_code.upper(),
                "street": tags.get("addr:street", ""),
                "star_rating": stars,
                "source_category": f"{category_group} · {category_value}",
                "last_edited_at": element.get("timestamp"),
                "description": " · ".join(
                    value for value in (
                        tags.get("description"),
                        tags.get("opening_hours"),
                        tags.get("access"),
                    ) if value
                ),
                "amenities": sorted({
                    value.replace("_", " ")
                    for key, value in tags.items()
                    if key in {"internet_access", "swimming_pool", "air_conditioning", "wheelchair", "cuisine", "sport", "religion", "denomination", "access", "opening_hours"}
                    and value not in (None, "", "no")
                }),
            }
        )
    return result


def fetch_wikidata_attractions(city_name: str = "Delhi", limit: int = 100, country_code: str = "IN") -> list[dict]:
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
                "country_code": country_code.upper(),
                "description": binding.get("itemDescription", {}).get("value", ""),
                "star_rating": None,
                "amenities": [],
            }
        )
    return attractions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", default="Delhi")
    parser.add_argument("--country-code", choices=("IN", "AE"), default="IN")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--source", choices=("osm", "wikidata", "both"), default="osm")
    parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "data" / "osm_inventory.json"
    )
    args = parser.parse_args()
    status_path = args.output.with_name(f"{args.output.stem}.status.json")
    started_at = datetime.now(timezone.utc).isoformat()

    def write_status(payload: dict) -> None:
        temporary_status = status_path.with_suffix(status_path.suffix + ".tmp")
        temporary_status.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temporary_status.replace(status_path)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_status({"state": "refreshing", "started_at": started_at, "city": args.city, "country_code": args.country_code})
    try:
        inventory = {"hotels": [], "attractions": []}
        if args.source in {"osm", "both"}:
            osm = fetch_osm_inventory(args.city, args.limit, args.country_code)
            inventory["hotels"].extend(osm["hotels"])
            inventory["attractions"].extend(osm["attractions"])
        if args.source in {"wikidata", "both"}:
            inventory["attractions"].extend(fetch_wikidata_attractions(args.city, args.limit, args.country_code))
        # Keep the first record for each source id when both datasets overlap.
        inventory["attractions"] = list({row["source_id"]: row for row in inventory["attractions"]}.values())
        refreshed_at = datetime.now(timezone.utc).isoformat()
        metadata = {
            "source": "OpenStreetMap/Overpass" if args.source == "osm" else args.source,
            "city": args.city,
            "country_code": args.country_code.upper(),
            "license": "ODbL",
            "refreshed_at": refreshed_at,
            "hotel_count": len(inventory["hotels"]),
            "attraction_count": len(inventory["attractions"]),
        }
        inventory["metadata"] = metadata
        temporary_output = args.output.with_name(f".{args.output.name}.tmp")
        temporary_output.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary_output.replace(args.output)
        write_status({"state": "ready", "started_at": started_at, "metadata": metadata})
        print(
            f"Updated {metadata['hotel_count']} hotel places and "
            f"{metadata['attraction_count']} experiences for {args.city} from OpenStreetMap at {refreshed_at}."
        )
        print("OSM place data has no live room prices, availability, or customer review scores.")
    except Exception as exc:
        write_status({"state": "error", "started_at": started_at, "error": str(exc)[:500]})
        raise


if __name__ == "__main__":
    main()
