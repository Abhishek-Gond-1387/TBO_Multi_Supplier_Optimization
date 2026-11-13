"""Extract comparable sightseeing inclusions from supplier descriptions."""

from __future__ import annotations

import re
import os
from functools import lru_cache
from typing import Any

TRANSFER_PRIVATE = r"\bprivate\s+(?:hotel\s+)?(?:transfer|car|chauffeur|pickup|pick.?up|vehicle)\b"
TRANSFER_SHARED = r"\b(shared|hotel\s+pickup|round.?trip\s+transfer|coach\s+transfer|seat.?in.?coach)\b"


@lru_cache(maxsize=1)
def _zero_shot_pipeline():
    from transformers import pipeline

    return pipeline(
        "zero-shot-classification",
        model=os.getenv("ZERO_SHOT_MODEL_NAME", "facebook/bart-large-mnli"),
        device=-1,
    )


def _classify_optional(text: str, labels: list[str]) -> str | None:
    if os.getenv("ENABLE_ZERO_SHOT_INCLUSIONS", "false").strip().lower() not in {"true", "1", "yes"}:
        return None
    try:
        result = _zero_shot_pipeline()(text, candidate_labels=labels, multi_label=False)
        if result["scores"][0] >= 0.62:
            return result["labels"][0]
    except (ImportError, OSError, RuntimeError, KeyError, IndexError):
        pass
    return None


def extract_inclusions(description: str) -> dict[str, list[str]]:
    parsed = extract_tour_inclusions("", description, [])
    return {
        "transfer": [parsed["transfer"]] if parsed["transfer"] != "NONE" else [],
        "meal": [parsed["meal"]] if parsed["meal"] != "NONE" else [],
        "access": [parsed["access"]] if parsed["access"] != "STANDARD" else [],
        "cancellation": [parsed["cancellation"]],
        "guide_language": [parsed["guide_language"]],
    }


def extract_tour_inclusions(
    title: str, description: str, inclusions_list: list[str] | None = None
) -> dict[str, Any]:
    corpus = " ".join([title, description, *(inclusions_list or [])]).casefold()
    if re.search(r"\b(no|without|not included|excluded)\s+(?:hotel\s+)?(?:transfer|pickup|pick up)\b", corpus):
        transfer = "NONE"
    elif re.search(TRANSFER_PRIVATE, corpus):
        transfer = "PRIVATE"
    elif re.search(TRANSFER_SHARED, corpus):
        transfer = "SHARED"
    else:
        predicted_transfer = _classify_optional(corpus, ["no transfer", "shared transfer", "private transfer"])
        transfer = {"shared transfer": "SHARED", "private transfer": "PRIVATE"}.get(predicted_transfer, "NONE")
    if re.search(r"\b(dinner|gourmet meal)\b", corpus):
        meal = "DINNER"
    elif re.search(r"\b(lunch)\b", corpus):
        meal = "LUNCH"
    elif re.search(r"\b(breakfast)\b", corpus):
        meal = "BREAKFAST"
    elif re.search(r"\b(snacks|refreshments|drinks?|beverage)\b", corpus):
        meal = "SNACKS"
    else:
        predicted_meal = _classify_optional(corpus, ["no meal included", "breakfast included", "lunch included", "dinner included", "snacks included"])
        meal = {
            "breakfast included": "BREAKFAST",
            "lunch included": "LUNCH",
            "dinner included": "DINNER",
            "snacks included": "SNACKS",
        }.get(predicted_meal, "NONE")
    if re.search(r"\b(vip|lounge|level\s*148|luxury\s+access)\b", corpus):
        access = "VIP_LOUNGE"
    elif re.search(r"\b(skip[- ]the[- ]line|fast[- ]track|priority\s+entrance|express\s+entry)\b", corpus):
        access = "SKIP_THE_LINE"
    elif re.search(r"\b(general admission|standard entry|admission ticket)\b", corpus):
        access = "GENERAL_ADMISSION"
    else:
        access = _classify_optional(corpus, ["standard general admission", "skip the line access", "VIP lounge access"]) or "STANDARD"
        access = {
            "standard general admission": "GENERAL_ADMISSION",
            "skip the line access": "SKIP_THE_LINE",
            "VIP lounge access": "VIP_LOUNGE",
        }.get(access, access)
    hours = re.search(r"(\d+(?:\.\d+)?)\s*(hours?|hrs?)\b", corpus)
    minutes = re.search(r"(\d+)\s*(minutes?|mins?)\b", corpus)
    duration = int(float(hours.group(1)) * 60) if hours else int(minutes.group(1)) if minutes else 120
    if re.search(r"\b(cancel\s+up\s+to\s+48|48[- ]hour\s+free)\b", corpus):
        cancellation = "FREE_48H"
    elif re.search(r"\b(free\s+cancellation|flexible\s+cancellation|cancel\s+up\s+to\s+24|24[- ]hour\s+free)\b", corpus):
        cancellation = "FREE_24H"
    else:
        cancellation = "NON_REFUNDABLE"
    language = re.search(r"\b(english|arabic|hindi|french|spanish|german|italian|mandarin)\s+(?:speaking\s+)?guide\b", corpus)
    age = re.search(r"\b(children?|kids?)\s*(\d{1,2})\s*(?:-|to|–)\s*(\d{1,2})\b", corpus)
    return {
        "transfer": transfer,
        "meal": meal,
        "access": access,
        "duration_minutes": duration,
        "cancellation": cancellation,
        "guide_language": language.group(1).upper() if language else "UNSPECIFIED",
        "child_age_tier": f"{age.group(2)}-{age.group(3)}" if age else "UNSPECIFIED",
    }


def generate_inclusion_diff(offer_a: dict[str, Any], offer_b: dict[str, Any]) -> dict[str, str]:
    labels = {
        "transfer": "transfers",
        "meal": "meals",
        "access": "access_type",
        "duration_minutes": "duration",
        "cancellation": "cancellation",
        "guide_language": "guide_language",
        "child_age_tier": "child_age_tier",
    }
    differences = {}
    for key, label in labels.items():
        left, right = offer_a.get(key), offer_b.get(key)
        if left != right:
            differences[label] = f"Offer A: {left} vs Offer B: {right}"
    return differences


def compare_inclusions(left: str, right: str) -> dict[str, dict[str, list[str]]]:
    a, b = extract_inclusions(left), extract_inclusions(right)
    return {
        category: {
            "shared": sorted(set(a[category]) & set(b[category])),
            "only_left": sorted(set(a[category]) - set(b[category])),
            "only_right": sorted(set(b[category]) - set(a[category])),
        }
        for category in a
    }
