"""Normalize common supplier room abbreviations into readable room labels."""

from __future__ import annotations

import re

REPLACEMENTS = (
    (r"\bDLX\b", "Deluxe"),
    (r"\bSUP\b", "Superior"),
    (r"\bSTD\b", "Standard"),
    (r"\bSTE\b", "Suite"),
    (r"\bDBL\b", "Double"),
    (r"\bTWN?\b", "Twin"),
    (r"\bSGL\b", "Single"),
    (r"\bTRPL\b", "Triple"),
    (r"\bOCVW\b|\bOV\b", "Ocean View"),
    (r"\bSEAVW\b|\bSV\b", "Sea View"),
    (r"\bCVW\b|\bCV\b", "City View"),
    (r"\bW\s*/\s*BALC\b|\bBALC\b", "with Balcony"),
    (r"\bRO\b", "Room Only"),
    (r"\bBB\b", "Bed and Breakfast"),
)


def normalize_room(raw_name: str) -> str:
    normalized = raw_name.upper().replace("_", " ")
    normalized = re.sub(r"[-/,]+", " ", normalized)
    for pattern, replacement in REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", normalized).strip(" -")
    return normalized[:1].upper() + normalized[1:] if normalized else "Unknown Room"
