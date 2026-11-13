"""Rule-based travel query parser; runs locally without paid NLP services."""

from __future__ import annotations

import re

INCLUSION_TERMS = {
    "breakfast": "BREAKFAST",
    "free breakfast": "BREAKFAST",
    "pool": "POOL",
    "swimming pool": "POOL",
    "wifi": "WIFI",
    "wi-fi": "WIFI",
    "cancellation": "FLEXIBLE_CANCELLATION",
    "free cancellation": "FLEXIBLE_CANCELLATION",
}


def parse_voice_query(transcript: str) -> dict[str, object]:
    text = transcript.strip()
    lowered = text.casefold()
    result: dict[str, object] = {
        "transcript": text,
        "entity_type": "HOTEL" if re.search(r"\bhotel|resort|stay\b", lowered) else "ANY",
        "destination": None,
        "star_rating": None,
        "max_price": None,
        "landmark": None,
        "inclusions": [],
    }
    star_match = re.search(r"\b([1-5])\s*[- ]?star\b", lowered)
    if star_match:
        result["star_rating"] = float(star_match.group(1))
    price_match = re.search(
        r"\b(?:under|below|less than|max(?:imum)?|up to)\s*(?:\$|usd\s*)?([\d,]+(?:\.\d+)?)",
        lowered,
    ) or re.search(r"\$\s*([\d,]+(?:\.\d+)?)", lowered)
    if price_match:
        result["max_price"] = float(price_match.group(1).replace(",", ""))
    destination_match = re.search(r"\bin\s+([a-z][a-z .'-]*?)(?=\s+(?:near|with|under|below|for|at)\b|[,;.!?]|$)", text, re.I)
    if destination_match:
        result["destination"] = destination_match.group(1).strip().title()
    landmark_match = re.search(r"\bnear\s+(?:the\s+)?([a-z][a-z '-]*?)(?=\s+(?:with|under|below|for)\b|[,;.!?]|$)", text, re.I)
    if landmark_match:
        result["landmark"] = landmark_match.group(1).strip().title()
    inclusions = {
        label
        for phrase, label in INCLUSION_TERMS.items()
        if re.search(rf"\b{re.escape(phrase)}\b", lowered)
    }
    result["inclusions"] = sorted(inclusions)
    return result
