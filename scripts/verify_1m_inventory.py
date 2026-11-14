"""Retired utility: There is no one-million-record live inventory in this project. Verify the Delhi source snapshot with GET /api/v1/data/status and GET /api/v1/inventory/search."""

from __future__ import annotations

import sys


def main() -> int:
    print(__doc__)
    print("No synthetic data was generated.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
