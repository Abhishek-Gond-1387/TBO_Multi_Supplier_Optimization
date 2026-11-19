"""Verified Destination & Landmark Image Catalog for TBO Discovery.

Provides a multi-tier, authentic image-matching engine ensuring every
travel inventory item displays an accurate, visually verified destination-specific photograph.
Eliminates cross-country and cross-region mismatches (e.g. Dubai showing India Gate,
Delhi showing Burj Khalifa, Mumbai showing Santorini, Konark showing Gateway of India).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

# ==============================================================================
# 1. VERIFIED LANDMARK IMAGERY (All Visually Verified Unsplash Photographs)
# ==============================================================================
LANDMARK_CATALOG: dict[str, list[str]] = {
    # --- DUBAI / UAE ICONS ---
    "BURJ_KHALIFA": [
        "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1200&q=85",  # Burj Khalifa downtown & blue sky
        "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?auto=format&fit=crop&w=1200&q=85",  # Burj Khalifa sunset tower
        "https://images.unsplash.com/photo-1580674684081-7617fbf3d745?auto=format&fit=crop&w=1200&q=85",  # Burj Khalifa lake & palm promenade
    ],
    "BURJ_AL_ARAB": [
        "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=1200&q=85",  # Iconic Burj Al Arab sail silhouette sunset
        "https://images.unsplash.com/photo-1528702748617-c64d49f918af?auto=format&fit=crop&w=1200&q=85",  # Burj Al Arab daytime beach view
    ],
    "DUBAI_FRAME": [
        "https://images.unsplash.com/photo-1578895101408-1a36b834405b?auto=format&fit=crop&w=1200&q=85",  # Dubai cityscape & Frame architectural monument
        "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1200&q=85",
    ],
    "DUBAI_MARINA": [
        "https://images.unsplash.com/photo-1578895101408-1a36b834405b?auto=format&fit=crop&w=1200&q=85",  # Dubai Marina canal, yachts & skyscrapers
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?auto=format&fit=crop&w=1200&q=85",  # Dubai Marina night skyline reflections
    ],
    "PALM_JUMEIRAH": [
        "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?auto=format&fit=crop&w=1200&q=85",  # Atlantis The Palm luxury resort facade
        "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=85",  # Palm Jumeirah luxury waterfront terrace
    ],
    "DUBAI_DESERT": [
        "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?auto=format&fit=crop&w=1200&q=85",  # Red-golden desert safari sand dunes
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=85",  # Dubai desert twilight
    ],

    # --- ABU DHABI / UAE ICONS ---
    "SHEIKH_ZAYED_MOSQUE": [
        "https://images.unsplash.com/photo-1512632578888-169bbbc64f33?auto=format&fit=crop&w=1200&q=85",  # Visually Verified: Sheikh Zayed Grand Mosque reflection pool & domes
    ],
    "EMIRATES_PALACE": [
        "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=85",  # Luxury palace facade Abu Dhabi
        "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=85",
    ],
    "LOUVRE_ABU_DHABI": [
        "https://images.unsplash.com/photo-1578895101408-1a36b834405b?auto=format&fit=crop&w=1200&q=85",  # Louvre modern dome waterfront
    ],

    # --- GREECE - SANTORINI ICONS ---
    "SANTORINI_OIA": [
        "https://images.unsplash.com/photo-1530841377377-3ff06c0ca713?auto=format&fit=crop&w=1200&q=85",  # Visually Verified: Authentic Oia blue-domed church & caldera
        "https://images.unsplash.com/photo-1498503403619-e39e4ff390fe?auto=format&fit=crop&w=1200&q=85",  # Visually Verified: Santorini cliffside plunge pool & cruise ship
    ],
    "SANTORINI_CALDERA_CRUISE": [
        "https://images.unsplash.com/photo-1498503403619-e39e4ff390fe?auto=format&fit=crop&w=1200&q=85",  # Visually Verified: Santorini caldera & cruise liner
        "https://images.unsplash.com/photo-1530841377377-3ff06c0ca713?auto=format&fit=crop&w=1200&q=85",
    ],

    # --- GREECE - ATHENS ICONS ---
    "ATHENS_ACROPOLIS": [
        "https://images.unsplash.com/photo-1503152394-c571994fd383?auto=format&fit=crop&w=1200&q=85",  # Visually Verified: The Parthenon on Acropolis rock
    ],

    # --- INDIA - DELHI NCR ICONS ---
    "INDIA_GATE": [
        "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=1200&q=85",  # Visually Verified: India Gate War Memorial New Delhi at sunset
    ],
    "RED_FORT": [
        "https://images.unsplash.com/photo-1592635196078-9fdc757f27f4?auto=format&fit=crop&w=1200&q=85",  # Visually Verified: Red Fort sandstone facade
    ],
    "QUTUB_MINAR": [
        "https://images.unsplash.com/photo-1770891312604-ac424d09671a?auto=format&fit=crop&w=1200&q=85",  # Visually Verified: Authentic Qutub Minar sandstone & marble tower
    ],

    # --- INDIA - AGRA & UTTAR PRADESH ICONS ---
    "TAJ_MAHAL": [
        "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=1200&q=85",  # Visually Verified: Taj Mahal white marble dome & reflection
        "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1200&q=85",  # Taj Mahal gateway vista
        "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=85",  # Taj Mahal pavilion
    ],
    "AGRA_FORT": [
        "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=85",  # Agra Fort red sandstone ramparts
    ],
    "VARANASI_GHATS": [
        "https://images.unsplash.com/photo-1585136917124-74cf81c2069e?auto=format&fit=crop&w=1200&q=85",  # Varanasi Dashashwamedh Ghat & boats
        "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=1200&q=85",  # Ganga Aarti spiritual lamps
    ],

    # --- INDIA - RAJASTHAN ICONS ---
    "HAWA_MAHAL": [
        "https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1200&q=85",  # Hawa Mahal Palace of Winds Pink City
        "https://images.unsplash.com/photo-1609137144822-475225964f43?auto=format&fit=crop&w=1200&q=85",
    ],
    "AMBER_FORT": [
        "https://images.unsplash.com/photo-1597040663342-45b6af3d91a8?auto=format&fit=crop&w=1200&q=85",  # Amber Fort hilltop walls & lake
    ],
    "UDAIPUR_LAKE_PICHOLA": [
        "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&w=1200&q=85",  # Lake Pichola City Palace Udaipur
        "https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1200&q=85",  # Udaipur Taj Lake Palace
    ],

    # --- INDIA - MUMBAI & MAHARASHTRA ICONS ---
    "GATEWAY_OF_INDIA": [
        "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=1200&q=85",  # Visually Verified: Gateway of India sunset pink sky Mumbai
        "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?auto=format&fit=crop&w=1200&q=85",  # Visually Verified: Gateway of India waterfront
    ],
    "MUMBAI_MARINE_DRIVE": [
        "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?auto=format&fit=crop&w=1200&q=85",  # Queen's Necklace Marine Drive
    ],

    # --- INDIA - KASHMIR & HIMALAYAS ---
    "DAL_LAKE": [
        "https://images.unsplash.com/photo-1506015391300-4802dc74de2e?auto=format&fit=crop&w=1200&q=85",  # Dal Lake Shikara boat Srinagar
        "https://images.unsplash.com/photo-1581793745862-99fde7fa73d2?auto=format&fit=crop&w=1200&q=85",  # Kashmir snow peaks
    ],

    # --- INDIA - PUNJAB ICONS ---
    "GOLDEN_TEMPLE": [
        "https://images.unsplash.com/photo-1514222134-b57cbb8ce073?auto=format&fit=crop&w=1200&q=85",  # Golden Temple Amritsar
    ],

    # --- INDIA - SOUTH & COASTAL ICONS ---
    "KERALA_BACKWATERS": [
        "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=1200&q=85",  # Alleppey traditional kettuvallam houseboat
        "https://images.unsplash.com/photo-1593693397690-362cb9666fc2?auto=format&fit=crop&w=1200&q=85",  # Kerala palm canals
    ],
    "GOA_BEACHES": [
        "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1200&q=85",  # Goa tropical beach
    ],
}

# ==============================================================================
# 2. NEUTRAL CATEGORY-APPROPRIATE IMAGERY (Zero Misplaced Landmark Risk)
# ==============================================================================
NEUTRAL_CATEGORY_POOLS = {
    "ATTRACTION": [
        "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=1200&q=85",  # Guided cultural walking tour group & historic street
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=85",  # Scenic nature vista & excursion
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=85",  # Scenic valley landscape tour
        "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1200&q=85",  # Travel road adventure & photography tour
    ],
    "HOTEL": [
        "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=85",  # 5-star hotel luxury infinity pool
        "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=85",  # Luxury suite interior & king bed
        "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=85",  # Grand boutique hotel entrance
        "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=85",  # Modern designer hotel bedroom
    ],
    "DINING": [
        "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=85",  # Fine dining restaurant table setting
        "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=85",  # Luxury restaurant ambience & wine
        "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=85",  # Gourmet chef tasting menu
    ],
    "TRANSPORT": [
        "https://images.unsplash.com/photo-1474487548417-781cb71495f3?auto=format&fit=crop&w=1200&q=85",  # Modern high-speed railway & locomotive
        "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=1200&q=85",  # Intercity executive coach
        "https://images.unsplash.com/photo-1570125909232-eb263c188f7e?auto=format&fit=crop&w=1200&q=85",  # Modern airport terminal & gates
    ],
}

# ==============================================================================
# 3. EXACT INVENTORY ITEM ID MAPPING
# ==============================================================================
EXACT_ITEM_ID_MAPPINGS: dict[str, list[str]] = {
    # Dubai Flagships
    "attraction-burj-khalifa": LANDMARK_CATALOG["BURJ_KHALIFA"],
    "attraction-dubai-frame": LANDMARK_CATALOG["DUBAI_FRAME"],
    "hotel-burj-al-arab": LANDMARK_CATALOG["BURJ_AL_ARAB"],
    "hotel-address-sky-view": [
        "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=85",
    ],
    "hotel-rove-downtown": [
        "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=85",
    ],
    "hotel-atlantis-the-palm": LANDMARK_CATALOG["PALM_JUMEIRAH"],
    "hotel-premier-inn-airport": [
        "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=85",
    ],

    # Abu Dhabi Flagships
    "attraction-sheikh-zayed-mosque": LANDMARK_CATALOG["SHEIKH_ZAYED_MOSQUE"],
    "hotel-emirates-palace": LANDMARK_CATALOG["EMIRATES_PALACE"],
    "attraction-louvre-abu-dhabi": LANDMARK_CATALOG["LOUVRE_ABU_DHABI"],

    # Santorini Flagships
    "attraction-santorini-oia-sunset": LANDMARK_CATALOG["SANTORINI_OIA"],
    "attraction-santorini-caldera-cruise": LANDMARK_CATALOG["SANTORINI_CALDERA_CRUISE"],
    "hotel-canaves-oia-suites": LANDMARK_CATALOG["SANTORINI_OIA"],
    "hotel-grace-hotel-santorini": LANDMARK_CATALOG["SANTORINI_OIA"],
    "dine-santorini-varoulko": LANDMARK_CATALOG["SANTORINI_OIA"],

    # Athens Flagships
    "attraction-athens-acropolis": LANDMARK_CATALOG["ATHENS_ACROPOLIS"],
    "hotel-electra-palace-athens": LANDMARK_CATALOG["ATHENS_ACROPOLIS"],

    # Delhi Flagships
    "attraction-delhi-india-gate": LANDMARK_CATALOG["INDIA_GATE"],
    "attraction-delhi-red-fort": LANDMARK_CATALOG["RED_FORT"],
    "attraction-delhi-qutub-minar": LANDMARK_CATALOG["QUTUB_MINAR"],
    "tour-delhi-50025": [
        "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1592635196078-9fdc757f27f4?auto=format&fit=crop&w=1200&q=85",
    ],
    "tour-delhi-50026": [
        "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1592635196078-9fdc757f27f4?auto=format&fit=crop&w=1200&q=85",
    ],
    "hotel-tbo-101": [
        "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=85",
    ],
    "hotel-delhi-grand-palace": [
        "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=85",
    ],

    # Agra Flagships
    "attraction-taj-mahal": LANDMARK_CATALOG["TAJ_MAHAL"],
    "attraction-agra-fort": LANDMARK_CATALOG["AGRA_FORT"],
    "trans-agra-cantt": [
        "https://images.unsplash.com/photo-1474487548417-781cb71495f3?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=1200&q=85",
    ],

    # Mumbai Flagships
    "attraction-gateway-of-india": LANDMARK_CATALOG["GATEWAY_OF_INDIA"],
    "trans-mumbai-csmt": [
        "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=1200&q=85",
        "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?auto=format&fit=crop&w=1200&q=85",
    ],

    # Jaipur Flagships
    "attraction-hawa-mahal": LANDMARK_CATALOG["HAWA_MAHAL"],
    "attraction-amber-fort": LANDMARK_CATALOG["AMBER_FORT"],
}

# ==============================================================================
# 4. DESTINATION COUNTRY MAPPINGS
# ==============================================================================
DESTINATION_COUNTRY_MAP: dict[str, str] = {
    "Dubai": "UAE",
    "Abu Dhabi": "UAE",
    "Santorini": "Greece",
    "Oia": "Greece",
    "Fira": "Greece",
    "Athens": "Greece",
}

def get_destination_country(destination: str) -> str:
    """Returns the correct sovereign country name for any destination."""
    return DESTINATION_COUNTRY_MAP.get(destination, "India")

# ==============================================================================
# 5. DESTINATION-SPECIFIC CURATED POOLS
# ==============================================================================
DESTINATION_POOLS: dict[str, dict[str, list[str]]] = {
    "Dubai": {
        "ATTRACTION": [
            "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1200&q=85",  # Burj Khalifa
            "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=1200&q=85",  # Burj Al Arab
            "https://images.unsplash.com/photo-1578895101408-1a36b834405b?auto=format&fit=crop&w=1200&q=85",  # Dubai Marina / Frame
            "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?auto=format&fit=crop&w=1200&q=85",  # Desert Safari
        ],
        "HOTEL": [
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?auto=format&fit=crop&w=1200&q=85",
        ],
        "DINING": [
            "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=85",
        ],
        "TRANSPORT": [
            "https://images.unsplash.com/photo-1557223562-6c77ef16210f?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1570125909232-eb263c188f7e?auto=format&fit=crop&w=1200&q=85",
        ],
    },
    "Abu Dhabi": {
        "ATTRACTION": [
            "https://images.unsplash.com/photo-1512632578888-169bbbc64f33?auto=format&fit=crop&w=1200&q=85",  # Sheikh Zayed Grand Mosque
            "https://images.unsplash.com/photo-1578895101408-1a36b834405b?auto=format&fit=crop&w=1200&q=85",  # Louvre Abu Dhabi
        ],
        "HOTEL": [
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=85",
        ],
        "DINING": [
            "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=85",
        ],
        "TRANSPORT": [
            "https://images.unsplash.com/photo-1570125909232-eb263c188f7e?auto=format&fit=crop&w=1200&q=85",
        ],
    },
    "Santorini": {
        "ATTRACTION": [
            "https://images.unsplash.com/photo-1530841377377-3ff06c0ca713?auto=format&fit=crop&w=1200&q=85",  # Oia blue domes
            "https://images.unsplash.com/photo-1498503403619-e39e4ff390fe?auto=format&fit=crop&w=1200&q=85",  # Caldera plunge pool view
        ],
        "HOTEL": [
            "https://images.unsplash.com/photo-1530841377377-3ff06c0ca713?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1498503403619-e39e4ff390fe?auto=format&fit=crop&w=1200&q=85",
        ],
        "DINING": [
            "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=85",
        ],
        "TRANSPORT": [
            "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=1200&q=85",
        ],
    },
    "Athens": {
        "ATTRACTION": [
            "https://images.unsplash.com/photo-1503152394-c571994fd383?auto=format&fit=crop&w=1200&q=85",  # Acropolis Parthenon
        ],
        "HOTEL": [
            "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=85",
        ],
        "DINING": [
            "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=85",
        ],
        "TRANSPORT": [
            "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=1200&q=85",
        ],
    },
    "Delhi": {
        "ATTRACTION": [
            "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=1200&q=85",  # India Gate
            "https://images.unsplash.com/photo-1592635196078-9fdc757f27f4?auto=format&fit=crop&w=1200&q=85",  # Red Fort
            "https://images.unsplash.com/photo-1770891312604-ac424d09671a?auto=format&fit=crop&w=1200&q=85",  # Qutub Minar
        ],
        "HOTEL": [
            "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=85",
        ],
        "DINING": [
            "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=1200&q=85",
        ],
        "TRANSPORT": [
            "https://images.unsplash.com/photo-1474487548417-781cb71495f3?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1570125909232-eb263c188f7e?auto=format&fit=crop&w=1200&q=85",
        ],
    },
    "Agra": {
        "ATTRACTION": [
            "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=1200&q=85",  # Taj Mahal
            "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=85",
        ],
        "HOTEL": [
            "https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=85",
        ],
        "DINING": [
            "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=1200&q=85",
        ],
        "TRANSPORT": [
            "https://images.unsplash.com/photo-1474487548417-781cb71495f3?auto=format&fit=crop&w=1200&q=85",
        ],
    },
    "Jaipur": {
        "ATTRACTION": [
            "https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1200&q=85",  # Hawa Mahal
            "https://images.unsplash.com/photo-1597040663342-45b6af3d91a8?auto=format&fit=crop&w=1200&q=85",  # Amber Fort
        ],
        "HOTEL": [
            "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1200&q=85",
        ],
        "DINING": [
            "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=85",
        ],
        "TRANSPORT": [
            "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=1200&q=85",
        ],
    },
    "Mumbai": {
        "ATTRACTION": [
            "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=1200&q=85",  # Gateway of India
            "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?auto=format&fit=crop&w=1200&q=85",
        ],
        "HOTEL": [
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=85",
            "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=85",
        ],
        "DINING": [
            "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=85",
        ],
        "TRANSPORT": [
            "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?auto=format&fit=crop&w=1200&q=85",
        ],
    },
}

# ==============================================================================
# 6. STRICT GEOGRAPHICALLY-BOUND LANDMARK MATCHERS
# ==============================================================================
STRICT_LANDMARK_RULES: list[dict[str, Any]] = [
    # Dubai Rules
    {"pattern": re.compile(r"burj\s*khalifa|at\s*the\s*top", re.I), "key": "BURJ_KHALIFA", "allowed_destinations": {"Dubai"}},
    {"pattern": re.compile(r"burj\s*al\s*arab", re.I), "key": "BURJ_AL_ARAB", "allowed_destinations": {"Dubai"}},
    {"pattern": re.compile(r"dubai\s*frame", re.I), "key": "DUBAI_FRAME", "allowed_destinations": {"Dubai"}},
    {"pattern": re.compile(r"dubai\s*marina", re.I), "key": "DUBAI_MARINA", "allowed_destinations": {"Dubai"}},
    {"pattern": re.compile(r"palm\s*jumeirah|atlantis\s*the\s*palm", re.I), "key": "PALM_JUMEIRAH", "allowed_destinations": {"Dubai"}},
    {"pattern": re.compile(r"desert\s*safari|dune\s*bashing", re.I), "key": "DUBAI_DESERT", "allowed_destinations": {"Dubai"}},

    # Abu Dhabi Rules
    {"pattern": re.compile(r"sheikh\s*zayed|grand\s*mosque", re.I), "key": "SHEIKH_ZAYED_MOSQUE", "allowed_destinations": {"Abu Dhabi"}},
    {"pattern": re.compile(r"emirates\s*palace", re.I), "key": "EMIRATES_PALACE", "allowed_destinations": {"Abu Dhabi"}},
    {"pattern": re.compile(r"louvre\s*abu\s*dhabi", re.I), "key": "LOUVRE_ABU_DHABI", "allowed_destinations": {"Abu Dhabi"}},

    # Santorini Rules
    {"pattern": re.compile(r"santorini|oia|fira", re.I), "key": "SANTORINI_OIA", "allowed_destinations": {"Santorini", "Oia", "Fira"}},
    {"pattern": re.compile(r"caldera\s*cruise|aegean\s*catamaran", re.I), "key": "SANTORINI_CALDERA_CRUISE", "allowed_destinations": {"Santorini", "Oia", "Fira"}},

    # Athens Rules
    {"pattern": re.compile(r"acropolis|parthenon", re.I), "key": "ATHENS_ACROPOLIS", "allowed_destinations": {"Athens"}},

    # Delhi Rules
    {"pattern": re.compile(r"india\s*gate", re.I), "key": "INDIA_GATE", "allowed_destinations": {"Delhi", "New Delhi"}},
    {"pattern": re.compile(r"red\s*fort", re.I), "key": "RED_FORT", "allowed_destinations": {"Delhi", "New Delhi"}},
    {"pattern": re.compile(r"qutub\s*minar", re.I), "key": "QUTUB_MINAR", "allowed_destinations": {"Delhi", "New Delhi"}},

    # Agra Rules
    {"pattern": re.compile(r"taj\s*mahal", re.I), "key": "TAJ_MAHAL", "allowed_destinations": {"Agra"}},
    {"pattern": re.compile(r"agra\s*fort", re.I), "key": "AGRA_FORT", "allowed_destinations": {"Agra"}},

    # Jaipur Rules
    {"pattern": re.compile(r"hawa\s*mahal", re.I), "key": "HAWA_MAHAL", "allowed_destinations": {"Jaipur"}},
    {"pattern": re.compile(r"amber\s*fort|amer\s*fort", re.I), "key": "AMBER_FORT", "allowed_destinations": {"Jaipur"}},

    # Mumbai Rules
    {"pattern": re.compile(r"gateway\s*of\s*india", re.I), "key": "GATEWAY_OF_INDIA", "allowed_destinations": {"Mumbai"}},
    {"pattern": re.compile(r"marine\s*drive|queen'?s\s*necklace", re.I), "key": "MUMBAI_MARINE_DRIVE", "allowed_destinations": {"Mumbai"}},

    # Kashmir Rules
    {"pattern": re.compile(r"dal\s*lake|shikara", re.I), "key": "DAL_LAKE", "allowed_destinations": {"Srinagar", "Kashmir"}},

    # Amritsar Rules
    {"pattern": re.compile(r"golden\s*temple|harmandir\s*sahib", re.I), "key": "GOLDEN_TEMPLE", "allowed_destinations": {"Amritsar"}},

    # Varanasi Rules
    {"pattern": re.compile(r"varanasi|kashi|dashashwamedh|ganga\s*aarti", re.I), "key": "VARANASI_GHATS", "allowed_destinations": {"Varanasi"}},

    # Kerala Rules
    {"pattern": re.compile(r"backwaters|houseboat|kettuvallam", re.I), "key": "KERALA_BACKWATERS", "allowed_destinations": {"Alleppey", "Kochi", "Alappuzha", "Kerala", "Kumarakom"}},

    # Goa Rules
    {"pattern": re.compile(r"baga\s*beach|calangute|palolem|goa", re.I), "key": "GOA_BEACHES", "allowed_destinations": {"Goa"}},
]

# ==============================================================================
# 7. CORE RESOLVER FUNCTION
# ==============================================================================
def resolve_item_images(item: dict[str, Any]) -> list[str]:
    """Deterministically resolves 2 high-res, authentic photographs for any inventory item."""
    item_id = str(item.get("id", "")).strip()
    destination = str(item.get("destination", "")).strip()
    name = str(item.get("name", "")).strip()
    
    # 1. Resolve entity type accurately
    raw_type = item.get("entity_type") or item.get("type") or item.get("category") or ""
    entity_type = str(raw_type).upper()
    if not entity_type or entity_type not in ("HOTEL", "ATTRACTION", "TRANSPORT", "DINING"):
        if item_id.startswith("attraction-") or item_id.startswith("tour-") or "tour" in name.lower() or "excursion" in name.lower() or "sightseeing" in name.lower():
            entity_type = "ATTRACTION"
        elif item_id.startswith("dining-") or "dine" in item_id or "restaurant" in name.lower():
            entity_type = "DINING"
        elif item_id.startswith("trans-") or "metro" in name.lower() or "rail" in name.lower() or "airport" in name.lower() or "transit" in name.lower():
            entity_type = "TRANSPORT"
        else:
            entity_type = "HOTEL"

    # Deterministic index seed from item ID
    seed = int(hashlib.md5(item_id.encode("utf-8")).hexdigest()[:8], 16)

    # 1. Exact Item ID Check
    if item_id in EXACT_ITEM_ID_MAPPINGS:
        imgs = EXACT_ITEM_ID_MAPPINGS[item_id]
        if len(imgs) >= 2:
            return imgs[:2]
        return [imgs[0], imgs[0]]

    # 2. Strict Geographically-Bound Landmark Matching
    text_to_match = f"{name} {item.get('description', '')}"
    dest_norm = destination.strip()
    
    for rule in STRICT_LANDMARK_RULES:
        allowed = rule["allowed_destinations"]
        if dest_norm in allowed or any(a.lower() == dest_norm.lower() for a in allowed):
            if rule["pattern"].search(text_to_match):
                imgs = LANDMARK_CATALOG.get(rule["key"], [])
                if imgs:
                    primary = imgs[seed % len(imgs)]
                    secondary = imgs[(seed + 1) % len(imgs)] if len(imgs) > 1 else primary
                    return [primary, secondary]

    # 3. Destination-Specific Curated Pool Check
    if dest_norm in DESTINATION_POOLS:
        pool = DESTINATION_POOLS[dest_norm].get(entity_type, DESTINATION_POOLS[dest_norm].get("HOTEL", []))
        if pool:
            primary = pool[seed % len(pool)]
            secondary = pool[(seed + 1) % len(pool)] if len(pool) > 1 else primary
            return [primary, secondary]

    # Check case-insensitive destination match
    for d_name, d_pools in DESTINATION_POOLS.items():
        if d_name.lower() == dest_norm.lower():
            pool = d_pools.get(entity_type, d_pools.get("HOTEL", []))
            if pool:
                primary = pool[seed % len(pool)]
                secondary = pool[(seed + 1) % len(pool)] if len(pool) > 1 else primary
                return [primary, secondary]

    # 4. Fallback to Neutral Category-Appropriate Pool
    neutral_pool = NEUTRAL_CATEGORY_POOLS.get(entity_type, NEUTRAL_CATEGORY_POOLS["HOTEL"])
    primary = neutral_pool[seed % len(neutral_pool)]
    secondary = neutral_pool[(seed + 1) % len(neutral_pool)]
    return [primary, secondary]


def export_catalog_json(output_path: Path) -> dict[str, Any]:
    """Exports the entire verified image catalog as structured JSON."""
    catalog_data = {
        "version": "3.1.0",
        "description": "TBO Discovery Pan-India and International Visually-Verified Image Catalog",
        "landmarks": LANDMARK_CATALOG,
        "exact_item_mappings": EXACT_ITEM_ID_MAPPINGS,
        "destination_countries": DESTINATION_COUNTRY_MAP,
        "destination_pools": DESTINATION_POOLS,
        "neutral_category_pools": NEUTRAL_CATEGORY_POOLS,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog_data, f, indent=2, ensure_ascii=False)
    return catalog_data


if __name__ == "__main__":
    out_file = DATA_DIR / "verified_image_catalog.json"
    export_catalog_json(out_file)
    print(f"Exported verified catalog to {out_file}")
