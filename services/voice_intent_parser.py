"""Local rules-based travel intent parser with no paid API or model download."""

from __future__ import annotations

import re

# This demo is deliberately limited to the bundled Delhi open-data snapshot.
# Keep aliases local so voice queries cannot imply coverage for other cities.
DESTINATIONS = ("new delhi", "delhi")
DESTINATION_ALIASES = {"new delhi": "Delhi", "delhi": "Delhi"}
LANDMARKS = (
    "india gate", "qutub minar", "red fort", "humayun's tomb", "humayuns tomb",
    "lotus temple", "akshardham", "jama masjid", "connaught place", "lodhi garden",
    "national museum", "rashtrapati bhavan", "purana qila", "delhi airport",
)
INCLUSION_TERMS = {
    "free breakfast": "BREAKFAST",
    "breakfast": "BREAKFAST",
    "bed and breakfast": "BREAKFAST",
    "wifi": "WIFI",
    "wi-fi": "WIFI",
    "swimming pool": "POOL",
    "pool": "POOL",
    "free cancellation": "FREE_CANCELLATION",
    "flexible cancellation": "FREE_CANCELLATION",
    "cancellation": "FREE_CANCELLATION",
    "transfer": "TRANSFERS",
    "pickup": "TRANSFERS",
    "pick up": "TRANSFERS",
    "skip the line": "SKIP_THE_LINE",
    "fast track": "SKIP_THE_LINE",
    "private transfer": "PRIVATE_TRANSFER",
}


def parse_voice_travel_query(transcript: str) -> dict[str, object]:
    text = transcript.strip()
    lowered = text.casefold()
    sightseeing = bool(
        re.search(r"\b(tour|ticket|experience|sightseeing|attraction|museum|safari|cruise)\b", lowered)
        or any(place in lowered for place in LANDMARKS)
    )
    result: dict[str, object] = {
        "raw_query": text,
        "destination": None,
        "entity_type": "SIGHTSEEING" if sightseeing else "HOTEL",
        "star_rating": None,
        "max_price": None,
        "country_code": "IN",
        "currency": "INR",
        "inclusions": [],
        "landmark": None,
        "date_window": None,
    }
    star = re.search(r"\b([1-5])\s*[- ]?star\b", lowered)
    if star:
        result["star_rating"] = float(star.group(1))
    price = re.search(
        r"\b(?:under|below|less than|max(?:imum)?|up to)\s*(?:\$\s*|usd\s*|aed\s*|inr\s*)?([\d,]+(?:\.\d+)?)",
        lowered,
    ) or re.search(r"(?:\$|\b(?:usd|aed|inr)\s*)([\d,]+(?:\.\d+)?)", lowered)
    if price:
        result["max_price"] = float(price.group(1).replace(",", ""))
    currency = re.search(r"\b(usd|aed|inr|rupees?|rs\.?|dollars?|dirhams?|eur|gbp)\b|\$|€|£|₹", lowered)
    if currency:
        symbol = currency.group(0)
        result["currency"] = {
            "$": "USD", "€": "EUR", "£": "GBP", "₹": "INR",
            "rupee": "INR", "rupees": "INR", "rs": "INR", "rs.": "INR",
            "dollar": "USD", "dollars": "USD", "dirham": "AED", "dirhams": "AED",
        }.get(symbol, symbol.upper())
    if re.search(r"\b(united arab emirates|uae|emirates)\b", lowered):
        result["country_code"] = "AE"
        if not currency:
            result["currency"] = "USD"
    elif re.search(r"\b(india|indian)\b", lowered):
        result["country_code"] = "IN"
    for destination in DESTINATIONS:
        if re.search(rf"\b{re.escape(destination)}\b", lowered):
            result["destination"] = DESTINATION_ALIASES[destination]
            break
    for landmark in LANDMARKS:
        if re.search(rf"\b{re.escape(landmark)}\b", lowered):
            result["landmark"] = landmark.title()
            break
    result["inclusions"] = sorted(
        {label for phrase, label in INCLUSION_TERMS.items() if re.search(rf"\b{re.escape(phrase)}\b", lowered)}
    )
    if re.search(r"\bnext weekend\b", lowered):
        result["date_window"] = "NEXT_WEEKEND"
    elif re.search(r"\bthis weekend\b", lowered):
        result["date_window"] = "THIS_WEEKEND"
    return result


def parse_voice_query(transcript: str) -> dict[str, object]:
    """Compatibility alias used by the first demo API."""
    return parse_voice_travel_query(transcript)
