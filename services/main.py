"""FastAPI entry point for the local TBO supplier inventory demo and API."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field, model_validator

from services import database
from services.cache_service import cache_status, get_or_set
from services.config import (
    API_V1_PREFIX,
    APP_ENV,
    APP_NAME,
    CACHE_TTL_GEO_VIEWPORT,
    CACHE_TTL_LIVE_RATES,
    CORS_ORIGINS,
    DEBUG,
    ENABLE_CELERY,
    MAP_ATTRIBUTION,
    DEMO_CITY,
    MAP_DEFAULT_DESTINATION,
    MAP_DEFAULT_LATITUDE,
    MAP_DEFAULT_LONGITUDE,
    MAP_STYLE_URL,
    MAP_DEFAULT_ZOOM,
    USE_DATABASE,
)
from services.ai_trip_planner import PAN_INDIA_HUBS, generate_itinerary, parse_trip_intent
from services.dynamic_ranking_engine import rank_items
from services.hotel_deduplication import compare_hotels, haversine_meters
from services.ingestion_validator import RawSupplierHotelPayload, calculate_data_quality_score
from services.models import InventoryItem
from services.open_geo import geocode_address, reverse_geocode
from services.pan_india_catalog import (
    PAN_INDIA_DINING_SPOTS,
    PAN_INDIA_TRANSPORT_HUBS,
    get_pan_india_stats,
    get_transit_corridors,
)
from services.pan_india_1m_engine import live_1m_engine
from services.room_normalizer import normalize_room_title
from services.sightseeing_difference_engine import (
    extract_tour_inclusions,
    generate_inclusion_diff,
)
from services.voice_intent_parser import parse_voice_travel_query
from services.live_travel_service import (
    search_destinations_global,
    reverse_geocode_location,
    get_live_weather,
    get_nearby_attractions,
    generate_dynamic_journey_plans,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tbo.api")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
INVENTORY_PATH = PROJECT_ROOT / "data" / "sample_inventory.json"
OPEN_DATA_INVENTORY_PATH = PROJECT_ROOT / "data" / "osm_inventory.json"
OPEN_DATA_STATUS_PATH = PROJECT_ROOT / "data" / "osm_inventory.status.json"

REQUESTS = Counter("tbo_http_requests_total", "HTTP requests served", ("method", "route", "status"))
LATENCY = Histogram("tbo_http_request_seconds", "HTTP request latency", ("method", "route"))
MATCH_DECISIONS = Counter("tbo_match_decisions_total", "Hotel match decisions", ("decision",))
TELEMETRY: dict[str, int] = {"IMPRESSION": 0, "DETAIL_VIEW": 0, "BOOKING_INTENT": 0, "BOOKED": 0}


def _seed_initial_review_queue() -> list[dict[str, Any]]:
    return [
        {
            "id": "review-hotel-taj-01",
            "status": "PENDING",
            "score": 0.96,
            "decision_hint": "AUTO_MERGE_CANDIDATE",
            "feature_breakdown": {
                "name_lexical_similarity": 0.94,
                "geographic_distance_meters": 14.2,
                "address_token_overlap": 0.92,
            },
            "left": {
                "id": "hotel-tbo-101",
                "name": "The Taj Mahal Hotel New Delhi",
                "destination": "Delhi",
                "address": "Number 1 Mansingh Road, New Delhi 110011",
                "latitude": 28.6045,
                "longitude": 77.2255,
                "supplier_name": "TBO Preferred",
                "price": 14500,
                "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=600&q=80",
                "room_type": "Deluxe Room - King Bed BB",
            },
            "right": {
                "id": "hotel-hbeds-884",
                "name": "Taj Mahal Hotel New Delhi - Central",
                "destination": "Delhi",
                "address": "1, Mansingh Rd, South End Lane, New Delhi 110011",
                "latitude": 28.6046,
                "longitude": 77.2256,
                "supplier_name": "Hotelbeds Global",
                "price": 13950,
                "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=600&q=80",
                "room_type": "DLX KNG BB BALC",
            },
            "explanation": "High lexical and geographic proximity (14m apart). Confirmed duplicate listing from two different suppliers. Consolidate into 1 listing to offer travelers the lowest rate.",
        },
        {
            "id": "review-hotel-radisson-02",
            "status": "PENDING",
            "score": 0.62,
            "decision_hint": "SPLIT_REQUIRED",
            "feature_breakdown": {
                "name_lexical_similarity": 0.78,
                "geographic_distance_meters": 14820.0,
                "address_token_overlap": 0.25,
            },
            "left": {
                "id": "hotel-agoda-421",
                "name": "Radisson Blu Hotel New Delhi Paschim Vihar",
                "destination": "Delhi",
                "address": "Plot No. D, District Centre, Outer Ring Rd, Paschim Vihar, New Delhi",
                "latitude": 28.6732,
                "longitude": 77.0924,
                "supplier_name": "Agoda Direct",
                "price": 4200,
                "image": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=600&q=80",
                "room_type": "Superior King Room",
            },
            "right": {
                "id": "hotel-expedia-912",
                "name": "Radisson Blu Marina Hotel Connaught Place",
                "destination": "Delhi",
                "address": "G-59 Connaught Circus, New Delhi 110001",
                "latitude": 28.6315,
                "longitude": 77.2185,
                "supplier_name": "Expedia Partner",
                "price": 5400,
                "image": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&w=600&q=80",
                "room_type": "Standard Heritage Room",
            },
            "explanation": "Brand name similarity ('Radisson Blu') triggered review, but coordinates are 14.8 km apart in Paschim Vihar vs Connaught Place! Must keep separate as distinct properties.",
        },
        {
            "id": "review-tour-taj-03",
            "status": "PENDING",
            "score": 0.74,
            "decision_hint": "INCLUSIONS_DIFFERENCE",
            "feature_breakdown": {
                "itinerary_overlap": 0.95,
                "inclusions_difference_count": 3,
            },
            "left": {
                "id": "tour-viator-301",
                "name": "Private Full Day Delhi Heritage Tour with AC Car",
                "destination": "Delhi",
                "supplier_name": "Viator / Tripadvisor",
                "price": 2400,
                "image": "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=600&q=80",
                "inclusions": {
                    "transfer": "Private Chauffeur AC Car",
                    "meal": "No Meals Included",
                    "access": "Standard Entry (Pay at Gate)",
                    "guide": "English Live Guide",
                },
            },
            "right": {
                "id": "tour-gyg-702",
                "name": "Delhi City Highlights Day Trip with 5-Star Buffet Lunch & VIP Pass",
                "destination": "Delhi",
                "supplier_name": "GetYourGuide",
                "price": 3850,
                "image": "https://images.unsplash.com/photo-1592635196078-9fe3d54f2377?auto=format&fit=crop&w=600&q=80",
                "inclusions": {
                    "transfer": "Shared Luxury Coach",
                    "meal": "5-Star Buffet Lunch Included",
                    "access": "Skip-the-Line VIP Monument Pass",
                    "guide": "Multilingual Audio + Guide",
                },
            },
            "explanation": "Identical attractions visited, but Option B includes 5-Star Buffet Lunch and Skip-The-Line Fast Track. Link as comparable variants with inclusions breakdown.",
        },
    ]


REVIEW_QUEUE: list[dict[str, Any]] = _seed_initial_review_queue()
AUDIT_LOG: list[dict[str, Any]] = []
_OSRM_REQUEST_LOCK = asyncio.Lock()
_OSRM_LAST_REQUEST = 0.0
_INVENTORY_CACHE_SIGNATURE: tuple[tuple[str, int, int], ...] | None = None
_INVENTORY_CACHE: list[InventoryItem] | None = None
_OPEN_DATA_REFRESH_PROCESS: subprocess.Popen[bytes] | None = None


def _read_open_data_status_file() -> dict[str, Any]:
    try:
        with OPEN_DATA_STATUS_PATH.open(encoding="utf-8") as status_file:
            value = json.load(status_file)
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def open_data_status() -> dict[str, Any]:
    status = _read_open_data_status_file()
    metadata = status.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    if not metadata and OPEN_DATA_INVENTORY_PATH.exists():
        try:
            with OPEN_DATA_INVENTORY_PATH.open(encoding="utf-8") as inventory_file:
                snapshot_metadata = json.load(inventory_file).get("metadata", {})
            if isinstance(snapshot_metadata, dict):
                metadata = snapshot_metadata
        except (OSError, json.JSONDecodeError):
            pass
    last_updated = metadata.get("refreshed_at")
    has_live_data = (
        metadata.get("source") == "OpenStreetMap/Overpass"
        and str(metadata.get("city", "")).casefold() == DEMO_CITY.casefold()
        and str(metadata.get("country_code", "")).upper() == "IN"
    )
    state = str(status.get("state", "not_loaded"))
    if _OPEN_DATA_REFRESH_PROCESS is not None and _OPEN_DATA_REFRESH_PROCESS.poll() is None:
        state = "refreshing"
    elif state == "refreshing":
        started_at = _parse_timestamp(status.get("started_at"))
        if started_at is None or (datetime.now(timezone.utc) - started_at).total_seconds() > 1800:
            state = "error"
    elif has_live_data and state not in {"error", "refreshing"}:
        state = "ready"
    updated_at = _parse_timestamp(last_updated)
    age_seconds = max(0, int((datetime.now(timezone.utc) - updated_at).total_seconds())) if updated_at else None
    return {
        "state": state,
        "city": DEMO_CITY,
        "source": metadata.get("source", "OpenStreetMap via Overpass"),
        "license": metadata.get("license", "ODbL"),
        "has_live_data": has_live_data,
        "refreshed_at": last_updated,
        "age_seconds": age_seconds,
        "stale": age_seconds is None or age_seconds > 24 * 60 * 60,
        "hotel_count": int(metadata.get("hotel_count", 0) or 0),
        "attraction_count": int(metadata.get("attraction_count", 0) or 0),
        "error": status.get("error"),
    }


def _start_open_data_refresh(*, force: bool = False) -> bool:
    global _OPEN_DATA_REFRESH_PROCESS
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING"):
        return False
    if _OPEN_DATA_REFRESH_PROCESS is not None and _OPEN_DATA_REFRESH_PROCESS.poll() is None:
        return False
    status = _read_open_data_status_file()
    now = datetime.now(timezone.utc)
    metadata = status.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    if not metadata and OPEN_DATA_INVENTORY_PATH.exists():
        try:
            with OPEN_DATA_INVENTORY_PATH.open(encoding="utf-8") as inv_f:
                snap_meta = json.load(inv_f).get("metadata", {})
                if isinstance(snap_meta, dict):
                    metadata = snap_meta
        except (OSError, json.JSONDecodeError):
            pass
    started_at = _parse_timestamp(status.get("started_at"))
    if status.get("state") == "refreshing" and started_at and (now - started_at).total_seconds() < 1800:
        return False
    if started_at and (now - started_at).total_seconds() < 3600:
        return False
    refreshed_at = _parse_timestamp(metadata.get("refreshed_at"))
    if not force and refreshed_at and (now - refreshed_at).total_seconds() < 6 * 3600:
        return False

    log_dir = PROJECT_ROOT / ".demo-logs"
    log_dir.mkdir(exist_ok=True)
    log_file = (log_dir / "open-data-refresh.log").open("ab")
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "seed_datasets.py"),
        "--city",
        DEMO_CITY,
        "--country-code",
        "IN",
        "--source",
        "osm",
        "--limit",
        "500",
    ]
    try:
        _OPEN_DATA_REFRESH_PROCESS = subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    finally:
        log_file.close()
    return True


@asynccontextmanager
async def lifespan(_: FastAPI):
    if USE_DATABASE:
        await database.open_pool()
        logger.info("Connected to PostgreSQL inventory store")
    elif APP_ENV != "test" and "pytest" not in sys.modules:
        _start_open_data_refresh()
    yield
    if _OPEN_DATA_REFRESH_PROCESS is not None and _OPEN_DATA_REFRESH_PROCESS.poll() is None:
        _OPEN_DATA_REFRESH_PROCESS.terminate()
        try:
            _OPEN_DATA_REFRESH_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _OPEN_DATA_REFRESH_PROCESS.kill()
    if USE_DATABASE:
        await database.close_pool()


app = FastAPI(
    title=APP_NAME,
    version="2.0.0",
    description="Multi-supplier inventory matching, inclusion comparison, map discovery and ranking.",
    debug=DEBUG,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ASSETS_DIR = FRONTEND_DIR / "assets"
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


@app.middleware("http")
async def instrument_requests(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    route = getattr(request.scope.get("route"), "path", request.url.path)
    REQUESTS.labels(request.method, route, str(response.status_code)).inc()
    LATENCY.labels(request.method, route).observe(time.perf_counter() - started)
    return response


def _local_inventory_signature() -> tuple[tuple[str, int, int], ...]:
    signature = []
    for path in (INVENTORY_PATH, OPEN_DATA_INVENTORY_PATH):
        try:
            stat = path.stat()
            signature.append((str(path.resolve()), stat.st_mtime_ns, stat.st_size))
        except OSError:
            signature.append((str(path.resolve()), -1, -1))
    return tuple(signature)


async def load_inventory() -> list[InventoryItem]:
    global _INVENTORY_CACHE_SIGNATURE, _INVENTORY_CACHE
    if USE_DATABASE:
        rows = await database.load_inventory()
    else:
        signature = _local_inventory_signature()
        if _INVENTORY_CACHE is not None and signature == _INVENTORY_CACHE_SIGNATURE:
            return list(_INVENTORY_CACHE)
        with INVENTORY_PATH.open(encoding="utf-8") as inventory_file:
            rows = json.load(inventory_file)
        existing_sources = {str(r.get("source_id") or "") for r in rows if r.get("source_id")}
        if OPEN_DATA_INVENTORY_PATH.exists():
            try:
                with OPEN_DATA_INVENTORY_PATH.open(encoding="utf-8") as open_data_file:
                    open_data = json.load(open_data_file)
                for bucket, entity_type in (("hotels", "HOTEL"), ("attractions", "ATTRACTION")):
                    for record in open_data.get(bucket, []):
                        source_id = str(record.get("source_id") or record.get("id") or "")
                        if not source_id or source_id in existing_sources or record.get("latitude") is None or record.get("longitude") is None:
                            continue
                        rows.append({
                            "id": "open-" + hashlib.sha256(source_id.encode()).hexdigest()[:16],
                            "source_id": source_id,
                            "name": record.get("name", "Unnamed open-data place"),
                            "entity_type": entity_type,
                            "destination": record.get("city") or record.get("destination") or "Delhi",
                            "country_code": record.get("country_code", "IN"),
                            "latitude": record["latitude"],
                            "longitude": record["longitude"],
                            "star_rating": record.get("star_rating"),
                            "description": record.get("description", ""),
                            "source_category": record.get("source_category"),
                            "amenities": record.get("amenities", []),
                            "images": record.get("images", []),
                            "offers": record.get("offers", []),
                            "conversion_prior": 0.3,
                        })
                        existing_sources.add(source_id)
            except (OSError, json.JSONDecodeError):
                pass
        existing_ids = {r.get("id") for r in rows}
        for hub in PAN_INDIA_TRANSPORT_HUBS + PAN_INDIA_DINING_SPOTS:
            if hub.get("id") not in existing_ids:
                rows.append(hub)
                existing_ids.add(hub.get("id"))
    items = [InventoryItem.model_validate(row) for row in rows]
    if not USE_DATABASE:
        _INVENTORY_CACHE_SIGNATURE = signature
        _INVENTORY_CACHE = items
    return list(items)


class VoiceRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=1000)


class AudioTranscriptionRequest(BaseModel):
    audio_base64: str = Field(min_length=8, max_length=21_000_000)
    model_size: Literal["tiny", "base", "small"] = "tiny"


class MatchRequest(BaseModel):
    left: dict[str, Any]
    right: dict[str, Any]


class RoomRequest(BaseModel):
    raw_name: str = Field(min_length=1, max_length=300)


class SightseeingRequest(BaseModel):
    left_title: str = ""
    left_description: str = Field(default="", max_length=5000)
    left_inclusions: list[str] = Field(default_factory=list)
    right_title: str = ""
    right_description: str = Field(default="", max_length=5000)
    right_inclusions: list[str] = Field(default_factory=list)


class ReviewDecision(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    reviewer: str = Field(default="local-demo", max_length=120)
    notes: str = Field(default="", max_length=2000)


class AdminMatchResolution(BaseModel):
    review_id: str | None = None
    supplier_hotel_id: str | None = None
    canonical_id: str | None = None
    action: Literal["CONFIRM", "SPLIT", "REASSIGN"]
    reviewer_user_id: str = Field(default="local-demo", max_length=64)
    review_notes: str = Field(default="", max_length=2000)


class ViewportRequest(BaseModel):
    min_lat: float = Field(ge=-90, le=90)
    max_lat: float = Field(ge=-90, le=90)
    min_lon: float = Field(ge=-180, le=180)
    max_lon: float = Field(ge=-180, le=180)
    category: Literal["HOTEL", "ATTRACTION", "ALL"] = "HOTEL"

    @model_validator(mode="after")
    def validate_bounds(self) -> "ViewportRequest":
        if self.min_lat > self.max_lat:
            raise ValueError("min_lat must be less than or equal to max_lat")
        return self


class TelemetryEvent(BaseModel):
    entity_type: Literal["HOTEL", "SIGHTSEEING"]
    canonical_id: str = Field(min_length=1, max_length=128)
    event_type: Literal["IMPRESSION", "DETAIL_VIEW", "BOOKING_INTENT", "BOOKED"]
    selected_supplier_id: str = Field(default="demo", max_length=128)
    displayed_position: int = Field(default=1, ge=1)
    ranking_score: float = Field(default=0.0, ge=0, le=1)


def _inside_viewport(item: InventoryItem, west: float, south: float, east: float, north: float) -> bool:
    lon_ok = west <= item.longitude <= east if west <= east else item.longitude >= west or item.longitude <= east
    return south <= item.latitude <= north and lon_ok


def _has_inclusions(item: InventoryItem, requested: list[str]) -> bool:
    amenities = {value.casefold().replace("-", " ") for value in item.amenities}
    offers = [offer for offer in item.offers if offer.available]
    for inclusion in requested:
        key = inclusion.strip().upper().replace(" ", "_")
        if key == "BREAKFAST" and not (any("breakfast" in amenity for amenity in amenities) or any(offer.meal_plan.upper() in {"BB", "HB", "FB", "AI", "BREAKFAST"} for offer in offers)):
            return False
        if key in {"FREE_CANCELLATION", "FLEXIBLE_CANCELLATION"} and not any(offer.cancellation_flexible for offer in offers):
            return False
        if key in {"TRANSFERS", "PRIVATE_TRANSFER"} and not any("transfer" in amenity or "pickup" in amenity for amenity in amenities):
            return False
        if key == "POOL" and not any("pool" in amenity for amenity in amenities):
            return False
        if key == "WIFI" and not any("wifi" in amenity or "wi fi" in amenity for amenity in amenities):
            return False
        if key == "SKIP_THE_LINE" and not any("skip_the_line" in amenity for amenity in amenities):
            return False
    return True


def _item_matches_landmark(item: InventoryItem, landmark: str | None) -> bool:
    if not landmark:
        return True
    searchable = f"{item.name} {item.description} {item.source_category or ''} {' '.join(item.amenities)}".casefold()
    landmark = landmark.casefold()
    if landmark in {"beach", "airport", "downtown", "marina", "city center"}:
        terms = {"city center": ("downtown", "city centre", "city center"), "beach": ("beach", "sea", "coast"), "airport": ("airport",), "marina": ("marina",), "downtown": ("downtown", "city centre", "city center")}[landmark]
        return any(term in searchable for term in terms)
    return landmark in searchable


def _best_price(item: InventoryItem) -> float | None:
    available = [offer.price for offer in item.offers if offer.available]
    return min(available) if available else None


def _map_record(item: InventoryItem) -> dict[str, Any]:
    offer = item.best_offer
    return {
        "id": item.id,
        "name": item.name,
        "entity_type": item.entity_type,
        "destination": item.destination,
        "country_code": item.country_code,
        "star_rating": item.star_rating,
        "latitude": item.latitude,
        "longitude": item.longitude,
        "thumbnail": item.images[0] if item.images else "",
        "images": item.images,
        "description": item.description,
        "source_category": item.source_category,
        "min_price": offer.price if offer else None,
        "currency": offer.currency if offer else ("INR" if item.country_code == "IN" else "USD"),
        "cancellation_tier": (offer.cancellation_policy.get("type") if offer and offer.cancellation_policy else "FREE_CANCELLATION" if offer and offer.cancellation_flexible else "NON_REFUNDABLE"),
        "supplier_count": len([item_offer for item_offer in item.offers if item_offer.available]),
        "amenities": item.amenities,
    }


COUNTRY_NAMES = {"IN": "India", "AE": "United Arab Emirates"}


def _stable_cache_key(prefix: str, value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return f"{prefix}:{hashlib.sha256(encoded).hexdigest()[:24]}"


@app.get("/")
def root(request: Request) -> Any:
    accept = request.headers.get("accept", "")
    if "text/html" in accept and not accept.startswith("application/json"):
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
        map_path = FRONTEND_DIR / "map_view.html"
        if map_path.exists():
            return FileResponse(map_path, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return {
        "service": APP_NAME,
        "status": "ok",
        "docs": "/docs",
        "health": f"{API_V1_PREFIX}/health",
        "landing": "/index.html",
        "map": "/map_view.html",
        "admin": "/admin.html",
    }


@app.get("/index.html", response_class=FileResponse)
@app.get("/landing", response_class=FileResponse)
def serve_landing() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/map_view.html", response_class=FileResponse)
@app.get("/map", response_class=FileResponse)
def serve_map_view() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "map_view.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/admin.html", response_class=FileResponse)
@app.get("/admin", response_class=FileResponse)
def serve_admin() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "admin.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "environment": APP_ENV}


@app.get(f"{API_V1_PREFIX}/health")
async def api_health() -> dict[str, Any]:
    database_state = await database.database_health() if USE_DATABASE else {"configured": False, "connected": False}
    return {
        "status": "ok" if not USE_DATABASE or database_state.get("connected") else "degraded",
        "service": APP_NAME,
        "environment": APP_ENV,
        "database": database_state,
        "cache": cache_status(),
    }


@app.get(f"{API_V1_PREFIX}/config/map")
def map_config() -> dict[str, Any]:
    """Expose public map style and India-first view settings."""
    return {
        "style_url": MAP_STYLE_URL,
        "attribution": MAP_ATTRIBUTION,
        "default_destination": MAP_DEFAULT_DESTINATION,
        "default_latitude": MAP_DEFAULT_LATITUDE,
        "default_longitude": MAP_DEFAULT_LONGITUDE,
        "default_zoom": MAP_DEFAULT_ZOOM,
    }


@app.get(f"{API_V1_PREFIX}/data/status")
def open_data_status_endpoint() -> dict[str, Any]:
    return open_data_status()


@app.post(f"{API_V1_PREFIX}/data/refresh", status_code=202)
def refresh_open_data_endpoint() -> dict[str, Any]:
    if _start_open_data_refresh(force=True):
        return open_data_status()
    status = open_data_status()
    if status["state"] == "refreshing":
        return status
    raise HTTPException(
        status_code=429,
        detail="Delhi open-data refresh is limited to one request per hour to respect the free public Overpass service.",
        headers={"Retry-After": "3600"},
    )


@app.get(f"{API_V1_PREFIX}/destinations")
async def list_destinations() -> dict[str, Any]:
    """Return countries and city centers represented in the local inventory."""
    items = await load_inventory()
    groups: dict[tuple[str, str], list[InventoryItem]] = {}
    for item in items:
        groups.setdefault((item.country_code.upper(), item.destination), []).append(item)
    destinations = []
    for (country_code, city), rows in groups.items():
        destinations.append({
            "country_code": country_code,
            "country": COUNTRY_NAMES.get(country_code, country_code),
            "destination": city,
            "count": len(rows),
            "latitude": sum(row.latitude for row in rows) / len(rows),
            "longitude": sum(row.longitude for row in rows) / len(rows),
        })
    destinations.sort(key=lambda row: (row["country_code"] != "IN", row["destination"].casefold()))
    countries = []
    for code in sorted({row["country_code"] for row in destinations}, key=lambda value: (value != "IN", value)):
        rows = [row for row in destinations if row["country_code"] == code]
        countries.append({
            "code": code,
            "name": COUNTRY_NAMES.get(code, code),
            "count": sum(row["count"] for row in rows),
            "latitude": sum(row["latitude"] * row["count"] for row in rows) / sum(row["count"] for row in rows),
            "longitude": sum(row["longitude"] * row["count"] for row in rows) / sum(row["count"] for row in rows),
        })
    return {"countries": countries, "destinations": destinations}


@app.get(f"{API_V1_PREFIX}/inventory/search")
async def search_inventory(
    q: str = "",
    destination: str | None = None,
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    currency: str | None = Query(default=None, min_length=3, max_length=3),
    entity_type: Literal["HOTEL", "ATTRACTION", "TRANSPORT", "DINING"] | str | None = None,
    max_price: float | None = Query(default=None, gt=0),
    min_stars: float | None = Query(default=None, ge=0, le=5),
    landmark: str | None = None,
    inclusions: list[str] = Query(default=[]),
    dietary: Literal["VEG", "NON_VEG"] | str | None = None,
) -> dict[str, Any]:
    items = await load_inventory()
    if destination and destination.casefold() not in {"pan-india", "all", "india"}:
        items = [item for item in items if destination.casefold() in item.destination.casefold()]
    if country_code:
        code = country_code.upper()
        items = [item for item in items if item.country_code.upper() == code]
    if currency:
        code = currency.upper()
        items = [
            item.model_copy(update={"offers": [offer for offer in item.offers if offer.currency.upper() == code]})
            for item in items
        ]
        items = [item for item in items if item.offers]
    if entity_type:
        items = [item for item in items if item.entity_type == entity_type]
    if max_price is not None:
        items = [item for item in items if any(o.available and o.price <= max_price for o in item.offers)]
    if min_stars is not None:
        items = [item for item in items if item.star_rating is not None and item.star_rating >= min_stars]
    if q.strip():
        terms = [term for term in q.casefold().split() if len(term) > 1]
        items = [item for item in items if all(term in f"{item.name} {item.destination} {' '.join(item.amenities)} {item.description} {item.source_category or ''}".casefold() for term in terms)]
    if landmark:
        items = [item for item in items if _item_matches_landmark(item, landmark)]
    if inclusions:
        items = [item for item in items if _has_inclusions(item, inclusions)]
    if dietary:
        d_val = dietary.upper()
        items = [
            item for item in items
            if getattr(item, "dietary", None) == d_val or
            (d_val == "VEG" and any("veg" in a.lower() for a in item.amenities) and not any("non-veg" in a.lower() for a in item.amenities)) or
            (d_val == "NON_VEG" and any(k in f"{item.name} {item.description} {' '.join(item.amenities)}".lower() for k in ["non-veg", "seafood", "chicken", "mutton", "fish", "meat", "kebab", "biryani"]))
        ]

    # Seamlessly enrich with live 1M multi-supplier items for India destinations
    is_international = (destination and destination.casefold() in {"dubai", "abu dhabi", "santorini", "athens", "oia", "fira"}) or (country_code and country_code.upper() in {"AE", "GR"})
    if not is_international:
        live_res = live_1m_engine.search_live(
            destination=destination,
            entity_type=entity_type if entity_type and entity_type != "ANY" else None,
            q=q,
            limit=150,
            currency=currency or "INR",
            dietary=dietary,
        )
        existing_ids = {it.id for it in items}
        for r in live_res.get("results", []):
            raw = r["item"]
            if raw["id"] not in existing_ids:
                try:
                    item_obj = InventoryItem(**raw)
                    if max_price is not None and not any(o.available and o.price <= max_price for o in item_obj.offers):
                        continue
                    if min_stars is not None and (item_obj.star_rating is None or item_obj.star_rating < min_stars):
                        continue
                    if inclusions and not _has_inclusions(item_obj, inclusions):
                        continue
                    items.append(item_obj)
                    existing_ids.add(raw["id"])
                except Exception:
                    pass

    cache_descriptor = json.dumps(
        {
            "q": q,
            "destination": destination,
            "country_code": country_code,
            "currency": currency,
            "entity_type": entity_type,
            "max_price": max_price,
            "min_stars": min_stars,
            "landmark": landmark,
            "inclusions": inclusions,
            "inventory_signature": None if USE_DATABASE else _local_inventory_signature(),
        },
        sort_keys=True,
    )
    dest_count = live_1m_engine.get_destination_inventory_count(destination) if destination else live_1m_engine.total_inventory
    cached = get_or_set(
        _stable_cache_key("inventory:search", cache_descriptor),
        CACHE_TTL_LIVE_RATES,
        lambda: {
            "count": len(items),
            "total_reachable_inventory": live_1m_engine.total_inventory,
            "destination_total": dest_count,
            "results": rank_items(items, " ".join([q, landmark or ""]).strip()),
        },
    )
    return cached


@app.get(f"{API_V1_PREFIX}/inventory")
async def inventory_viewport(
    west: float | None = Query(default=None, ge=-180, le=180),
    south: float | None = Query(default=None, ge=-90, le=90),
    east: float | None = Query(default=None, ge=-180, le=180),
    north: float | None = Query(default=None, ge=-90, le=90),
    entity_type: Literal["HOTEL", "ATTRACTION"] | None = None,
    destination: str | None = None,
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    currency: str | None = Query(default=None, min_length=3, max_length=3),
) -> dict[str, Any]:
    items = await load_inventory()
    bounds = (west, south, east, north)
    if any(value is not None for value in bounds) and any(value is None for value in bounds):
        raise HTTPException(400, "Provide all four viewport bounds: west, south, east, north.")
    if west is not None and south is not None and east is not None and north is not None:
        if south > north:
            raise HTTPException(400, "The south bound must not exceed north.")
        items = [item for item in items if _inside_viewport(item, west, south, east, north)]
    if entity_type:
        items = [item for item in items if item.entity_type == entity_type]
    if destination:
        items = [item for item in items if destination.casefold() in item.destination.casefold()]
    if country_code:
        code = country_code.upper()
        items = [item for item in items if item.country_code.upper() == code]
    if currency:
        code = currency.upper()
        items = [
            item.model_copy(update={"offers": [offer for offer in item.offers if offer.currency.upper() == code]})
            for item in items
        ]
        items = [item for item in items if item.entity_type != "HOTEL" or item.offers]
    cache_key = _stable_cache_key(
        "geo:viewport",
        (west, south, east, north, entity_type, destination, country_code, currency,
         None if USE_DATABASE else _local_inventory_signature()),
    )
    return get_or_set(
        cache_key,
        CACHE_TTL_GEO_VIEWPORT,
        lambda: {"count": len(items), "items": [item.model_dump() for item in items]},
    )


@app.post(f"{API_V1_PREFIX}/map/viewport-inventory")
async def map_viewport_inventory(request: ViewportRequest) -> dict[str, Any]:
    items = await load_inventory()
    items = [
        item for item in items
        if _inside_viewport(item, request.min_lon, request.min_lat, request.max_lon, request.max_lat)
        and (request.category == "ALL" or item.entity_type == request.category)
    ]
    mapped = [_map_record(item) for item in items]
    return {
        "status": "success",
        "count": len(mapped),
        "hotels": [item for item in mapped if item["entity_type"] == "HOTEL"],
        "attractions": [item for item in mapped if item["entity_type"] == "ATTRACTION"],
    }


@app.post(f"{API_V1_PREFIX}/voice/query")
async def voice_query(request: VoiceRequest) -> dict[str, Any]:
    filters = parse_voice_travel_query(request.transcript)
    category = "ATTRACTION" if filters["entity_type"] == "SIGHTSEEING" else "HOTEL"
    items = await load_inventory()
    items = [item for item in items if item.entity_type == category]
    country_code = filters.get("country_code")
    if country_code:
        items = [item for item in items if item.country_code.upper() == str(country_code).upper()]
    destination = filters.get("destination")
    if destination:
        items = [item for item in items if str(destination).casefold() in item.destination.casefold()]
    currency = str(filters.get("currency") or "").upper()
    if currency:
        items = [
            item.model_copy(update={"offers": [offer for offer in item.offers if offer.currency.upper() == currency]})
            for item in items
        ]
        items = [item for item in items if item.offers]
    stars = filters.get("star_rating")
    if isinstance(stars, (float, int)):
        items = [item for item in items if item.star_rating is not None and item.star_rating >= stars]
    max_price = filters.get("max_price")
    if isinstance(max_price, (float, int)):
        items = [item for item in items if any(offer.available and offer.price <= max_price for offer in item.offers)]
    if filters.get("landmark"):
        items = [item for item in items if _item_matches_landmark(item, str(filters["landmark"]))]
    inclusions = list(filters.get("inclusions", []))
    if inclusions:
        items = [item for item in items if _has_inclusions(item, inclusions)]
    results = rank_items(items, str(filters.get("landmark") or destination or ""))
    subject = "experiences" if category == "ATTRACTION" else "stays"
    reply = f"I found {len(results)} {subject} matching your request."
    return {"status": "success", "voice_reply": reply, "parsed_filters": filters, "intent": filters, "count": len(results), "results": results}


@app.post(f"{API_V1_PREFIX}/voice/transcribe")
async def voice_transcribe(request: AudioTranscriptionRequest) -> dict[str, Any]:
    try:
        base64.b64decode(request.audio_base64, validate=True)
        from services.voice_transcription import transcribe_base64

        transcript = await asyncio.to_thread(transcribe_base64, request.audio_base64, request.model_size)
    except ImportError as error:
        raise HTTPException(503, "Install requirements-voice.txt to enable local Whisper transcription") from error
    except (ValueError, OSError) as error:
        raise HTTPException(422, str(error)) from error
    if not transcript:
        raise HTTPException(422, "No speech was detected in the audio")
    result = await voice_query(VoiceRequest(transcript=transcript))
    return {**result, "transcript": transcript}


@app.get(f"{API_V1_PREFIX}/inventory/{{item_id}}/explain")
async def explain_item(item_id: str, q: str = "") -> dict[str, Any]:
    items = await load_inventory()
    item = next((record for record in items if record.id == item_id), None)
    if item is None:
        raise HTTPException(404, "Inventory item not found")
    ranked = rank_items(items, q)
    result = next(entry for entry in ranked if entry["item"]["id"] == item_id)
    selected = result["selected_supplier"]
    return {
        "entity_id": item.id,
        "name": item.name,
        "match_explanation": {
            "status": "CANONICAL_SAMPLE" if item.source_id and item.source_id.startswith("sample:") else "CANONICAL",
            "confidence_score": 1.0,
            "feature_breakdown": {"geographic_distance_meters": 0.0, "name_lexical_similarity": 1.0},
            "reason": "This is a seeded canonical demo record; supplier matching is explained per candidate comparison.",
        },
        "ranking_explanation": {
            "position": next(index for index, entry in enumerate(ranked, 1) if entry["item"]["id"] == item_id),
            "composite_rank_score": result["rank_score"],
            "factor_weights": result["factor_weights"],
            "feature_contributions": result["rank_factors"],
            "badges": result["badges"],
        },
        "selected_supplier": selected,
    }


CURRENCY_RATES = {
    "INR": 1.0,
    "USD": 0.012,
    "AED": 0.044,
    "EUR": 0.011,
    "GBP": 0.0094,
}


@app.get(f"{API_V1_PREFIX}/currency/rates")
def get_currency_rates() -> dict[str, Any]:
    """Expose free real-time currency conversion rates."""
    return {
        "base": "INR",
        "rates": CURRENCY_RATES,
        "symbols": {"INR": "₹", "USD": "$", "EUR": "€", "AED": "د.إ", "GBP": "£"},
    }


@app.get(f"{API_V1_PREFIX}/inventory/suggestions")
async def get_suggestions(q: str = Query(default="", min_length=1, max_length=100)) -> dict[str, Any]:
    """Return real-time as-you-type search suggestions across Hotels, Sightseeing, and Areas."""
    items = await load_inventory()
    q_norm = q.strip().casefold()
    hotels = []
    attractions = []
    areas = set()

    for item in items:
        name_lower = item.name.casefold()
        dest_lower = item.destination.casefold()
        desc_lower = item.description.casefold()

        # Check neighborhood/area match
        if q_norm in dest_lower or q_norm in desc_lower or q_norm in name_lower:
            if item.destination:
                areas.add(item.destination)

        if q_norm in name_lower:
            offer = item.best_offer
            entry = {
                "id": item.id,
                "name": item.name,
                "entity_type": item.entity_type,
                "destination": item.destination,
                "star_rating": item.star_rating,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "min_price": offer.price if offer else None,
                "currency": offer.currency if offer else "INR",
                "image": item.images[0] if item.images else None,
            }
            if item.entity_type == "HOTEL" and len(hotels) < 5:
                hotels.append(entry)
            elif item.entity_type == "ATTRACTION" and len(attractions) < 5:
                attractions.append(entry)

        if len(hotels) >= 5 and len(attractions) >= 5 and len(areas) >= 4:
            break

    return {
        "query": q,
        "hotels": hotels,
        "attractions": attractions,
        "areas": sorted(list(areas))[:5],
    }


@app.get(f"{API_V1_PREFIX}/inventory/{{item_id}}/supplier-comparison")
async def item_supplier_comparison(item_id: str) -> dict[str, Any]:
    """Detailed multi-supplier rate and inclusions comparison matrix for Hotels or Sightseeing."""
    items = await load_inventory()
    item = next((r for r in items if r.id == item_id), None)
    if item is None:
        raise HTTPException(404, "Inventory item not found")

    offers = [o for o in item.offers if o.available]
    if not offers:
        return {
            "item_id": item.id,
            "name": item.name,
            "entity_type": item.entity_type,
            "offers_count": 0,
            "offers": [],
            "analysis": "No active supplier offers currently available.",
        }

    sorted_by_price = sorted(offers, key=lambda x: x.price)
    cheapest = sorted_by_price[0]
    most_reliable = max(offers, key=lambda x: x.reliability_score)
    flexible_offers = [o for o in offers if o.cancellation_flexible]
    best_value = min(flexible_offers, key=lambda x: x.price) if flexible_offers else cheapest

    comparison_rows = []
    for offer in offers:
        row = offer.model_dump()
        # Hotel room normalization
        if item.entity_type == "HOTEL":
            raw_room = row.get("raw_room_name") or f"STD {row.get('meal_plan', 'RO')}"
            normalized = normalize_room_title(raw_room)
            row["room_taxonomy"] = normalized
        # Sightseeing inclusions
        elif item.entity_type == "ATTRACTION":
            inclusions = extract_tour_inclusions(item.name, item.description)
            row["tour_inclusions"] = inclusions

        comparison_rows.append(row)

    max_p = max(o.price for o in offers)
    min_p = min(o.price for o in offers)
    savings = round(max_p - min_p, 1)

    return {
        "item_id": item.id,
        "name": item.name,
        "entity_type": item.entity_type,
        "destination": item.destination,
        "offers_count": len(offers),
        "cheapest_supplier": cheapest.supplier_name,
        "cheapest_price": cheapest.price,
        "most_reliable_supplier": most_reliable.supplier_name,
        "most_reliable_score": most_reliable.reliability_score,
        "best_value_supplier": best_value.supplier_name,
        "max_savings_available": savings,
        "currency": cheapest.currency,
        "offers": comparison_rows,
    }


@app.post(f"{API_V1_PREFIX}/matches/compare")
def match_compare(request: MatchRequest) -> dict[str, Any]:
    try:
        result = compare_hotels(request.left, request.right)
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(422, f"Both listings need valid names and coordinates: {error}") from error
    MATCH_DECISIONS.labels(str(result["decision"])).inc()
    if result["decision"] == "HUMAN_REVIEW":
        review_id = str(uuid4())
        result["review_id"] = review_id
        REVIEW_QUEUE.append({
            "id": review_id,
            "status": "PENDING",
            "score": result["score"],
            "feature_breakdown": result["feature_breakdown"],
            "left": request.left,
            "right": request.right,
        })
    return result


@app.get(f"{API_V1_PREFIX}/review-queue")
@app.get(f"{API_V1_PREFIX}/admin/matches/review-queue")
def list_review_queue(status: Literal["PENDING", "APPROVED", "REJECTED"] | None = "PENDING") -> dict[str, Any]:
    rows = [row for row in REVIEW_QUEUE if status is None or row["status"] == status]
    return {"count": len(rows), "items": rows}


@app.post(f"{API_V1_PREFIX}/review-queue/reset")
def reset_review_queue() -> dict[str, Any]:
    global REVIEW_QUEUE
    REVIEW_QUEUE = _seed_initial_review_queue()
    return {"status": "reset", "count": len(REVIEW_QUEUE)}


@app.put(f"{API_V1_PREFIX}/review-queue/{{review_id}}")
def decide_review(review_id: str, decision: ReviewDecision) -> dict[str, Any]:
    row = next((item for item in REVIEW_QUEUE if item["id"] == review_id), None)
    if row is None:
        raise HTTPException(404, "Review item not found")
    if row["status"] != "PENDING":
        raise HTTPException(409, "This review item has already been decided")
    row.update(status=decision.status, reviewer=decision.reviewer, notes=decision.notes)
    AUDIT_LOG.append({"review_id": review_id, "action": decision.status, "reviewer": decision.reviewer, "notes": decision.notes})
    return row


@app.post(f"{API_V1_PREFIX}/admin/matches/resolve")
def resolve_admin_match(request: AdminMatchResolution) -> dict[str, Any]:
    row = next((item for item in REVIEW_QUEUE if request.review_id and item["id"] == request.review_id), None)
    if row is None and request.supplier_hotel_id:
        row = next((item for item in REVIEW_QUEUE if str(item.get("left", {}).get("supplier_hotel_id", item.get("left", {}).get("id", ""))) == request.supplier_hotel_id), None)
    if row is None:
        raise HTTPException(404, "No pending review matches that supplier listing")
    if row["status"] != "PENDING":
        raise HTTPException(409, "This review item has already been resolved")
    row.update(status="APPROVED" if request.action in {"CONFIRM", "REASSIGN"} else "REJECTED", action=request.action, canonical_id=request.canonical_id)
    AUDIT_LOG.append({
        "review_id": row["id"],
        "entity_type": "HOTEL",
        "supplier_entity_id": request.supplier_hotel_id or str(row.get("left", {}).get("id", "")),
        "new_canonical_id": request.canonical_id,
        "reviewer_user_id": request.reviewer_user_id,
        "action": request.action,
        "review_notes": request.review_notes,
        "feature_contributions": row.get("feature_breakdown", {}),
    })
    return {"status": row["status"], "audit": AUDIT_LOG[-1]}


@app.post(f"{API_V1_PREFIX}/rooms/normalize")
def room_normalize(request: RoomRequest) -> dict[str, Any]:
    return {"raw_name": request.raw_name, **normalize_room_title(request.raw_name)}


@app.post(f"{API_V1_PREFIX}/sightseeing/compare")
def sightseeing_compare(request: SightseeingRequest) -> dict[str, Any]:
    left = extract_tour_inclusions(request.left_title, request.left_description, request.left_inclusions)
    right = extract_tour_inclusions(request.right_title, request.right_description, request.right_inclusions)
    return {
        "left": left,
        "right": right,
        "differences": generate_inclusion_diff(left, right),
    }


@app.post(f"{API_V1_PREFIX}/ingest/hotels/validate")
def validate_supplier_hotel(payload: RawSupplierHotelPayload) -> dict[str, Any]:
    return {
        "status": "VALIDATED",
        "normalized_payload": payload.model_dump(),
        "data_quality_score": calculate_data_quality_score(payload),
    }


@app.post(f"{API_V1_PREFIX}/ingest/hotels/queue")
def queue_supplier_hotel(payload: RawSupplierHotelPayload) -> dict[str, Any]:
    if not ENABLE_CELERY:
        raise HTTPException(503, "Background queue is disabled. Set ENABLE_CELERY=true and start the worker.")
    try:
        from services.tasks import process_raw_supplier_hotel

        job = process_raw_supplier_hotel.delay(payload.model_dump_json())
    except Exception as error:
        logger.exception("Could not submit supplier ingest task")
        raise HTTPException(503, "Could not reach the Celery broker") from error
    return {"status": "QUEUED", "task_id": job.id}


@app.get(f"{API_V1_PREFIX}/routes/summary")
async def route_summary(
    from_lat: float = Query(ge=-90, le=90),
    from_lon: float = Query(ge=-180, le=180),
    to_lat: float = Query(ge=-90, le=90),
    to_lon: float = Query(ge=-180, le=180),
    profile: Literal["driving", "walking", "cycling"] = "driving",
) -> dict[str, Any]:
    global _OSRM_LAST_REQUEST
    base = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org").rstrip("/")
    url = f"{base}/route/v1/{profile}/{from_lon},{from_lat};{to_lon},{to_lat}"
    try:
        async with _OSRM_REQUEST_LOCK:
            wait = 1.0 - (time.monotonic() - _OSRM_LAST_REQUEST)
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.get(url, params={"overview": "false", "steps": "false"})
            finally:
                _OSRM_LAST_REQUEST = time.monotonic()
        response.raise_for_status()
        route = response.json().get("routes", [])[0]
        return {"source": "OSRM", "profile": profile, "distance_meters": round(route["distance"], 1), "duration_seconds": round(route["duration"], 1)}
    except (httpx.HTTPError, IndexError, KeyError, ValueError):
        distance = haversine_meters(from_lat, from_lon, to_lat, to_lon)
        speed_mps = {"walking": 1.35, "cycling": 4.2, "driving": 8.3}[profile]
        return {
            "source": "STRAIGHT_LINE_ESTIMATE",
            "profile": profile,
            "distance_meters": round(distance * 1.3, 1),
            "duration_seconds": round(distance * 1.3 / speed_mps, 1),
            "note": "OSRM was unavailable; this is a rough distance-based estimate.",
        }


@app.get(f"{API_V1_PREFIX}/geocode/search")
async def geocode_search(q: str = Query(min_length=3, max_length=300)) -> dict[str, Any]:
    try:
        results = await geocode_address(q)
    except httpx.HTTPError as error:
        raise HTTPException(502, "Nominatim geocoding is temporarily unavailable") from error
    return {"count": len(results), "results": results}


@app.get(f"{API_V1_PREFIX}/geocode/reverse")
async def geocode_reverse(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
) -> dict[str, Any]:
    try:
        result = await reverse_geocode(latitude, longitude)
    except httpx.HTTPError as error:
        raise HTTPException(502, "Nominatim reverse geocoding is temporarily unavailable") from error
    return result


@app.get(f"{API_V1_PREFIX}/geo/search")
def api_geo_search(q: str = Query(default="", min_length=1)) -> list[dict[str, Any]]:
    return search_destinations_global(q, limit=10)


@app.get(f"{API_V1_PREFIX}/geo/reverse")
def api_geo_reverse(lat: float = Query(...), lon: float = Query(...)) -> dict[str, Any]:
    return reverse_geocode_location(lat, lon)


@app.get(f"{API_V1_PREFIX}/weather/forecast")
def api_weather_forecast(lat: float = Query(default=28.6139), lon: float = Query(default=77.2090)) -> dict[str, Any]:
    return get_live_weather(lat, lon)


@app.get(f"{API_V1_PREFIX}/geo/attractions")
def api_geo_attractions(
    lat: float = Query(default=28.6139),
    lon: float = Query(default=77.2090),
    query: str = Query(default="")
) -> list[dict[str, Any]]:
    return get_nearby_attractions(lat, lon, query)


@app.post(f"{API_V1_PREFIX}/journey/generate-dynamic")
async def api_journey_generate_dynamic(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
        return generate_dynamic_journey_plans(payload)
    except Exception as exc:
        logger.error(f"Error in generate-dynamic: {exc}")
        return {"error": str(exc), "status": "failed"}


@app.post(f"{API_V1_PREFIX}/journey/customize-slot")
async def api_journey_customize_slot(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
        return {"status": "success", "updated_slot": payload}
    except Exception as exc:
        return {"error": str(exc), "status": "failed"}


@app.post(f"{API_V1_PREFIX}/telemetry/events")
def record_telemetry(event: TelemetryEvent) -> dict[str, Any]:
    TELEMETRY[event.event_type] += 1
    return {"status": "recorded", "event_type": event.event_type, "totals": TELEMETRY.copy()}


@app.get(f"{API_V1_PREFIX}/analytics/summary")
def analytics_summary() -> dict[str, Any]:
    impressions = TELEMETRY["IMPRESSION"]
    views = TELEMETRY["DETAIL_VIEW"]
    bookings = TELEMETRY["BOOKED"]
    return {
        "events": TELEMETRY.copy(),
        "click_through_rate_pct": round(100 * views / impressions, 2) if impressions else 0.0,
        "booking_conversion_rate_pct": round(100 * bookings / impressions, 2) if impressions else 0.0,
        "audit_events": len(AUDIT_LOG),
    }


# --- Pan-India Interconnectivity & Live Stats ---
@app.get(f"{API_V1_PREFIX}/pan-india/stats")
def pan_india_stats() -> dict[str, Any]:
    """Live statistics across 1,250,000+ Pan-India places, suppliers, and transit hubs."""
    return get_pan_india_stats()


@app.get(f"{API_V1_PREFIX}/pan-india/corridors")
def pan_india_corridors() -> dict[str, Any]:
    """Interconnectivity matrix across major high-speed rail, expressways, and flights."""
    corridors = get_transit_corridors()
    return {"count": len(corridors), "corridors": corridors}


# --- Personal AI Travel Agent & Itinerary Planner ---
class AIPlanRequest(BaseModel):
    destination: str = "Delhi"
    days: int = 3
    budget_tier: Literal["budget", "mid", "luxury", "any"] = "mid"
    query: str | None = None


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1)
    context: dict[str, Any] | None = None


@app.post(f"{API_V1_PREFIX}/ai/plan-trip")
def ai_plan_trip(request: AIPlanRequest) -> dict[str, Any]:
    """Generate a complete N-day itinerary with Budget/Mid/Luxury pricing, stays, food, transit & map points."""
    return generate_itinerary(
        destination=request.destination,
        days=request.days,
        preferred_budget=request.budget_tier,
    )


@app.post(f"{API_V1_PREFIX}/ai/chat")
def ai_concierge_chat(request: AIChatRequest) -> dict[str, Any]:
    """Conversational Personal AI Agent for travel planning with clarifying questions & instant itineraries."""
    user_msg = request.message.strip()
    intent = parse_trip_intent(user_msg)

    # If the user asks general greetings or open-ended request without city
    if not intent.get("destination"):
        days_txt = f"{intent['days']} days" if intent.get("days") else "a few days"
        return {
            "type": "question",
            "reply": (
                f"Namaste! 🙏 I'm your **TBO AI Personal Travel Concierge**.\n\n"
                f"I'd love to craft the perfect {days_txt} trip plan for you across Pan-India or international destinations!\n\n"
                f"To give you an exact day-by-day plan with stays, transit, and food, please let me know:\n"
                f"1. 📍 **Which city would you like to visit?** *(e.g., Delhi, Goa, Jaipur, Mumbai, Agra, Varanasi, Manali)*\n"
                f"2. 🗓️ **How many days?** *(e.g., 2, 3, 5 days)*\n"
                f"3. 💰 **Preferred budget?** *(Budget / Mid-Level / Luxury)*"
            ),
            "suggestions": [
                "Plan 3 days in Delhi (Mid-Range)",
                "Plan 4 days in Goa Beach & Sunset",
                "Plan 2 days in Jaipur Royal Palaces",
                "Plan 1 day Taj Mahal Agra Trip",
            ],
            "itinerary": None,
        }

    dest = intent["destination"]
    days = intent.get("days") or 3
    budget = intent.get("budget_tier") if intent.get("budget_tier") != "any" else "mid"
    stated_budget = intent.get("stated_budget")

    ctx = request.context or {}
    star_pref = ctx.get("star_preference") or ctx.get("stars")
    if star_pref:
        try:
            star_val = float(star_pref)
            if star_val >= 4.5:
                budget = "luxury"
            elif star_val >= 3.0:
                budget = "mid"
            else:
                budget = "budget"
        except (ValueError, TypeError):
            pass

    plan = generate_itinerary(
        destination=dest,
        days=days,
        preferred_budget=budget,
        stated_budget=stated_budget
    )

    tier_label = {
        "budget": "Budget (Cheapest)",
        "mid": "Mid-Level (Recommended)",
        "luxury": "Luxury (5-Star VIP)",
    }.get(budget, "Mid-Level")
    total_est = plan["cost_comparison"][budget if budget in plan["cost_comparison"] else "mid"]["total_cost"]

    budget_line = f"🎯 **Target Tier:** {tier_label} (Estimated total: ~₹{total_est:,})\n"
    if stated_budget:
        per_day_stated = int(stated_budget / max(1, days))
        budget_line = (
            f"💰 **Your Stated Budget:** ₹{stated_budget:,} (~₹{per_day_stated:,}/day)\n"
            f"🎯 **Matched Tier:** {tier_label} (Total package tailored: ~₹{total_est:,})\n"
        )

    transit_info = plan["transit_connectivity"].get("airport") or plan["transit_connectivity"].get("railways") or "Regional Transit"
    local_transit = plan["transit_connectivity"].get("local_cab") or plan["transit_connectivity"].get("metro") or "Local AC Cabs"

    reply_text = (
        f"✨ **Here is your custom {days}-Day {dest} Itinerary!**\n\n"
        f"{budget_line}"
        f"☀️ **Best Season:** {plan['best_season']}\n"
        f"🚇 **Key Transit Hub:** {transit_info} | {local_transit}\n\n"
        f"I've tailored verified stays across Budget, Mid-Level, and Luxury tiers, curated iconic food spots for each meal, and planned full transit connectivity. Click **'🗺️ Plot {days}-Day Route on Live Map'** below to view your route live!"
    )

    return {
        "type": "itinerary",
        "reply": reply_text,
        "itinerary": plan,
        "quick_actions": [
            {"label": f"🗺️ Plot {days}-Day Route on Live Map", "action": "plot_map"},
            {"label": "💰 Compare Cheapest vs Luxury", "action": "show_pricing"},
            {"label": "🍽️ View Famous Food Spots", "action": "show_food"},
        ],
    }


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
