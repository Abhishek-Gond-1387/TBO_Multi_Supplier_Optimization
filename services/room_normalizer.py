"""Normalize common supplier room abbreviations into readable room labels."""

from __future__ import annotations

import re

ROOM_CLASS_RULES = {
    "Suite": (r"\bsuite\b", r"\bste\b", r"\bpresidential\b", r"\bpenthouse\b"),
    "Executive": (r"\bexec(?:utive)?\b", r"\bclub\b"),
    "Deluxe": (r"\bdeluxe\b", r"\bdlx\b", r"\bsuperior\b", r"\bsup\b", r"\bpremium\b"),
    "Standard": (r"\bstandard\b", r"\bstd\b", r"\bclassic\b", r"\beconomy\b"),
}
BED_RULES = {
    "King": (r"\bking\b", r"\bkng\b", r"\b1k\b"),
    "Queen": (r"\bqueen\b", r"\bqn\b", r"\b1q\b"),
    "Twin": (r"\btwin\b", r"\btwn\b", r"\b2 beds?\b", r"\bdouble/twin\b", r"\bdbl\b"),
    "Single": (r"\bsingle\b", r"\bsgl\b", r"\b1 bed\b"),
}
VIEW_RULES = {
    "Ocean View": (r"\bocean\b", r"\bsea\b", r"\bwater\b", r"\bocvw\b", r"\bov\b", r"\bbeach\b"),
    "City View": (r"\bcity\b", r"\bskyline\b", r"\bstreet\b", r"\bcvw\b", r"\bcv\b"),
    "Garden View": (r"\bgarden\b", r"\bpark\b", r"\bcourtyard\b"),
    "Pool View": (r"\bpool\b",),
}


def _detect(text: str, rules: dict[str, tuple[str, ...]], default: str) -> str:
    for label, patterns in rules.items():
        if any(re.search(pattern, text) for pattern in patterns):
            return label
    return default


def normalize_room_title(raw_room_name: str) -> dict[str, str]:
    text = re.sub(r"[^a-z0-9/]+", " ", raw_room_name.casefold()).strip()
    room_class = _detect(text, ROOM_CLASS_RULES, "Standard")
    bed_type = _detect(text, BED_RULES, "Standard Bed")
    view_type = _detect(text, VIEW_RULES, "Standard View")
    meal = "Room Only" if re.search(r"\b(ro|room only)\b", text) else "Bed and Breakfast" if re.search(r"\b(bb|breakfast)\b", text) else "Meal Plan Unspecified"
    balcony = bool(re.search(r"\b(balc|balcony)\b", text))
    label = f"{room_class} Room - {bed_type} ({view_type})"
    if balcony:
        label += ", Balcony"
    return {
        "room_class": room_class,
        "bed_type": bed_type,
        "view_type": view_type,
        "meal_plan": meal,
        "balcony": str(balcony).lower(),
        "normalized_name": label,
    }


def normalize_room(raw_name: str) -> str:
    return normalize_room_title(raw_name)["normalized_name"]
