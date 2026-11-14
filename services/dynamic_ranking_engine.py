"""Explainable multi-factor dynamic ranking and supplier-rate selection engine.

Supports configurable B2B ranking modes:
- RECOMMENDED (Balanced Conversion: Price 25%, Reliability 25%, Quality 15%, Cancellation 15%, Relevance 20%)
- CHEAPEST (Price Competitiveness 50%, Reliability 20%, Relevance 20%, Quality 10%)
- MOST_RELIABLE (Supplier Reliability 45%, Instant Confirmation 20%, Price 15%, Quality 20%)
- BEST_VALUE (Price Competitiveness + Inclusions / Amenities Value maximized)
- HIGH_CONVERSION (Historical Booking Conversion + Instant Booking)
"""

from __future__ import annotations

import os
import statistics
from collections.abc import Mapping, Sequence
from typing import Any

from rapidfuzz import fuzz

from services.models import InventoryItem, SupplierOffer

STRATEGY_WEIGHTS = {
    "RECOMMENDED": {
        "relevance": 0.20,
        "price_competitiveness": 0.25,
        "supplier_reliability": 0.25,
        "content_quality": 0.10,
        "cancellation_flexibility": 0.10,
        "conversion_prior": 0.10,
    },
    "CHEAPEST": {
        "relevance": 0.15,
        "price_competitiveness": 0.50,
        "supplier_reliability": 0.15,
        "content_quality": 0.05,
        "cancellation_flexibility": 0.10,
        "conversion_prior": 0.05,
    },
    "MOST_RELIABLE": {
        "relevance": 0.15,
        "price_competitiveness": 0.15,
        "supplier_reliability": 0.45,
        "content_quality": 0.10,
        "cancellation_flexibility": 0.10,
        "conversion_prior": 0.05,
    },
    "BEST_VALUE": {
        "relevance": 0.15,
        "price_competitiveness": 0.35,
        "supplier_reliability": 0.20,
        "content_quality": 0.15,
        "cancellation_flexibility": 0.15,
        "conversion_prior": 0.00,
    },
}

DEFAULT_WEIGHTS = STRATEGY_WEIGHTS["RECOMMENDED"]


def _active_weights(
    strategy: str = "RECOMMENDED",
    weights: Mapping[str, float] | None = None,
) -> dict[str, float]:
    base = STRATEGY_WEIGHTS.get(strategy.upper(), DEFAULT_WEIGHTS)
    source = weights or {
        key: float(os.getenv(f"RANKING_WEIGHT_{key.upper()}", str(value)))
        for key, value in base.items()
    }
    clean = {key: max(0.0, float(source.get(key, 0.0))) for key in base}
    total = sum(clean.values())
    if total <= 0:
        return base.copy()
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
    strategy: str = "RECOMMENDED",
    weights: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    active = _active_weights(strategy, weights)
    price = float(item.get("price", 0) or 0)
    cancellation_type = str(item.get("cancellation_type", "NON_REFUNDABLE")).upper()
    flexible = cancellation_type in {"FREE_24H", "FREE_48H", "FREE_CANCELLATION"} or bool(
        item.get("cancellation_flexible", False)
    )
    raw_conversion = float(item.get("historical_conversion_rate", item.get("conversion_prior", 0.0)))
    raw_quality = float(item.get("content_quality_score", 0.0))
    factors = {
        "relevance": _clamp(item.get("relevance_score", 0.0)),
        "price_competitiveness": calculate_price_competitiveness(price, median_market_price),
        "supplier_reliability": _clamp(item.get("supplier_reliability_score", item.get("reliability_score", 0.0))),
        "content_quality": _clamp(raw_quality / 100.0 if raw_quality > 1 else raw_quality),
        "cancellation_flexibility": 1.0 if flexible else 0.0,
        "conversion_prior": _clamp(raw_conversion * 10.0 if raw_conversion <= 0.1 else raw_conversion),
    }
    available_signals = {
        "relevance": item.get("relevance_score") is not None,
        "price_competitiveness": price > 0 and median_market_price > 0,
        "supplier_reliability": item.get("supplier_reliability_score", item.get("reliability_score")) is not None,
        "content_quality": item.get("content_quality_score") is not None,
        "cancellation_flexibility": item.get("cancellation_flexible") is not None or item.get("cancellation_type") is not None,
        "conversion_prior": item.get("historical_conversion_rate", item.get("conversion_prior")) is not None,
    }
    usable_weights = {key: value for key, value in active.items() if available_signals.get(key)}
    weight_total = sum(usable_weights.values())
    effective = ({key: value / weight_total for key, value in usable_weights.items()}
                 if weight_total else {})
    score = round(sum(effective[key] * factors[key] for key in effective), 4) if effective else 0.0
    badges = []
    if factors["price_competitiveness"] >= 0.9 and available_signals["price_competitiveness"]:
        badges.append("PRICE_COMPETITIVE")
    if factors["supplier_reliability"] >= 0.96 and available_signals["supplier_reliability"]:
        badges.append("RELIABILITY_SIGNAL")
    if item.get("available") and item.get("payment_terms") in {"PAY_AT_HOTEL", "NET_30"}:
        badges.append("FLEXIBLE_PAYMENT")

    return {
        "canonical_id": item.get("id", item.get("canonical_id")),
        "rank_score": score,
        "badges": badges,
        "factors": factors,
        "weights": effective,
    }


