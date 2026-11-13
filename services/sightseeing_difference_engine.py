"""Extract comparable sightseeing inclusions from supplier descriptions."""

from __future__ import annotations

import re

PATTERNS = {
    "transfer": {
        "PRIVATE": (r"\bprivate\s+(?:hotel\s+)?transfer\b", r"\bprivate\s+pick.?up\b"),
        "SHARED": (r"\bshared\s+(?:hotel\s+)?transfer\b", r"\bseat.?in.?coach\b"),
    },
    "meal": {
        "BREAKFAST": (r"\bbreakfast\b",),
        "BUFFET_LUNCH": (r"\bbuffet\s+lunch\b",),
        "LUNCH": (r"\blunch\b",),
        "DINNER": (r"\bdinner\b",),
    },
    "access": {
        "SKIP_THE_LINE": (r"\bskip[- ]the[- ]line\b", r"\bfast.?track\b"),
        "GENERAL_ADMISSION": (r"\bgeneral admission\b", r"\badmission ticket\b"),
    },
}


def extract_inclusions(description: str) -> dict[str, list[str]]:
    text = description.casefold()
    return {
        category: [
            label
            for label, expressions in labels.items()
            if any(re.search(expression, text) for expression in expressions)
        ]
        for category, labels in PATTERNS.items()
    }


def compare_inclusions(left: str, right: str) -> dict[str, dict[str, list[str]]]:
    a, b = extract_inclusions(left), extract_inclusions(right)
    return {
        category: {
            "shared": sorted(set(a[category]) & set(b[category])),
            "only_left": sorted(set(a[category]) - set(b[category])),
            "only_right": sorted(set(b[category]) - set(a[category])),
        }
        for category in PATTERNS
    }
