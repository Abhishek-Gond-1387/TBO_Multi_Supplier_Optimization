"""Explainable multi-factor ranking and supplier-rate selection."""

from __future__ import annotations

import os
import statistics
from collections.abc import Mapping, Sequence
from typing import Any

from rapidfuzz import fuzz

from services.models import InventoryItem, SupplierOffer

DEFAULT_WEIGHTS = {
    "relevance": 0.25,
    "price_competitiveness": 0.25,
    "supplier_reliability": 0.20,
    "content_quality": 0.10,
    "cancellation_flexibility": 0.10,
    "conversion_prior": 0.10,
}


def _active_weights(weights: Mapping[str, float] | None = None) -> dict[str, float]:
    source = weights or {
        key: float(os.getenv(f"RANKING_WEIGHT_{key.upper()}", str(value)))
        for key, value in DEFAULT_WEIGHTS.items()
    }
    clean = {key: max(0.0, float(source.get(key, 0.0))) for key in DEFAULT_WEIGHTS}
    total = sum(clean.values())
    if total <= 0:
        return DEFAULT_WEIGHTS.copy()
    return {key: value / total for key, value in clean.items()}


def _clamp(value: Any) -> float:
    try:
        return min(1.0, max(0.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def calculate_price_competitiveness(price: float, median_market_price: float) -> float:
    if price <= 0:
        return 0.0
    if median_market_price <= 0:
        return 1.0
    ratio = price / median_market_price
    if ratio <= 0.8:
        return 1.0
    if ratio >= 1.5:
        return 0.0
    return round(1.0 - ((ratio - 0.8) / 0.7), 4)


def calculate_composite_rank_score(
    item: Mapping[str, Any],
    median_market_price: float,
    weights: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    active = _active_weights(weights)
    price = float(item.get("price", 0) or 0)
    cancellation_type = str(item.get("cancellation_type", "NON_REFUNDABLE")).upper()
    flexible = cancellation_type in {"FREE_24H", "FREE_48H", "FREE_CANCELLATION"} or bool(
        item.get("cancellation_flexible", False)
    )
    raw_conversion = float(item.get("historical_conversion_rate", item.get("conversion_prior", 0.05)))
    raw_quality = float(item.get("content_quality_score", 80.0))
    factors = {
        "relevance": _clamp(item.get("relevance_score", 0.9)),
        "price_competitiveness": calculate_price_competitiveness(price, median_market_price),
        "supplier_reliability": _clamp(item.get("supplier_reliability_score", item.get("reliability_score", 0.95))),
        "content_quality": _clamp(raw_quality / 100.0 if raw_quality > 1 else raw_quality),
        "cancellation_flexibility": 1.0 if flexible else 0.3,
        "conversion_prior": _clamp(raw_conversion * 10.0 if raw_conversion <= 0.1 else raw_conversion),
    }
    score = round(sum(active[key] * factors[key] for key in active), 4)
    badges = []
    if factors["price_competitiveness"] >= 0.9:
        badges.append("CHEAPEST")
    if factors["supplier_reliability"] >= 0.98 and factors["content_quality"] >= 0.85:
        badges.append("MOST_RELIABLE")
    if score >= 0.85:
        badges.append("RECOMMENDED")
    if flexible and factors["price_competitiveness"] >= 0.75:
        badges.append("BEST_VALUE")
    return {
        "canonical_id": item.get("id", item.get("canonical_id")),
        "rank_score": score,
        "badges": badges,
        "factors": factors,
        "weights": active,
    }


def select_supplier_offer(
    offers: Sequence[SupplierOffer], median_market_price: float
) -> tuple[SupplierOffer | None, list[dict[str, Any]]]:
    ranked_offers = []
    for offer in offers:
        if not offer.available:
            continue
        result = calculate_composite_rank_score(
            {
                "id": offer.supplier_name,
                "price": offer.price,
                "supplier_reliability_score": offer.reliability_score,
                "cancellation_flexible": offer.cancellation_flexible,
                "content_quality_score": 80,
                "relevance_score": 1.0,
            },
            median_market_price,
        )
        ranked_offers.append({"offer": offer.model_dump(), **result})
    ranked_offers.sort(key=lambda item: item["rank_score"], reverse=True)
    selected = SupplierOffer.model_validate(ranked_offers[0]["offer"]) if ranked_offers else None
    return selected, ranked_offers


def rank_items(items: Sequence[InventoryItem], query: str = "") -> list[dict[str, object]]:
    prices = [offer.price for item in items for offer in item.offers if offer.available]
    median_price = statistics.median(prices) if prices else 0.0
    query_terms = [term for term in query.casefold().split() if len(term) > 1]
    ranked: list[dict[str, object]] = []
    for item in items:
        searchable = f"{item.name} {item.destination} {' '.join(item.amenities)} {item.description}".casefold()
        relevance = sum(term in searchable for term in query_terms) / len(query_terms) if query_terms else 0.9
        selected, offer_scores = select_supplier_offer(item.offers, median_price)
        if offer_scores:
            top_factors = dict(offer_scores[0]["factors"])
        else:
            top_factors = {
                "relevance": relevance,
                "price_competitiveness": 0.0,
                "supplier_reliability": 0.0,
                "content_quality": min(1.0, 0.35 + (0.25 if item.description else 0) + min(len(item.amenities), 8) * 0.05),
                "cancellation_flexibility": 0.0,
                "conversion_prior": item.conversion_prior,
            }
        top_factors["relevance"] = relevance
        top_factors["conversion_prior"] = item.conversion_prior
        active_weights = _active_weights()
        score = round(sum(active_weights[key] * top_factors[key] for key in active_weights), 4)
        cheapest_price = min((offer.price for offer in item.offers if offer.available), default=None)
        badges = []
        if selected and cheapest_price is not None and selected.price == cheapest_price:
            badges.append("CHEAPEST")
        if selected and selected.reliability_score >= 0.95:
            badges.append("MOST_RELIABLE")
        if selected and selected.cancellation_flexible and top_factors["price_competitiveness"] >= 0.75:
            badges.append("BEST_VALUE")
        if score >= 0.8:
            badges.append("RECOMMENDED")
        ranked.append(
            {
                "item": item.model_dump(),
                "rank_score": score,
                "rank_factors": top_factors,
                "factor_weights": active_weights,
                "badges": badges,
                "selected_supplier": selected.model_dump() if selected else None,
                "supplier_offers_ranked": offer_scores,
            }
        )
    return sorted(ranked, key=lambda result: result["rank_score"], reverse=True)
