"""RETIRED module: The fabricated itinerary planner is retired and its API routes are not published. The product scope is hotel and sightseeing inventory quality."""

from __future__ import annotations


def __getattr__(name: str):
    raise RuntimeError(
        "This module is retired; use the Delhi OpenStreetMap inventory and current Hotels/Sightseeing APIs."
    )
