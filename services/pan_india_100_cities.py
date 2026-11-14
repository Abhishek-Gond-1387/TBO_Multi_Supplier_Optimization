"""RETIRED module: Synthetic city and travel fixtures are retired. The active pilot is scoped to source-backed Delhi records."""

from __future__ import annotations


def __getattr__(name: str):
    raise RuntimeError(
        "This module is retired; use the Delhi OpenStreetMap inventory and current Hotels/Sightseeing APIs."
    )
