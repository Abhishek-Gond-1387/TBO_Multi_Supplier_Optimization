"""Show the Delhi source-data pilot using the running local API."""

from __future__ import annotations

import argparse
import requests


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = args.api.rstrip("/")
    session = requests.Session()
    health = session.get(f"{base}/api/v1/health", timeout=5)
    health.raise_for_status()
    status = session.get(f"{base}/api/v1/data/status", timeout=5).json()

    print("=" * 68)
    print("TBO INVENTORY QUALITY PILOT · DELHI")
    print("=" * 68)
    print(f"API: {health.json().get('status')}")
    print(f"OpenStreetMap snapshot: {status.get('hotel_count', 0)} hotel records, "
          f"{status.get('attraction_count', 0)} visitor-place records")
    print("Supplier live rates: not connected. Guest review ratings: not in this source.\n")

    for kind, label in (("HOTEL", "Hotels"), ("ATTRACTION", "Sightseeing / visitor places")):
        response = session.get(
            f"{base}/api/v1/inventory/search",
            params={"destination": "Delhi", "entity_type": kind},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        print(f"{label}: {data['count']} matches")
        for row in data["results"][:3]:
            item = row["item"]
            print(f"  · {item['name']} — source: {item.get('source', 'unknown')}; "
                  "price/rating: not supplied")

    room = session.post(
        f"{base}/api/v1/rooms/normalize",
        json={"raw_name": "DLX KNG CT-VW BB BALC"}, timeout=5,
    )
    room.raise_for_status()
    print("\nRoom normalization example:")
    print(f"  {room.json().get('raw_name')} → {room.json().get('normalized_name')}")

    print("\nOpening the real-record hotel match audit…")
    audit = session.post(f"{base}/api/v1/admin/dedup/batch-run", timeout=15)
    audit.raise_for_status()
    result = audit.json()
    print(f"  Scanned: {result.get('total_listings_scanned', 0)} hotels")
    print(f"  Potential merge suggestions: {result.get('proposed_auto_merge_candidates_count', 0)}")
    print(f"  Human review candidates: {result.get('human_review_candidates_count', 0)}")
    print("  Source rows changed: 0 (analysis only)")

    print("\nMap:        http://127.0.0.1:5500/map_view.html")
    print("Match hub:  http://127.0.0.1:5500/admin.html")
    print(f"API docs:   {base}/docs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
