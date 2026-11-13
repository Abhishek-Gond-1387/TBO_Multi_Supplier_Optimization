"""FastAPI application for the TBO multi-supplier discovery MVP."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.config import API_V1_PREFIX, APP_ENV, APP_NAME, CORS_ORIGINS, DEBUG
from services.dynamic_ranking_engine import rank_items
from services.hotel_deduplication import compare_hotels
from services.models import InventoryItem
from services.room_normalizer import normalize_room
from services.sightseeing_difference_engine import compare_inclusions
from services.voice_intent_parser import parse_voice_query

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = PROJECT_ROOT / "data" / "sample_inventory.json"

app = FastAPI(title=APP_NAME, version="0.1.0", debug=DEBUG)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type"],
)


def load_inventory() -> list[InventoryItem]:
    with INVENTORY_PATH.open(encoding="utf-8") as inventory_file:
        rows = json.load(inventory_file)
    return [InventoryItem.model_validate(row) for row in rows]


class VoiceRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=1000)


class MatchRequest(BaseModel):
    left: dict
    right: dict


class RoomRequest(BaseModel):
    raw_name: str = Field(min_length=1, max_length=300)


class SightseeingRequest(BaseModel):
    left_description: str = Field(max_length=5000)
    right_description: str = Field(max_length=5000)


class ReviewDecision(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    reviewer: str = Field(default="local-demo", max_length=120)


review_queue: list[dict] = []


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": APP_ENV}


@app.get(f"{API_V1_PREFIX}/health")
def api_health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME, "environment": APP_ENV}


@app.get(f"{API_V1_PREFIX}/inventory")
def inventory_viewport(
    west: float | None = Query(default=None, ge=-180, le=180),
    south: float | None = Query(default=None, ge=-90, le=90),
    east: float | None = Query(default=None, ge=-180, le=180),
    north: float | None = Query(default=None, ge=-90, le=90),
    entity_type: Literal["HOTEL", "ATTRACTION"] | None = None,
    destination: str | None = None,
) -> dict[str, object]:
    items = load_inventory()
    if entity_type:
        items = [item for item in items if item.entity_type == entity_type]
    if destination:
        items = [item for item in items if destination.casefold() in item.destination.casefold()]
    bounds = (west, south, east, north)
    if any(value is not None for value in bounds):
        if any(value is None for value in bounds):
            raise HTTPException(400, "Provide all four viewport bounds: west, south, east, north.")
        assert west is not None and south is not None and east is not None and north is not None
        if south > north:
            raise HTTPException(400, "The south bound must be less than or equal to north.")
        if west <= east:
            items = [item for item in items if south <= item.latitude <= north and west <= item.longitude <= east]
        else:
            items = [item for item in items if south <= item.latitude <= north and (item.longitude >= west or item.longitude <= east)]
    return {"count": len(items), "items": [item.model_dump() for item in items]}


@app.get(f"{API_V1_PREFIX}/inventory/search")
def search_inventory(
    q: str = "",
    destination: str | None = None,
    entity_type: Literal["HOTEL", "ATTRACTION"] | None = None,
    max_price: float | None = Query(default=None, gt=0),
    min_stars: float | None = Query(default=None, ge=0, le=5),
) -> dict[str, object]:
    items = load_inventory()
    if destination:
        items = [item for item in items if destination.casefold() in item.destination.casefold()]
    if entity_type:
        items = [item for item in items if item.entity_type == entity_type]
    if max_price is not None:
        items = [item for item in items if item.best_offer is not None and item.best_offer.price <= max_price]
    if min_stars is not None:
        items = [item for item in items if item.star_rating is not None and item.star_rating >= min_stars]
    if q.strip():
        terms = q.casefold().split()
        items = [item for item in items if all(term in f"{item.name} {item.destination} {' '.join(item.amenities)}".casefold() for term in terms)]
    ranked = rank_items(items, q)
    return {"count": len(ranked), "results": ranked}


@app.post(f"{API_V1_PREFIX}/voice/query")
def voice_query(request: VoiceRequest) -> dict[str, object]:
    intent = parse_voice_query(request.transcript)
    items = load_inventory()
    destination = intent.get("destination")
    if destination:
        items = [item for item in items if str(destination).casefold() in item.destination.casefold()]
    if intent["entity_type"] == "HOTEL":
        items = [item for item in items if item.entity_type == "HOTEL"]
    stars = intent.get("star_rating")
    if isinstance(stars, (float, int)):
        items = [item for item in items if item.star_rating is not None and item.star_rating >= stars]
    price = intent.get("max_price")
    if isinstance(price, (float, int)):
        items = [item for item in items if item.best_offer and item.best_offer.price <= price]
    inclusions = set(intent.get("inclusions", []))
    if "FLEXIBLE_CANCELLATION" in inclusions:
        items = [item for item in items if item.best_offer and item.best_offer.cancellation_flexible]
    if "BREAKFAST" in inclusions:
        items = [item for item in items if any("breakfast" in amenity.casefold() for amenity in item.amenities)]
    results = rank_items(items, str(destination or ""))
    return {"intent": intent, "count": len(results), "results": results}


@app.post(f"{API_V1_PREFIX}/matches/compare")
def match_compare(request: MatchRequest) -> dict[str, object]:
    result = compare_hotels(request.left, request.right)
    if result["decision"] == "HUMAN_REVIEW":
        result["review_id"] = str(uuid4())
        review_queue.append({"id": result["review_id"], "status": "PENDING", "score": result["score"], "left": request.left, "right": request.right})
    return result


@app.get(f"{API_V1_PREFIX}/review-queue")
def list_review_queue(status: Literal["PENDING", "APPROVED", "REJECTED"] | None = "PENDING") -> dict[str, object]:
    rows = [row for row in review_queue if status is None or row["status"] == status]
    return {"count": len(rows), "items": rows}


@app.put(f"{API_V1_PREFIX}/review-queue/{{review_id}}")
def decide_review(review_id: str, decision: ReviewDecision) -> dict[str, object]:
    row = next((item for item in review_queue if item["id"] == review_id), None)
    if row is None:
        raise HTTPException(404, "Review item not found.")
    if row["status"] != "PENDING":
        raise HTTPException(409, "This review item has already been decided.")
    row.update(status=decision.status, reviewer=decision.reviewer)
    return row


@app.post(f"{API_V1_PREFIX}/rooms/normalize")
def room_normalize(request: RoomRequest) -> dict[str, str]:
    return {"raw_name": request.raw_name, "normalized_name": normalize_room(request.raw_name)}


@app.post(f"{API_V1_PREFIX}/sightseeing/compare")
def sightseeing_compare(request: SightseeingRequest) -> dict[str, object]:
    return compare_inclusions(request.left_description, request.right_description)
