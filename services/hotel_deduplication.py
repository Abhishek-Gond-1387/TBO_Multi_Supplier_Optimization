"""Hybrid name and distance matcher for identifying hotel listing candidates."""

from __future__ import annotations

import math
import re
import unicodedata
from difflib import SequenceMatcher

from rapidfuzz import fuzz

from services.config import AUTO_MERGE_THRESHOLD, HUMAN_REVIEW_THRESHOLD, MAX_GEO_DISTANCE_METERS


def _normalized_name(value: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", ascii_name.casefold()).strip()


def haversine_meters(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    radius = 6_371_000
    phi_a, phi_b = math.radians(lat_a), math.radians(lat_b)
    delta_phi = math.radians(lat_b - lat_a)
    delta_lambda = math.radians(lon_b - lon_a)
    value = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi_a) * math.cos(phi_b) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(min(1.0, value)))


def compare_hotels(left: dict, right: dict) -> dict[str, float | str]:
    name_a, name_b = _normalized_name(str(left.get("name", ""))), _normalized_name(
        str(right.get("name", ""))
    )
    token_score = fuzz.token_sort_ratio(name_a, name_b) / 100.0
    sequence_score = SequenceMatcher(None, name_a, name_b).ratio()
    name_score = 0.7 * token_score + 0.3 * sequence_score
    distance = haversine_meters(
        float(left["latitude"]), float(left["longitude"]),
        float(right["latitude"]), float(right["longitude"]),
    )
    same_destination = str(left.get("destination", "")).casefold() == str(
        right.get("destination", "")
    ).casefold()
    if distance > MAX_GEO_DISTANCE_METERS or not same_destination:
        score = name_score * 0.55
    else:
        geo_score = 1.0 - distance / MAX_GEO_DISTANCE_METERS
        score = 0.78 * name_score + 0.22 * geo_score
    if score >= AUTO_MERGE_THRESHOLD:
        decision = "AUTO_MERGE"
    elif score >= HUMAN_REVIEW_THRESHOLD:
        decision = "HUMAN_REVIEW"
    else:
        decision = "REJECT"
    return {
        "name_similarity": round(name_score, 4),
        "distance_meters": round(distance, 2),
        "score": round(score, 4),
        "decision": decision,
    }
