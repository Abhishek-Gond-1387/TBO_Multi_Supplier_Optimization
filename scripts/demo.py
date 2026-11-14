"""TBO Multi-Supplier Inventory Optimization Walkthrough."""

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
    print("==================================================================")
    print("TBO MULTI-SUPPLIER INVENTORY OPTIMIZATION PLATFORM")
    print("==================================================================")
    print(f"API Health: {health.json()['status']}")

    rates_resp = session.get(f"{base}/api/v1/currency/rates", timeout=5)
    if rates_resp.ok:
        print(f"Supported Currencies: {', '.join(rates_resp.json()['rates'].keys())}")

    for entity_type, label in (("HOTEL", "Hotels"), ("ATTRACTION", "Sightseeing & Experiences")):
        response = session.get(
            f"{base}/api/v1/inventory/search",
            params={"destination": "Delhi", "entity_type": entity_type},
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        print(f"\n{label} Available: {payload['count']} results")
        for result in payload["results"][:3]:
            item = result["item"]
            best = result.get("selected_supplier")
            price_str = f"INR {best['price']:.0f} via {best['supplier_name']}" if best else "Quote Needed"
            print(f"  • {item['name']} ({item['destination']}) - {price_str}")

    # Demo Room Normalization
    room_resp = session.post(f"{base}/api/v1/rooms/normalize", json={"raw_name": "DLX KNG CT-VW BB BALC"}, timeout=5)
    if room_resp.ok:
        norm = room_resp.json()
        print(f"\nRoom Normalizer Demo:")
        print(f"  Input:  'DLX KNG CT-VW BB BALC'")
        print(f"  Output: '{norm['normalized_name']}' [Class: {norm['room_class']}, Bed: {norm['bed_type']}]")

    # Demo Tour Inclusions Diff
    tour_resp = session.post(
        f"{base}/api/v1/sightseeing/compare",
        json={
            "left_title": "Red Fort Standard Entry (Viator)",
            "left_description": "Admission ticket, no transfers, self guided.",
            "right_title": "Red Fort VIP Fast Track with Private Chauffeur & Lunch (GetYourGuide)",
            "right_description": "Skip the line admission, private hotel pickup, buffet lunch included.",
        },
        timeout=5,
    )
    if tour_resp.ok:
        diff = tour_resp.json()
        print(f"\nSightseeing Inclusions Diff Demo:")
        print(f"  Differences Identified: {', '.join(diff['differences'])}")

    print("\n------------------------------------------------------------------")
    print(f"Google Discovery Map:  http://127.0.0.1:5500/map_view.html")
    print(f"Operations Review:     http://127.0.0.1:5500/admin.html")
    print(f"Interactive API Docs:  {base}/docs")
    print("==================================================================")


if __name__ == "__main__":
    main()
