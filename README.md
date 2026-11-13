# TBO Multi-Supplier Inventory Engine

A runnable local MVP for comparing hotel inventory from multiple suppliers. It includes a FastAPI service, sample Dubai inventory, viewport map, voice query parsing, deterministic duplicate matching, room and sightseeing normalization, and a PostgreSQL/PostGIS/pgvector plus Redis development stack.

## Start locally on Windows

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
docker compose up -d --build
uvicorn services.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, serve the map page:

```powershell
py -m http.server 5500 --directory frontend
```

Open `http://127.0.0.1:5500/map_view.html`. The API docs are at `http://127.0.0.1:8000/docs`.

The API reads sample records from `data/sample_inventory.json`, so the demo works without a database connection. The Compose stack provisions PostGIS and pgvector extensions, the initial relational schema, and Redis; database persistence and Redis caching are not wired into the MVP API yet. The human review queue is held in process memory and resets when the API restarts.

## Main API routes

- `GET /api/v1/inventory` — filter map items by viewport and destination.
- `GET /api/v1/inventory/search` — search by text, destination, entity type, price, and hotel rating; includes ranking factors and badges.
- `POST /api/v1/voice/query` — parse a voice transcript and return matching inventory.
- `POST /api/v1/matches/compare` — compare two hotel listings; borderline matches enter the in-memory review queue.
- `GET /api/v1/review-queue` and `PUT /api/v1/review-queue/{id}` — review a candidate match.
- `POST /api/v1/rooms/normalize` and `POST /api/v1/sightseeing/compare` — normalize supplier descriptions.

## Optional OSM sample

`py scripts/seed_datasets.py --city Dubai --limit 100` fetches a small public OpenStreetMap sample and writes `data/osm_inventory.json`. The script uses the public Overpass endpoint, so availability and response time depend on that service. The downloaded file is ignored by Git.

## Configuration and credentials

`.env.example` contains development defaults. `.env` is ignored by Git. Replace the example JWT and encryption values before adding authentication or storing supplier credentials, and use unique database credentials outside local development. The current MVP does not implement authentication or store supplier secrets.

Ranking uses configurable weights from `.env`; the supplied defaults total 1.0. Matching uses normalized name similarity and geographic distance, with thresholds configurable through `DEDUP_*` values. The voice parser is a local rules-based parser; transformer models listed in the environment guide are not downloaded or loaded by this MVP.
