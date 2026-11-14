"""RETIRED module: The synthetic one-million-item generator is retired. The Delhi demo reads only the bundled OpenStreetMap snapshot in data/osm_inventory.json. No generated inventory, supplier quotes, or fake geographic coordinates are provided."""

from __future__ import annotations


def __getattr__(name: str):
    raise RuntimeError(
        "This module is retired; use the Delhi OpenStreetMap inventory and current Hotels/Sightseeing APIs."
    )
