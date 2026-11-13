"""Show the Delhi open-place pilot from the running local API."""

from __future__ import annotations

import argparse

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = args.api.rstrip("/")
    session = requests.Session()

    health = session.get(f"{base}/api/v1/health", timeout=5)
    health.raise_for_status()
    print("API:", health.json()["status"])

    status_response = session.get(f"{base}/api/v1/data/status", timeout=5)
    status_response.raise_for_status()
    status = status_response.json()
    print(f"\nDelhi place-data status: {status['state']}")
    if status.get("refreshed_at"):
        print(f"Source: OpenStreetMap · refreshed {status['refreshed_at']}")

    for entity_type, label in (("HOTEL", "Hotel places"), ("ATTRACTION", "Experiences & other places")):
        response = session.get(
            f"{base}/api/v1/inventory/search",
            params={"country_code": "IN", "destination": "Delhi", "entity_type": entity_type},
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        print(f"\n{label}: {payload['count']}")
        for result in payload["results"][:5]:
            item = result["item"]
            origin = "OpenStreetMap" if str(item.get("source_id", "")).startswith("osm/") else "local illustrative fallback"
            print(f"  {item['name']} · {item['latitude']:.5f}, {item['longitude']:.5f} · {origin}")

    print("\nFree OSM data provides place records, not live supplier rates, room availability, or cancellation terms.")
    print("Supplier comparison and bookable ranking need authorized supplier feeds.")
    print(f"\nOpen the Delhi map: {base.replace(':8000', ':5500')}/map_view.html")
    print(f"Review queue: {base.replace(':8000', ':5500')}/admin.html")


if __name__ == "__main__":
    main()
