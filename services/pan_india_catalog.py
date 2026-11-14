"""RETIRED module: Pan-India, dining, and transit fixture catalogs are retired and are not part of the Hotels and Sightseeing pilot."""

from __future__ import annotations


def __getattr__(name: str):
    raise RuntimeError(
        "This module is retired; use the Delhi OpenStreetMap inventory and current Hotels/Sightseeing APIs."
    )
