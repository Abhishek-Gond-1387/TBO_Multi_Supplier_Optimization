"""Rate-limited helpers for the public Nominatim geocoding service."""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import httpx

_request_lock = asyncio.Lock()
_last_request = 0.0


async def _nominatim_get(path: str, params: dict[str, Any]) -> Any:
    global _last_request
    base = os.getenv("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org").rstrip("/")
    async with _request_lock:
        wait = 1.0 - (time.monotonic() - _last_request)
        if wait > 0:
            await asyncio.sleep(wait)
        async with httpx.AsyncClient(timeout=12.0, headers={
            "User-Agent": os.getenv("NOMINATIM_USER_AGENT", "TBO-MultiSupplier-Platform/0.2 (local demo)")
        }) as client:
            response = await client.get(f"{base}{path}", params=params)
        _last_request = time.monotonic()
    response.raise_for_status()
    return response.json()


async def geocode_address(query: str) -> list[dict[str, Any]]:
    return await _nominatim_get("/search", {"q": query, "format": "jsonv2", "limit": 5, "addressdetails": 1})


async def reverse_geocode(latitude: float, longitude: float) -> dict[str, Any]:
    return await _nominatim_get("/reverse", {"lat": latitude, "lon": longitude, "format": "jsonv2", "addressdetails": 1})
