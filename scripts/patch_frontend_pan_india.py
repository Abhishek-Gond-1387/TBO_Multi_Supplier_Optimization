"""Retired utility: This retired migration script previously inserted synthetic Pan-India claims into the frontend. The active UI is Delhi-only."""

from __future__ import annotations

import sys


def main() -> int:
    print(__doc__)
    print("No synthetic data was generated.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
