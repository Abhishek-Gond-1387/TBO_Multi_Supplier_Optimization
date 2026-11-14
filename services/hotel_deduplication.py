"""Hybrid name and distance matcher for identifying hotel listing candidates."""

from __future__ import annotations

import math
import os
import re
import unicodedata
from functools import lru_cache

from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

from services.config import AUTO_MERGE_THRESHOLD, HUMAN_REVIEW_THRESHOLD


def _normalized_name(value: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    name = re.sub(r"[^a-z0-9]+", " ", ascii_name.casefold()).strip()
    return re.sub(r"\b(hotel|resort|the)\b", " ", name).strip()


@lru_cache(maxsize=1)
def _load_embedding_model():
    """Load MiniLM only when explicitly enabled; normal demo startup is offline."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"))


def _semantic_similarity(left: str, right: str) -> float:
    if os.getenv("ENABLE_SEMANTIC_MATCHING", "false").strip().lower() in {"1", "true", "yes"}:
        try:
            model = _load_embedding_model()
            vectors = model.encode([left, right], normalize_embeddings=True)
            return max(0.0, min(1.0, float(vectors[0] @ vectors[1])))
        except (ImportError, OSError, RuntimeError):
            # Missing optional model/dependency must not make ingestion unavailable.
            pass
    # Deterministic lightweight proxy keeps local matching useful without downloads.
    return fuzz.token_set_ratio(left, right) / 100.0


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


def compute_hotel_match_score(
    supplier_name: str,
    supplier_addr: str,
    supplier_lat: float,
    supplier_lon: float,
    canonical_name: str,
    canonical_addr: str,
    canonical_lat: float,
    canonical_lon: float,
) -> tuple[float, dict[str, float | str]]:
    """Return an explainable hybrid match score and feature breakdown."""
    distance = haversine_meters(supplier_lat, supplier_lon, canonical_lat, canonical_lon)
    if distance > 300.0:
        return 0.0, {"geo_dist_m": round(distance, 1), "reason": "Spatial distance exceeded 300m"}

    name_a = _normalized_name(supplier_name)
    name_b = _normalized_name(canonical_name)
    jaro_sim = JaroWinkler.normalized_similarity(name_a, name_b)
    semantic_sim = _semantic_similarity(name_a, name_b)
    if supplier_addr and canonical_addr:
        addr_sim = fuzz.token_set_ratio(_normalized_name(supplier_addr), _normalized_name(canonical_addr)) / 100.0
    else:
        addr_sim = 0.5
    geo_sim = max(0.0, 1.0 - distance / 200.0)
    score = round(0.35 * jaro_sim + 0.35 * semantic_sim + 0.15 * addr_sim + 0.15 * geo_sim, 4)
    return score, {
        "jaro_sim": round(jaro_sim, 4),
        "cosine_sim": round(semantic_sim, 4),
        "addr_sim": round(addr_sim, 4),
        "geo_dist_m": round(distance, 1),
        "geo_sim": round(geo_sim, 4),
        "composite_score": score,
    }


def compare_hotels(left: dict, right: dict) -> dict[str, float | str]:
    score, features = compute_hotel_match_score(
        supplier_name=str(left.get("name", "")),
        supplier_addr=str(left.get("address", left.get("street_address", ""))),
        supplier_lat=float(left["latitude"]),
        supplier_lon=float(left["longitude"]),
        canonical_name=str(right.get("name", "")),
        canonical_addr=str(right.get("address", right.get("street_address", ""))),
        canonical_lat=float(right["latitude"]),
        canonical_lon=float(right["longitude"]),
    )
    if left.get("destination") and right.get("destination") and str(left["destination"]).casefold() != str(right["destination"]).casefold():
        score = 0.0
        features["reason"] = "Destination mismatch"
    if score >= AUTO_MERGE_THRESHOLD:
        decision = "AUTO_MERGE"
    elif score >= HUMAN_REVIEW_THRESHOLD:
        decision = "HUMAN_REVIEW"
    else:
        decision = "REJECT"
    return {
        "name_similarity": float(features.get("jaro_sim", 0)),
        "distance_meters": float(features.get("geo_dist_m", 0)),
        "feature_breakdown": features,
        "score": round(float(score), 4),
        "decision": decision,
    }
