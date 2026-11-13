"""Small, configurable multi-factor ranking function for inventory results."""

from __future__ import annotations

import os
from collections.abc import Sequence

from services.models import InventoryItem

WEIGHTS = {
    "relevance": float(os.getenv("RANKING_WEIGHT_RELEVANCE", "0.25")),
    "price_competitiveness": float(
        os.getenv("RANKING_WEIGHT_PRICE_COMPETITIVENESS", "0.25")
    ),
    "supplier_reliability": float(
        os.getenv("RANKING_WEIGHT_SUPPLIER_RELIABILITY", "0.20")
    ),
    "content_quality": float(os.getenv("RANKING_WEIGHT_CONTENT_QUALITY", "0.10")),
    "cancellation_flexibility": float(
        os.getenv("RANKING_WEIGHT_CANCELLATION_FLEXIBILITY", "0.10")
    ),
    "conversion_prior": float(os.getenv("RANKING_WEIGHT_CONVERSION_PRIOR", "0.10")),
}
_WEIGHT_TOTAL = sum(max(0.0, value) for value in WEIGHTS.values()) or 1.0


def rank_items(
    items: Sequence[InventoryItem], query: str = ""
) -> list[dict[str, object]]:
    available_prices = [
        item.best_offer.price for item in items if item.best_offer is not None
    ]
    lowest_price = min(available_prices, default=1.0)
    normalized_query = query.casefold().strip()
    ranked: list[dict[str, object]] = []

    for item in items:
        offer = item.best_offer
        relevance = 1.0 if normalized_query and normalized_query in item.name.casefold() else 0.6
        if not normalized_query:
            relevance = 0.6
        price_score = min(1.0, lowest_price / offer.price) if offer else 0.0
        reliability = offer.reliability_score if offer else 0.0
        content_quality = min(
            1.0,
            0.35 + (0.25 if item.description else 0.0) + min(len(item.amenities), 8) * 0.05,
        )
        cancellation = 1.0 if offer and offer.cancellation_flexible else 0.0
        factors = {
            "relevance": relevance,
            "price_competitiveness": price_score,
            "supplier_reliability": reliability,
            "content_quality": content_quality,
            "cancellation_flexibility": cancellation,
            "conversion_prior": item.conversion_prior,
        }
        score = sum(
            max(0.0, WEIGHTS[key]) * value for key, value in factors.items()
        ) / _WEIGHT_TOTAL
        badges = []
        if offer and offer.price == lowest_price:
            badges.append("BEST PRICE")
        if offer and offer.cancellation_flexible:
            badges.append("FLEXIBLE CANCELLATION")
        ranked.append(
            {
                "item": item.model_dump(),
                "rank_score": round(score, 4),
                "rank_factors": {key: round(value, 4) for key, value in factors.items()},
                "badges": badges,
            }
        )
    return sorted(ranked, key=lambda result: result["rank_score"], reverse=True)