def select_supplier_offer(
    offers: Sequence[SupplierOffer],
    median_market_price: float,
    strategy: str = "RECOMMENDED",
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
                "payment_terms": getattr(offer, "payment_terms", "PAY_NOW"),
                "content_quality_score": None,
                "relevance_score": 1.0,
                "conversion_prior": 0.0,
            },
            median_market_price,
            strategy=strategy,
        )
        ranked_offers.append({"offer": offer.model_dump(), **result})
    ranked_offers.sort(key=lambda item: item["rank_score"], reverse=True)
    selected = SupplierOffer.model_validate(ranked_offers[0]["offer"]) if ranked_offers else None
    return selected, ranked_offers


def generate_rank_explanation(item_name: str, selected_supplier: SupplierOffer | None, factors: dict[str, float], badges: list[str]) -> str:
    """Generate human-readable justification for why this listing is positioned at its rank."""
    if not selected_supplier:
        return "Ranked by baseline relevance and property quality score."
    supp = selected_supplier.supplier_name
    price = selected_supplier.price
    parts = []
    if factors.get("price_competitiveness", 0) >= 0.8:
        parts.append(f"Lower-priced among this listing's supplied offers ({supp}: {selected_supplier.currency} {price:,.0f})")
    else:
        parts.append(f"Offered via {supp} at {selected_supplier.currency} {price:,.0f}")

    if selected_supplier.cancellation_flexible:
        parts.append("with flexible cancellation according to the supplied offer")

    return " • ".join(parts)


def _content_completeness(item: InventoryItem) -> float:
    """Fraction of useful catalog fields present; this is not a quality truth score."""
    fields = (
        bool(item.name.strip()),
        bool(item.destination.strip()),
        bool(item.description.strip()),
        bool(item.source_category),
        bool(item.amenities),
        bool(item.images),
        item.property_classification is not None or item.star_rating is not None,
        bool(item.source_id),
    )
    return sum(fields) / len(fields)


def rank_items(
    items: Sequence[InventoryItem],
    query: str = "",
    strategy: str = "RECOMMENDED",
) -> list[dict[str, object]]:
    """Rank listings only on observed text relevance and source-field completeness.

    Supplier price, reliability, cancellation and conversion signals are not used to
    rank properties when the local OSM pilot has no supplier offer feed.
    """
    query_terms = [term for term in query.casefold().split() if len(term) > 1]
    ranked: list[dict[str, object]] = []
    for item in items:
        searchable = (
            f"{item.name} {item.destination} {' '.join(item.amenities)} "
            f"{item.description} {item.source_category or ''}"
        ).casefold()
        relevance = (sum(term in searchable for term in query_terms) / len(query_terms)) if query_terms else 0.5
        completeness = _content_completeness(item)
        # No conversion prior, customer rating, or supplier reliability is inferred.
        factors = {"text_relevance": relevance, "source_completeness": completeness}
        score = round(0.75 * relevance + 0.25 * completeness, 4)
        offers = [offer for offer in item.offers if offer.available]
        selected: SupplierOffer | None = None
        offer_scores: list[dict[str, Any]] = []
        if offers:
            selected, offer_scores = select_supplier_offer(offers, statistics.median(o.price for o in offers), strategy)
        badges = ["TEXT_MATCH"] if query_terms and relevance >= 0.8 else []
        explanation = (
            "Ordered by text match and fields present in the source record; no booking, review, or supplier reliability feed is connected."
            if not offers else
            "Property order uses text match and source-field completeness. Supplier options are ranked within this listing only."
        )
        ranked.append({
            "item": item.model_dump(),
            "rank_score": score,
            "rank_factors": factors,
            "factor_weights": {"text_relevance": 0.75, "source_completeness": 0.25},
            "ranking_method": "TEXT_RELEVANCE_AND_SOURCE_COMPLETENESS",
            "badges": badges,
            "rank_explanation": explanation,
            "selected_supplier": selected.model_dump() if selected else None,
            "supplier_offers_ranked": offer_scores,
        })
    return sorted(
        ranked,
        key=lambda result: (result["rank_score"], str(result["item"].get("name", "")).casefold()),
        reverse=True,
    )
