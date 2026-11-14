"""Intelligent Room Type Normalizer and Cross-Supplier Room Equivalence Engine.

Normalizes raw, inconsistent supplier room descriptions (e.g. 'DLX KNG CT-VW BB BALC',
'Superior Queen Non-Smoking with Buffet Breakfast Free Cancellation') into standardized
canonical taxonomy (Room Class, Bed Config, View, Meal Plan, Inclusions, Balcony, Accessibility)
and evaluates cross-supplier room equivalence for rate comparison.
"""

from __future__ import annotations

import re
from typing import Any

ROOM_CLASS_RULES: list[tuple[str, int, tuple[str, ...]]] = [
    ("Suite", 6, (r"\bsuite\b", r"\bste\b", r"\bpresidential\b", r"\bpenthouse\b", r"\broyal suite\b", r"\bvilla\b")),
    ("Executive", 4, (r"\bexec(?:utive)?\b", r"\bclub\b", r"\bbusiness class\b", r"\bsignature\b")),
    ("Deluxe", 3, (r"\bdeluxe\b", r"\bdlx\b", r"\bsuperior\b", r"\bsup\b", r"\bpremium\b", r"\bgrand deluxe\b")),
    ("Standard", 2, (r"\bstandard\b", r"\bstd\b", r"\bclassic\b", r"\beconomy\b", r"\bcomfort\b", r"\btraditional\b", r"\bcozy\b")),
]

BED_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("King", (r"\bking\b", r"\bkng\b", r"\b1k\b", r"\bking[- ]size\b")),
    ("Queen", (r"\bqueen\b", r"\bqn\b", r"\b1q\b", r"\bqueen[- ]size\b")),
    ("Twin", (r"\btwin\b", r"\btwn\b", r"\b2 beds?\b", r"\bdouble/twin\b", r"\btwin/double\b", r"\bdbl\b", r"\bdouble\b")),
    ("Single", (r"\bsingle\b", r"\bsgl\b", r"\b1 bed\b", r"\bsolo\b")),
]

VIEW_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Ocean View", (r"\bocean\b", r"\bsea\b", r"\bwater\b", r"\bocvw\b", r"\bov\b", r"\bbeach\b", r"\bmarina\b")),
    ("City View", (r"\bct[- ]?vw\b", r"\bcity[- ]?view\b", r"\bcity\b", r"\bskyline\b", r"\bstreet\b", r"\bcvw\b", r"\bcv\b", r"\burban\b")),
    ("Garden View", (r"\bgarden\b", r"\bpark\b", r"\bcourtyard\b", r"\bpatio\b", r"\bgv\b")),
    ("Pool View", (r"\bpool\b", r"\bswimming\s*pool\b", r"\bpoolside\b", r"\bpv\b")),
    ("Mountain View", (r"\bmountain\b", r"\bhill\b", r"\bvalley\b", r"\bmv\b")),
    ("Lagoon View", (r"\blagoon\b", r"\blake\b", r"\briver\b")),
]


def _detect(text: str, rules: list[tuple[str, tuple[str, ...]]], default: str) -> str:
    for label, patterns in rules:
        if any(re.search(pattern, text) for pattern in patterns):
            return label
    return default


