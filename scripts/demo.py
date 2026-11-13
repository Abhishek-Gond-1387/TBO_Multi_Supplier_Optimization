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
        params={"country_code": "IN", "destination": "Delhi", "currency": "INR", "entity_type": "HOTEL", "max_price": 10000},
        timeout=5,
    )
    search.raise_for_status()
    print("\nIndia first — top Delhi demo stays (illustrative INR prices):")
    for result in search.json()["results"][:3]:
        item, offer = result["item"], result["selected_supplier"]
        price = f"{offer['currency']} {offer['price']:,.0f}" if offer else "Price on request"
        print(f"  {item['name']}: {price} via {offer['supplier_name'] if offer else '—'} | {', '.join(result['badges']) or 'ranked'}")

    voice = session.post(
        f"{base}/api/v1/voice/query",
        json={"transcript": "Find hotels in India under 8000 rupees with breakfast"},
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
            "left_title": "Taj Mahal standard entry",
            "left_description": "General admission. No transfer included.",
            "right_title": "Taj Mahal priority entry with private car and lunch",
            "right_description": "Priority access, private hotel pickup, lunch and free cancellation up to 24 hours.",
        },
        timeout=5,
    )
    tour.raise_for_status()
    print("Tour differences:", tour.json()["differences"])

    dubai = session.get(
        f"{base}/api/v1/inventory/search",
        params={"country_code": "AE", "destination": "Dubai", "currency": "USD", "entity_type": "HOTEL", "max_price": 400},
        timeout=5,
    )
    dubai.raise_for_status()
    print(f"\nNext: Dubai has {dubai.json()['count']} illustrative USD hotel records.")
    print(f"\nOpen the map: {base.replace(':8000', ':5500')}/map_view.html")
    print(f"Review queue: {base.replace(':8000', ':5500')}/admin.html")


if __name__ == "__main__":
    main()
