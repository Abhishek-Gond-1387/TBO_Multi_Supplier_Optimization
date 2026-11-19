"""Purify and Enrich TBO Discovery Sample Inventory with Visually Verified Imagery.
"""

from __future__ import annotations

import json
from pathlib import Path
from services.image_catalog import resolve_item_images, get_destination_country, LANDMARK_CATALOG

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "sample_inventory.json"

NEW_INTERNATIONAL_ITEMS = [
    # --- SANTORINI (GREECE) ---
    {
        "id": "attraction-santorini-oia-sunset",
        "name": "Oia Village Sunset & Blue Domes Guided Walking Tour",
        "entity_type": "ATTRACTION",
        "destination": "Santorini",
        "country": "Greece",
        "country_code": "GR",
        "latitude": 36.4618,
        "longitude": 25.3753,
        "star_rating": 4.9,
        "description": "Iconic guided tour exploring the whitewashed alleys, blue-domed churches, and world-famous sunset viewpoints of Oia overlooking the Aegean caldera.",
        "source_category": "Cultural Heritage & Walking Tour",
        "amenities": ["Expert Local Guide", "Sunset Vista Guarantee", "Small Group VIP", "Instant Mobile Voucher"],
        "images": [
            "https://images.unsplash.com/photo-1530841377377-3ff06c0ca713?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1498503403619-e39e4ff390fe?auto=format&fit=crop&w=1200&q=85",
        ],
        "offers": [
            {"supplier_name": "Viator Experiences", "price": 4200, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.98},
            {"supplier_name": "TBO Preferred", "price": 3850, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.99},
            {"supplier_name": "Expedia Partner", "price": 4450, "currency": "INR", "available": True, "cancellation_flexible": False, "reliability_score": 0.94},
        ],
    },
    {
        "id": "attraction-santorini-caldera-cruise",
        "name": "Santorini Luxury Catamaran Caldera Cruise with BBQ & Wine",
        "entity_type": "ATTRACTION",
        "destination": "Santorini",
        "country": "Greece",
        "country_code": "GR",
        "latitude": 36.3865,
        "longitude": 25.3912,
        "star_rating": 5.0,
        "description": "Sail across the volcanic caldera with stops at the Red Beach, White Beach, and volcanic hot springs. Includes open bar with Greek wines and freshly grilled BBQ.",
        "source_category": "Luxury Catamaran Cruise",
        "amenities": ["Open Bar & Greek Wine", "BBQ Lunch Included", "Snorkeling Gear", "Hotel Pickup & Dropoff"],
        "images": [
            "https://images.unsplash.com/photo-1498503403619-e39e4ff390fe?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1530841377377-3ff06c0ca713?auto=format&fit=crop&w=1200&q=85",
        ],
        "offers": [
            {"supplier_name": "TBO Preferred", "price": 10500, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.99},
            {"supplier_name": "Booking.com Direct", "price": 11200, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.96},
            {"supplier_name": "Hotelbeds Global", "price": 11800, "currency": "INR", "available": True, "cancellation_flexible": False, "reliability_score": 0.95},
        ],
    },
    {
        "id": "hotel-canaves-oia-suites",
        "name": "Canaves Oia Suites & Luxury Spa",
        "entity_type": "HOTEL",
        "destination": "Santorini",
        "country": "Greece",
        "country_code": "GR",
        "latitude": 36.4632,
        "longitude": 25.3780,
        "star_rating": 5.0,
        "description": "Perched on the dramatic volcanic cliffs of Oia, featuring private plunge pools, infinity views of the Aegean Sea, and world-class Mediterranean hospitality.",
        "source_category": "5-Star Luxury Cliffside Suites",
        "amenities": ["Private Infinity Plunge Pool", "Caldera View", "Champagne Breakfast", "Free Ultra-Fast WiFi"],
        "images": [
            "https://images.unsplash.com/photo-1530841377377-3ff06c0ca713?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1498503403619-e39e4ff390fe?auto=format&fit=crop&w=1200&q=85",
        ],
        "offers": [
            {"supplier_name": "TBO Preferred", "price": 48500, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.99},
            {"supplier_name": "Agoda Direct", "price": 51200, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.95},
            {"supplier_name": "Booking.com Direct", "price": 53000, "currency": "INR", "available": True, "cancellation_flexible": False, "reliability_score": 0.96},
        ],
    },
    {
        "id": "hotel-grace-hotel-santorini",
        "name": "Grace Hotel Santorini, Auberge Resorts Collection",
        "entity_type": "HOTEL",
        "destination": "Santorini",
        "country": "Greece",
        "country_code": "GR",
        "latitude": 36.4338,
        "longitude": 25.4215,
        "star_rating": 5.0,
        "description": "An exquisite cliff-top retreat in Imerovigli offering uninterrupted caldera vistas, Michelin-inspired dining at Varoulko, and bespoke sunset concierge service.",
        "source_category": "Ultra-Luxury Cliffside Resort",
        "amenities": ["Iconic Infinity Pool", "Varoulko Dining", "Sunset Concierge", "Helicopter Transfer"],
        "images": [
            "https://images.unsplash.com/photo-1498503403619-e39e4ff390fe?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1530841377377-3ff06c0ca713?auto=format&fit=crop&w=1200&q=85",
        ],
        "offers": [
            {"supplier_name": "TBO Preferred", "price": 54000, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.99},
            {"supplier_name": "Hotelbeds Global", "price": 57500, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.96},
        ],
    },
    {
        "id": "dine-santorini-varoulko",
        "name": "Varoulko Santorini - Michelin Fine Dining by Lefteris Lazarou",
        "entity_type": "DINING",
        "destination": "Santorini",
        "country": "Greece",
        "country_code": "GR",
        "latitude": 36.4342,
        "longitude": 25.4220,
        "star_rating": 4.9,
        "description": "Renowned chef Lefteris Lazarou presents innovative Greek seafood pairings overlooking Skaros rock and the Aegean caldera.",
        "source_category": "Michelin Star Fine Dining",
        "amenities": ["Chef Tasting Menu", "Caldera Sunset Tables", "Sommelier Wine Pairing", "Air Conditioned"],
        "images": [
            "https://images.unsplash.com/photo-1530841377377-3ff06c0ca713?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1498503403619-e39e4ff390fe?auto=format&fit=crop&w=1200&q=85",
        ],
        "offers": [
            {"supplier_name": "TBO Preferred", "price": 7500, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.98},
        ],
    },

    # --- ABU DHABI (UAE) ---
    {
        "id": "attraction-sheikh-zayed-mosque",
        "name": "Sheikh Zayed Grand Mosque Architectural VIP Experience",
        "entity_type": "ATTRACTION",
        "destination": "Abu Dhabi",
        "country": "UAE",
        "country_code": "AE",
        "latitude": 24.4128,
        "longitude": 54.4750,
        "star_rating": 5.0,
        "description": "Tour the breathtaking Sheikh Zayed Grand Mosque, featuring 82 white marble domes, 24-carat gold-gilded chandeliers, and the world's largest hand-knotted carpet.",
        "source_category": "Architectural Landmark Tour",
        "amenities": ["Skip-The-Line Access", "Official Cultural Guide", "Traditional Attire Provided", "Instant Voucher"],
        "images": [
            "https://images.unsplash.com/photo-1512632578888-169bbbc64f33?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=85",
        ],
        "offers": [
            {"supplier_name": "TBO Preferred", "price": 2850, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.99},
            {"supplier_name": "Viator Experiences", "price": 3100, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.95},
        ],
    },
    {
        "id": "attraction-louvre-abu-dhabi",
        "name": "Louvre Abu Dhabi Museum Admission & Floating Dome Experience",
        "entity_type": "ATTRACTION",
        "destination": "Abu Dhabi",
        "country": "UAE",
        "country_code": "AE",
        "latitude": 24.5337,
        "longitude": 54.3986,
        "star_rating": 4.8,
        "description": "Discover Jean Nouvel's iconic 'Rain of Light' floating dome and universal masterpieces bridging Western and Eastern civilizations on Saadiyat Island.",
        "source_category": "Universal Art & Museum Admission",
        "amenities": ["Express Mobile Admission", "Children's Museum Access", "Waterfront Promenade", "Audio Tour App"],
        "images": [
            "https://images.unsplash.com/photo-1578895101408-1a36b834405b?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1512632578888-169bbbc64f33?auto=format&fit=crop&w=1200&q=85",
        ],
        "offers": [
            {"supplier_name": "TBO Preferred", "price": 1850, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.99},
            {"supplier_name": "Expedia Partner", "price": 2050, "currency": "INR", "available": True, "cancellation_flexible": False, "reliability_score": 0.93},
        ],
    },
    {
        "id": "hotel-emirates-palace",
        "name": "Emirates Palace Mandarin Oriental, Abu Dhabi",
        "entity_type": "HOTEL",
        "destination": "Abu Dhabi",
        "country": "UAE",
        "country_code": "AE",
        "latitude": 24.4617,
        "longitude": 54.3173,
        "star_rating": 5.0,
        "description": "One of the most magnificent luxury palaces in the world, surrounded by 100 hectares of manicured gardens and a 1.3 km private pristine beach.",
        "source_category": "Iconic Ultra-Luxury Palace",
        "amenities": ["Private Beach", "24K Gold Flake Cappuccino Service", "Butler Service", "Palace Spa"],
        "images": [
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1512632578888-169bbbc64f33?auto=format&fit=crop&w=1200&q=85",
        ],
        "offers": [
            {"supplier_name": "TBO Preferred", "price": 42000, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.99},
            {"supplier_name": "Agoda Direct", "price": 45500, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.95},
            {"supplier_name": "Booking.com Direct", "price": 47000, "currency": "INR", "available": True, "cancellation_flexible": False, "reliability_score": 0.96},
        ],
    },

    # --- ATHENS (GREECE) ---
    {
        "id": "attraction-athens-acropolis",
        "name": "Acropolis & Parthenon VIP Skip-the-Line Guided Tour",
        "entity_type": "ATTRACTION",
        "destination": "Athens",
        "country": "Greece",
        "country_code": "GR",
        "latitude": 37.9715,
        "longitude": 23.7257,
        "star_rating": 4.9,
        "description": "Bypass the main entrance queues with an expert archeologist guide to explore the Parthenon, Erechtheion, Propylaea, and the Theater of Dionysus.",
        "source_category": "UNESCO World Heritage Tour",
        "amenities": ["Skip-the-Line Ticket Included", "Licensed Archeologist Guide", "Headsets Included", "Small Group"],
        "images": [
            "https://images.unsplash.com/photo-1503152394-c571994fd383?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=85",
        ],
        "offers": [
            {"supplier_name": "TBO Preferred", "price": 4600, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.99},
            {"supplier_name": "Viator Experiences", "price": 4950, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.96},
        ],
    },
    {
        "id": "hotel-electra-palace-athens",
        "name": "Electra Palace Athens (Plaka & Acropolis View)",
        "entity_type": "HOTEL",
        "destination": "Athens",
        "country": "Greece",
        "country_code": "GR",
        "latitude": 37.9730,
        "longitude": 23.7314,
        "star_rating": 4.8,
        "description": "Aristocratic 5-star hotel in the heart of historic Plaka with a rooftop pool and dining terrace facing directly towards the illuminated Parthenon.",
        "source_category": "5-Star Heritage Hotel",
        "amenities": ["Direct Parthenon View", "Rooftop Pool", "Plaka Center", "Greek Breakfast Buffet"],
        "images": [
            "https://images.unsplash.com/photo-1503152394-c571994fd383?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=85",
        ],
        "offers": [
            {"supplier_name": "TBO Preferred", "price": 22500, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.99},
            {"supplier_name": "Booking.com Direct", "price": 24800, "currency": "INR", "available": True, "cancellation_flexible": True, "reliability_score": 0.96},
        ],
    },
]


def run():
    print(f"Loading {DATA_PATH}...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    # Index new items
    new_by_id = {it["id"]: it for it in NEW_INTERNATIONAL_ITEMS}
    existing_ids = {it["id"] for it in items}

    for idx, cur in enumerate(items):
        if cur["id"] in new_by_id:
            items[idx] = new_by_id[cur["id"]]

    for new_id, new_it in new_by_id.items():
        if new_id not in existing_ids:
            items.append(new_it)
            existing_ids.add(new_id)

    print(f"Total items to purify: {len(items)}")

    mismatches_fixed = 0
    for it in items:
        dest = it.get("destination", "Delhi")
        country = get_destination_country(dest)
        it["country"] = country
        if country == "UAE":
            it["country_code"] = "AE"
        elif country == "Greece":
            it["country_code"] = "GR"
        else:
            it["country_code"] = "IN"

        # Deterministically resolve verified destination photos
        clean_images = resolve_item_images(it)
        if it.get("images") != clean_images:
            mismatches_fixed += 1
            it["images"] = clean_images

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"Purification complete. Updated {mismatches_fixed} records.")


if __name__ == "__main__":
    run()
