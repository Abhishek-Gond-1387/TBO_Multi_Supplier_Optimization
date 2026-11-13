"""Environment-backed settings with safe development defaults."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


APP_NAME = os.getenv("APP_NAME", "TBO Multi-Supplier Inventory Engine")
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = env_bool("DEBUG", True)
HOST = os.getenv("HOST", "127.0.0.1")
PORT = env_int("PORT", 8000)
API_V1_PREFIX = os.getenv("API_V1_PREFIX", "/api/v1").rstrip("/")
USE_DATABASE = env_bool("USE_DATABASE", False)
USE_REDIS = env_bool("USE_REDIS", False)
ENABLE_CELERY = env_bool("ENABLE_CELERY", False)
ENABLE_SEMANTIC_MATCHING = env_bool("ENABLE_SEMANTIC_MATCHING", False)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5500,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
]
AUTO_MERGE_THRESHOLD = env_float("DEDUP_AUTO_MERGE_THRESHOLD", 0.88)
HUMAN_REVIEW_THRESHOLD = env_float("DEDUP_HUMAN_REVIEW_THRESHOLD", 0.65)
MAX_GEO_DISTANCE_METERS = env_float("DEDUP_MAX_GEO_DISTANCE_METERS", 250.0)
MAP_TILE_SERVER_URL = os.getenv(
    "MAP_TILE_SERVER_URL",
    "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
)
MAP_ATTRIBUTION = os.getenv(
    "MAP_ATTRIBUTION",
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
)
MAP_DEFAULT_LATITUDE = env_float("MAP_DEFAULT_LATITUDE", 22.9734)
MAP_DEFAULT_LONGITUDE = env_float("MAP_DEFAULT_LONGITUDE", 78.6569)
MAP_DEFAULT_ZOOM = env_int("MAP_DEFAULT_ZOOM", 4)
CACHE_TTL_LIVE_RATES = env_int("CACHE_TTL_LIVE_RATES", 300)
CACHE_TTL_GEO_VIEWPORT = env_int("CACHE_TTL_GEO_VIEWPORT", 1800)
