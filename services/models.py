"""API schemas shared by the search, map and ranking endpoints."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SupplierOffer(BaseModel):
    supplier_name: str
    price: float = Field(gt=0)
    currency: str = "USD"
    available: bool = True
    cancellation_flexible: bool = False
    reliability_score: float = Field(default=0.75, ge=0, le=1)
    meal_plan: str | None = "RO"
    payment_terms: str = "PAY_NOW"
    cancellation_policy: dict[str, Any] = Field(default_factory=dict)
    tax_and_fees: float = Field(default=0, ge=0)


class InventoryItem(BaseModel):
    id: str
    name: str
    entity_type: Literal["HOTEL", "ATTRACTION", "TRANSPORT", "DINING"] | str
    destination: str
    country_code: str = Field(default="IN", min_length=2, max_length=2)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    star_rating: float | None = Field(default=None, ge=0, le=5)
    description: str = ""
    source_category: str | None = None
    amenities: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    offers: list[SupplierOffer] = Field(default_factory=list)
    conversion_prior: float = Field(default=0.5, ge=0, le=1)
    source_id: str | None = None

    @property
    def best_offer(self) -> SupplierOffer | None:
        offers = [offer for offer in self.offers if offer.available]
        return min(offers, key=lambda offer: offer.price) if offers else None
