"""Strict validation and completeness scoring for supplier hotel feeds."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class RawSupplierHotelPayload(BaseModel):
    supplier_code: str = Field(min_length=2, max_length=32)
    supplier_hotel_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=2, max_length=255)
    street_address: str | None = None
    city: str = Field(min_length=2, max_length=100)
    country_code: str = Field(min_length=2, max_length=2)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    star_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    images: list[str] = Field(default_factory=list, max_length=100)
    amenities: list[str] = Field(default_factory=list, max_length=200)

    @field_validator("name", "city", mode="before")
    @classmethod
    def clean_text(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()

    @field_validator("country_code")
    @classmethod
    def standardize_country(cls, value: str) -> str:
        return value.upper()

    @field_validator("amenities")
    @classmethod
    def normalize_amenities(cls, values: list[str]) -> list[str]:
        return sorted({re.sub(r"\s+", " ", value).strip().casefold() for value in values if value.strip()})

    @model_validator(mode="after")
    def validate_coordinate_sanity(self) -> "RawSupplierHotelPayload":
        if abs(self.latitude) < 0.001 and abs(self.longitude) < 0.001:
            raise ValueError("Coordinates at Null Island (0,0) are invalid")
        return self


class RawSupplierSightseeingPayload(BaseModel):
    supplier_code: str = Field(min_length=2, max_length=32)
    supplier_product_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=10000)
    city: str = Field(min_length=2, max_length=100)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    inclusions: list[str] = Field(default_factory=list, max_length=100)
    price: float | None = Field(default=None, gt=0)


def calculate_data_quality_score(hotel: RawSupplierHotelPayload) -> float:
    score = 25.0  # Pydantic already validated coordinate bounds and Null Island.
    if hotel.street_address and len(hotel.street_address.strip()) > 5:
        score += 20.0
    if hotel.star_rating and hotel.star_rating > 0:
        score += 15.0
    if len(hotel.images) >= 10:
        score += 20.0
    elif len(hotel.images) >= 5:
        score += 12.0
    elif hotel.images:
        score += 5.0
    if len(hotel.amenities) >= 8:
        score += 20.0
    elif len(hotel.amenities) >= 4:
        score += 12.0
    elif hotel.amenities:
        score += 5.0
    return round(score, 2)