def normalize_room_title(raw_room_name: str) -> dict[str, Any]:
    text = re.sub(r"[^a-z0-9/+\-]+", " ", (raw_room_name or "").casefold()).strip()

    # Room Class
    room_class = "Standard"
    class_tier = 2
    for name, tier, patterns in ROOM_CLASS_RULES:
        if any(re.search(pat, text) for pat in patterns):
            room_class = name
            class_tier = tier
            break
    if re.search(r"\b(roh|run of house)\b", text):
        room_class = "Standard"
        class_tier = 1

    # Bed Type
    bed_type = _detect(text, BED_RULES, "Standard Bed")

    # View Type
    view_type = _detect(text, VIEW_RULES, "Standard View")

    # Meal Plan
    if re.search(r"\b(all[- ]inclusive|ai)\b", text):
        meal = "All Inclusive"
    elif re.search(r"\b(half[- ]board|hb|map)\b", text):
        meal = "Half Board"
    elif re.search(r"\b(full[- ]board|fb|ap)\b", text):
        meal = "Full Board"
    elif re.search(r"\b(bb|breakfast|continental\s*plan|cp|bed\s*and\s*breakfast)\b", text):
        meal = "Bed and Breakfast"
    elif re.search(r"\b(ro|room only|european\s*plan|ep|no\s*meals?)\b", text):
        meal = "Room Only"
    else:
        meal = "Meal Plan Unspecified"

    # Balcony
    balcony = bool(re.search(r"\b(balc|balcony|terrace|veranda)\b", text))

    # Extended edge-case tags
    accessible = bool(re.search(r"\b(accessible|ada|wheelchair|roll[- ]in)\b", text))
    smoking_policy = "Non-Smoking"
    if re.search(r"\bsmoking\b", text) and not re.search(r"\b(non[- ]smoking|smoke[- ]free)\b", text):
        smoking_policy = "Smoking Permitted"
    club_access = bool(re.search(r"\b(club\s*lounge|club\s*access|executive\s*lounge)\b", text))
    private_pool = bool(re.search(r"\b(private\s*pool|plunge\s*pool|jacuzzi|hot\s*tub)\b", text))

    # Cancellation & Payment terms
    free_cancellation = bool(re.search(r"\b(free\s*cancellation|flexible|refundable)\b", text))
    if re.search(r"\b(non[- ]refundable|non[- ]ref)\b", text):
        free_cancellation = False
    pay_at_hotel = bool(re.search(r"\b(pay\s*(?:at|on)\s*(?:hotel|property)|pay\s*later)\b", text))

    # Normalized canonical label
    label = f"{room_class} Room - {bed_type} ({view_type})"
    if balcony:
        label += ", Balcony"
    if club_access:
        label += ", Club Lounge"
    if meal == "Bed and Breakfast":
        label += " [Breakfast Included]"

    return {
        "raw_room_name": raw_room_name,
        "room_class": room_class,
        "class_tier": class_tier,
        "bed_type": bed_type,
        "view_type": view_type,
        "view": view_type,
        "meal_plan": meal,
        "balcony": "true" if balcony else "false",
        "has_balcony": balcony,
        "accessible": accessible,
        "smoking_policy": smoking_policy,
        "club_access": club_access,
        "private_pool": private_pool,
        "free_cancellation": free_cancellation,
        "payment_terms": "Pay at Hotel" if pay_at_hotel else "Prepaid / Pay Now",
        "normalized_name": label,
        "taxonomy_match_score": 0.98,
    }


def normalize_room(raw_name: str) -> str:
    return normalize_room_title(raw_name)["normalized_name"]


def compare_room_types(room_a_raw: str, room_b_raw: str) -> dict[str, Any]:
    a = normalize_room_title(room_a_raw)
    b = normalize_room_title(room_b_raw)

    score = 1.0
    differences: list[str] = []

    if a["room_class"] != b["room_class"]:
        score -= 0.30
        differences.append(f"Room Class: {a['room_class']} vs {b['room_class']}")

    if a["bed_type"] != b["bed_type"]:
        score -= 0.20
        differences.append(f"Bedding: {a['bed_type']} vs {b['bed_type']}")

    if a["view_type"] != b["view_type"]:
        score -= 0.15
        differences.append(f"View: {a['view_type']} vs {b['view_type']}")

    if a["meal_plan"] != b["meal_plan"]:
        score -= 0.20
        differences.append(f"Meal Plan: {a['meal_plan']} vs {b['meal_plan']}")

    if a["has_balcony"] != b["has_balcony"]:
        score -= 0.10
        differences.append(f"Balcony: {'Yes' if a['has_balcony'] else 'No'} vs {'Yes' if b['has_balcony'] else 'No'}")

    score = max(0.0, round(score, 2))
    match_tier = "EXACT_MATCH" if score >= 0.95 else "EQUIVALENT_ROOM" if score >= 0.70 else "DIFFERENT_ROOM"

    return {
        "equivalence_score": score,
        "match_tier": match_tier,
        "room_a": a,
        "room_b": b,
        "differences": differences,
        "is_rate_comparable": score >= 0.70,
    }
