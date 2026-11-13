# TBO Multi-Supplier Inventory Optimization

[![Python checks](https://github.com/Abhishek-Gond-1387/TBO_Multi_Supplier_Optimization/actions/workflows/tests.yml/badge.svg)](https://github.com/Abhishek-Gond-1387/TBO_Multi_Supplier_Optimization/actions/workflows/tests.yml)

This release is a Delhi-only pilot for the multi-supplier inventory objective. It searches up to 500 named free OpenStreetMap records across hotels, attractions, food, culture, parks, recreation, and shopping, and ranks them for discovery. It also provides hotel matching, room normalization, sightseeing inclusion comparison, voice search, match review, metrics, optional PostgreSQL/PostGIS/pgvector, Redis caching, and Celery components.

OpenStreetMap does not provide customer review scores, bookable room rates, current availability, cancellation terms, or supplier reliability. Its occasional `stars` tag is a mapped property classification, not a live customer rating. Live supplier comparison and booking conversion ranking require authorized supplier feeds, which this pilot does not connect to. Until the Delhi open-data refresh succeeds, bundled Delhi rows may appear as an explicitly labelled illustrative fallback.

## Run the demo without Docker

Use Python 3.10 or later. On Windows, open the repository folder and run `run_demo.bat` (or double-click it). The launcher creates `.venv` if needed, installs `requirements.txt` when core packages are missing, creates a local `.env` from the example if needed, starts the API and frontend, checks both are responding, opens the Delhi map, and prints a short open-data walkthrough. The API refreshes the Delhi snapshot in the background when no recent snapshot exists. Keep the launcher window open while presenting; press **Ctrl+C** in it to stop the services it started. Startup logs are saved under `.demo-logs/` and are ignored by Git.

You can also launch it from PowerShell:

```powershell
Set-Location "$HOME\OneDrive\Desktop\TBO_Multi_Supplier_Optimization"
.\run_demo.bat
```

Open the [discovery map](http://127.0.0.1:5500/map_view.html), [match review dashboard](http://127.0.0.1:5500/admin.html), or [API docs](http://127.0.0.1:8000/docs). The quickstart forces the self-contained JSON sample mode and does not need Docker, PostgreSQL, or Redis. If either port is already used by another app, the launcher reports which port and where to inspect the logs.

For manual startup, use one terminal for `python -m uvicorn services.main:app --host 127.0.0.1 --port 8000` and a second for `python -m http.server 5500 --bind 127.0.0.1 --directory frontend`, both from the repository directory. Run `python scripts/demo.py` for the terminal walkthrough after the API has started.

## Full local stack with Docker Desktop

After Docker Desktop is installed and running, copy `.env.example` to `.env`, then run:

```powershell
docker compose up --build
```

Compose starts PostgreSQL 16 with PostGIS and pgvector, Redis, the API, the Celery worker, and the static frontend. The API seeds the demo inventory into PostgreSQL on startup. Open `http://127.0.0.1:5500` and `http://127.0.0.1:8000/docs`.

The regular Python quickstart intentionally uses the bundled JSON catalog. To connect it to your own PostgreSQL service, set `USE_DATABASE=true` and `DATABASE_URL` in `.env`, apply the SQL files in `database/init/`, then run `python scripts/seed_demo_db.py`.

## Demo flow

1. The map opens at Delhi and reads the cached OpenStreetMap snapshot; use **Refresh** to request a new snapshot. Refreshes are limited to one per hour to respect the public endpoint.
2. Search hotel and experience place records by name, area, or amenity. Map search filters the already-loaded results locally as you zoom or pan.
3. The data timestamp and record counts appear above the results. Open place records have no live booking price or availability.
4. Use the microphone button for browser speech search. The current map pilot is limited to Delhi.
5. Try room normalization and sightseeing inclusion comparison in the API docs. These logic examples are not live supplier offers.

## API surface

- `GET /api/v1/inventory` and `POST /api/v1/map/viewport-inventory` — bounding-box inventory for the map.
- `GET /api/v1/inventory/search` — destination, text, star, budget, landmark, and inclusion filters with supplier selection and ranking explanation.
- `POST /api/v1/voice/query` — parse a voice transcript and return ranked results.
- `POST /api/v1/matches/compare` — explain a hotel-pair match and queue borderline pairs for review.
- `GET /api/v1/admin/matches/review-queue`, `PUT /api/v1/review-queue/{id}`, and `POST /api/v1/admin/matches/resolve` — human review actions and audit trace.
- `GET /api/v1/inventory/{id}/explain` — item ranking and selected-supplier explanation.
- `POST /api/v1/ingest/hotels/validate` — validate and score a supplier hotel payload; `/queue` submits it to Celery when enabled.
- `POST /api/v1/rooms/normalize` and `POST /api/v1/sightseeing/compare` — room taxonomy and offer-inclusion differences.
- `GET /api/v1/routes/summary`, `/api/v1/geocode/search`, and `/api/v1/geocode/reverse` — open routing and geocoding helpers.
- `POST /api/v1/telemetry/events`, `GET /api/v1/analytics/summary`, and `GET /metrics` — demo conversion counters and Prometheus metrics.

## Public sample data and optional models

The Delhi place snapshot comes from the public OpenStreetMap Overpass API and is stored locally at `data/osm_inventory.json` (ignored by Git). OSM is openly licensed under ODbL; attribution is shown on the map. This public data is community-maintained and can be incomplete or stale. The API caches up to 500 named Delhi visitor places and automatically refreshes the snapshot no more often than every six hours; the UI refresh action is limited to once per hour. Follow the [Overpass public service guidance](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html). The free source provides place names, coordinates, and some mapped tags, not live hotel prices, availability, or user ratings. No paid supplier, geocoding, routing, map tile, hosted model, or dataset API is configured.

The map uses [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/) with the [OpenFreeMap Liberty vector style](https://openfreemap.org/quick_start/), which requires no API key and gives smooth, continuous zoom with map labels and clustered inventory pins. OpenFreeMap uses OpenStreetMap-derived data; attribution is shown on the map. Its public service is free and provided as-is, without an availability SLA. The public Nominatim helper is limited to one request per second per app process and is for user-initiated, moderate demo use; it must not be used for autocomplete or bulk geocoding. The public OSRM demo server is throttled to one request per second per app process, is best-effort, and is intended for reasonable non-commercial use. For higher traffic or commercial deployment, run your own open-data style, geocoding, and routing services; self-hosting can still have infrastructure costs. See the [Nominatim policy](https://operations.osmfoundation.org/policies/nominatim/) and [OSRM demo server policy](https://github.com/Project-OSRM/osrm-backend/wiki/Demo-server).

The default matching and voice-query parsing paths run locally using rules and lexical similarity. Optional MiniLM embeddings and BART zero-shot inclusion classification use locally downloaded open model weights, not a hosted inference API; install `requirements-ml.txt` and enable them with `ENABLE_SEMANTIC_MATCHING=true` or `ENABLE_ZERO_SHOT_INCLUSIONS=true`. Browser voice uses the browser's Web Speech API; server-side Whisper is optional and runs locally after installing `requirements-voice.txt` and downloading model weights.

## Configuration, storage, and safety

`.env.example` is the committed template. `.env` is ignored by Git. Replace its development database and secret values before using it outside a local demo. The JSON quickstart keeps the review queue and analytics counters in memory; they reset when the API restarts. PostgreSQL schema and seeding cover persistent inventory and supplier-rate data. External supplier credentials and production booking flows are not implemented.

## Tests

```powershell
python -m pytest -q
```
