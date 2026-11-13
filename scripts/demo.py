"""Call the running local API and print a compact end-to-end demo."""

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

    search = session.get(
        f"{base}/api/v1/inventory/search",
        params={"destination": "Dubai", "entity_type": "HOTEL", "max_price": 400},
        timeout=5,
    )
    search.raise_for_status()
    print("\nTop supplier-ranked stays:")
    for result in search.json()["results"][:3]:
        item, offer = result["item"], result["selected_supplier"]
        price = f"{offer['currency']} {offer['price']:,.0f}" if offer else "Price on request"
        print(f"  {item['name']}: {price} via {offer['supplier_name'] if offer else '—'} | {', '.join(result['badges']) or 'ranked'}")

    voice = session.post(
        f"{base}/api/v1/voice/query",
        json={"transcript": "Find 3-star hotels in Dubai with breakfast under 150 dollars"},
        timeout=5,
    )
    voice.raise_for_status()
    print("\nVoice search:", voice.json()["voice_reply"])
    print("Parsed filters:", voice.json()["parsed_filters"])

    room = session.post(
        f"{base}/api/v1/rooms/normalize", json={"raw_name": "DLX DBL OCVW RO W/BALC"}, timeout=5
    )
    room.raise_for_status()
    print("\nRoom normalization:", room.json()["normalized_name"])

    tour = session.post(
        f"{base}/api/v1/sightseeing/compare",
        json={
            "left_title": "At The Top Level 124 standard entry",
            "left_description": "General admission. No transfer included.",
            "right_title": "Sky Lounge Level 148 with Private Chauffeur and Lunch",
            "right_description": "VIP access, private hotel pickup, lunch and free cancellation up to 24 hours.",
        },
        timeout=5,
    )
    tour.raise_for_status()
    print("Tour differences:", tour.json()["differences"])
    print(f"\nOpen the map: {base.replace(':8000', ':5500')}/map_view.html")
    print(f"Review queue: {base.replace(':8000', ':5500')}/admin.html")


if __name__ == "__main__":
    main()
