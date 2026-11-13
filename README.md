# TBO Multi-Supplier Inventory Optimization

[![Python checks](https://github.com/Abhishek-Gond-1387/TBO_Multi_Supplier_Optimization/actions/workflows/tests.yml/badge.svg)](https://github.com/Abhishek-Gond-1387/TBO_Multi_Supplier_Optimization/actions/workflows/tests.yml)

This repository is a runnable, India-first local discovery and operations demo based on the attached platform specification. It starts on India with Delhi, Mumbai, Goa, Jaipur, Agra, Bengaluru, Hyderabad and Kochi demo inventory; users can then switch to Dubai/UAE or all destinations. It covers supplier-feed validation, hotel matching, room normalization, sightseeing differences, supplier-rate selection, map search, voice queries, match review, metrics, optional PostgreSQL/PostGIS/pgvector, Redis caching, and a Celery worker.

All bundled hotel rates and supplier names are illustrative demo data, not live quotes. This repository does not connect to hotel suppliers or make bookings.

## Run the demo without Docker

Use Python 3.10 or later. In PowerShell, from the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
python -m uvicorn services.main:app --reload --host 127.0.0.1 --port 8000
```

In a second PowerShell window, from the same project directory:

```powershell
python -m http.server 5500 --directory frontend
```

Open the [discovery map](http://127.0.0.1:5500/map_view.html) or the [match review dashboard](http://127.0.0.1:5500/admin.html). API docs are at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). The sample JSON mode needs no database or Redis.

To run the repeatable API demo in another window:

```powershell
python scripts/demo.py
```

## Full local stack with Docker Desktop

After Docker Desktop is installed and running, copy `.env.example` to `.env`, then run:

```powershell
docker compose up --build
```

Compose starts PostgreSQL 16 with PostGIS and pgvector, Redis, the API, the Celery worker, and the static frontend. The API seeds the demo inventory into PostgreSQL on startup. Open `http://127.0.0.1:5500` and `http://127.0.0.1:8000/docs`.

The regular Python quickstart intentionally uses the bundled JSON catalog. To connect it to your own PostgreSQL service, set `USE_DATABASE=true` and `DATABASE_URL` in `.env`, apply the SQL files in `database/init/`, then run `python scripts/seed_demo_db.py`.

## Demo flow

1. Start with India, select a city such as Delhi, Mumbai, Jaipur or Goa, then filter hotels by text, star rating, currency, and budget.
2. Switch to Dubai/UAE or All destinations when ready. Hotel pins are clustered and show the lowest available rate in the selected currency.
3. Use the microphone button for browser speech search. The API returns a parsed query and a spoken reply.
4. On the operations page, choose **Create demo match**, inspect the name/address/distance features, then confirm or keep the two listings separate.
5. Try room normalization and sightseeing inclusion comparison in the API docs, or run `scripts/demo.py` for a terminal walkthrough.

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

No paid supplier, geocoding, routing, map tile, model-hosting, or dataset API is configured. India and Dubai hotel rates are synthetic demo rows; optional place imports use OpenStreetMap via Overpass (ODbL) and Wikidata (CC0), not a paid feed. See [OSM data licensing](https://www.openstreetmap.org/copyright) and [Wikidata licensing](https://www.wikidata.org/wiki/Wikidata:Licensing). Run `python scripts/seed_datasets.py --city Delhi --country-code IN --source both --limit 100` to fetch open place data when wanted. The app automatically includes `data/osm_inventory.json` after you create it. For Dubai, pass `--city Dubai --country-code AE`. The dataset script reads `OVERPASS_API_URL`, `WIKIDATA_API_URL`, and `WIKIDATA_SPARQL_URL` from `.env` so public endpoints can be changed without editing code.

The map uses the no-key OpenStreetMap standard tile service and displays its required attribution. OSM map data is open data, but the community tile servers are donation-funded, best-effort, and rate-limited; this app requests only tiles for the current interactive view. Do not bulk-download tiles. The public Nominatim helper is limited to one request per second per app process and is for user-initiated, moderate demo use; it must not be used for autocomplete or bulk geocoding. The public OSRM demo server is throttled to one request per second per app process, is best-effort, and is intended for reasonable non-commercial use. For higher traffic or commercial deployment, keep the code on these open formats but run your own OSM-derived tile, geocoding, and routing services; self-hosting can still have infrastructure costs. See the [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/), [Nominatim policy](https://operations.osmfoundation.org/policies/nominatim/), and [OSRM demo server policy](https://github.com/Project-OSRM/osrm-backend/wiki/Demo-server).

The default matching and voice-query parsing paths run locally using rules and lexical similarity. Optional MiniLM embeddings and BART zero-shot inclusion classification use locally downloaded open model weights, not a hosted inference API; install `requirements-ml.txt` and enable them with `ENABLE_SEMANTIC_MATCHING=true` or `ENABLE_ZERO_SHOT_INCLUSIONS=true`. Browser voice uses the browser's Web Speech API; server-side Whisper is optional and runs locally after installing `requirements-voice.txt` and downloading model weights.

## Configuration, storage, and safety

`.env.example` is the committed template. `.env` is ignored by Git. Replace its development database and secret values before using it outside a local demo. The JSON quickstart keeps the review queue and analytics counters in memory; they reset when the API restarts. PostgreSQL schema and seeding cover persistent inventory and supplier-rate data. External supplier credentials and production booking flows are not implemented.

## Tests

```powershell
python -m pytest -q
```
