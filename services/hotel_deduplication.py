"""Analysis-only hybrid matcher for hotel listing candidates."""

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
    token_sim = _semantic_similarity(name_a, name_b)
    has_address = bool(supplier_addr.strip() and canonical_addr.strip())
    addr_sim = (
        fuzz.token_set_ratio(_normalized_name(supplier_addr), _normalized_name(canonical_addr)) / 100.0
        if has_address else 0.0
    )
    geo_sim = max(0.0, 1.0 - distance / 300.0)
    weights = {"jaro_sim": 0.45, "token_set_similarity": 0.25, "address_similarity": 0.15 if has_address else 0.0, "geo_sim": 0.15}
    values = {"jaro_sim": jaro_sim, "token_set_similarity": token_sim, "address_similarity": addr_sim, "geo_sim": geo_sim}
    active_total = sum(weights.values())
    score = round(sum(weights[key] * values[key] for key in weights) / active_total, 4)
    return score, {
        "jaro_sim": round(jaro_sim, 4),
        "token_set_similarity": round(token_sim, 4),
        "address_similarity": round(addr_sim, 4),
        "address_available": has_address,
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
        decision = "AUTO_MERGE_CANDIDATE"
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


def run_batch_inventory_deduplication(
    inventory_items: list[dict[str, Any]],
    auto_merge_threshold: float = AUTO_MERGE_THRESHOLD,
    human_review_threshold: float = HUMAN_REVIEW_THRESHOLD,
) -> dict[str, Any]:
    """Execute high-performance spatial-grid batch deduplication across multi-supplier hotel listings.

    Clusters properties by spatial grid cells (~1km blocks) to achieve linear O(N) candidate
    generation, computes composite Jaro-Winkler + Haversine metrics, and groups duplicates into
    canonical entities while routing borderlines to the Human Review Queue.
    """
    import collections
    from uuid import uuid4

    hotels = [item for item in inventory_items if str(item.get("entity_type", "HOTEL")).upper() == "HOTEL"]
    total_raw_hotels = len(hotels)

    # 1. Spatial Grid Indexing (0.01 deg lat/lon is ~1.1 km)
    grid: dict[tuple[int, int], list[dict[str, Any]]] = collections.defaultdict(list)
    for h in hotels:
        try:
            lat = float(h.get("latitude", 0))
            lon = float(h.get("longitude", 0))
            if lat == 0 and lon == 0:
                continue
            cell = (int(round(lat * 100)), int(round(lon * 100)))
            grid[cell].append(h)
        except (ValueError, TypeError):
            continue

    auto_merge_candidates: list[dict[str, Any]] = []
    review_queue_items: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()

    # Union-Find estimates cluster impact; it does not mutate or merge inventory.
    parent: dict[str, str] = {str(h.get("id")): str(h.get("id")) for h in hotels if h.get("id")}

    def find(x: str) -> str:
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x: str, y: str):
        root_x, root_y = find(x), find(y)
        if root_x != root_y:
            parent[root_y] = root_x

    # 2. Localized Neighbor Pairwise Matching
    for (cx, cy), cell_hotels in grid.items():
        # Check current cell and adjacent 8 neighboring cells
        neighbor_candidates = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                neighbor_candidates.extend(grid.get((cx + dx, cy + dy), []))

        for i, left in enumerate(cell_hotels):
            for right in neighbor_candidates:
                id_left = str(left.get("id"))
                id_right = str(right.get("id"))
                if id_left >= id_right:
                    continue
                pair_key = (id_left, id_right)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                comparison = compare_hotels(left, right)
                score = comparison["score"]
                decision = comparison["decision"]

                if decision == "AUTO_MERGE_CANDIDATE" and id_left in parent and id_right in parent:
                    union(id_left, id_right)
                    auto_merge_candidates.append({
                        "left_id": id_left,
                        "right_id": id_right,
                        "left_name": left.get("name"),
                        "right_name": right.get("name"),
                        "score": score,
                        "distance_m": comparison["distance_meters"],
                        "feature_breakdown": comparison["feature_breakdown"],
                    })
                elif decision == "HUMAN_REVIEW":
                    review_queue_items.append({
                        "id": f"rev-{id_left}-{id_right}",
                        "status": "PENDING",
                        "score": score,
                        "decision_hint": "HUMAN_REVIEW_RECOMMENDED",
                        "feature_breakdown": comparison["feature_breakdown"],
                        "left": left,
                        "right": right,
                        "explanation": f"Fuzzy lexical match ({round(comparison['name_similarity']*100)}%) and close proximity ({comparison['distance_meters']}m). Review required before merging.",
                    })

    # 3. Form Unique Canonical Clusters
    clusters: dict[str, list[str]] = collections.defaultdict(list)
    for h in hotels:
        item_id = str(h.get("id") or "")
        if item_id in parent:
            clusters[find(item_id)].append(item_id)

    estimated_unique_clusters = len(clusters)
    estimated_reduction = round(
        (total_raw_hotels - estimated_unique_clusters) / max(1, total_raw_hotels) * 100, 1
    )

    return {
        "status": "ANALYZED",
        "mode": "ANALYSIS_ONLY",
        "automatic_merges_applied": 0,
        "total_listings_scanned": total_raw_hotels,
        "spatial_grid_cells_evaluated": len(grid),
        "pairwise_comparisons_performed": len(seen_pairs),
        "proposed_auto_merge_candidates_count": len(auto_merge_candidates),
        "human_review_candidates_count": len(review_queue_items),
        "estimated_unique_clusters_if_auto_candidates_accepted": estimated_unique_clusters,
        "estimated_reduction_pct_if_auto_candidates_accepted": estimated_reduction,
        "sample_auto_merge_candidates": auto_merge_candidates[:10],
        "generated_review_items": review_queue_items[:200],
    }
