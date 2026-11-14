# TBO Multi-Supplier Inventory Quality Pilot · Delhi

A runnable prototype for the Hotels and Sightseeing parts of TBO's multi-supplier inventory problem. The current demonstration is deliberately limited to a bundled, source-attributed OpenStreetMap snapshot for Delhi. It is not a live supplier-rate or customer-review product.

## What works in this pilot

- Delhi map and fast local search for the bundled OpenStreetMap records. The map uses free OpenFreeMap tiles and MapLibre GL; place data is from OpenStreetMap under ODbL.
- Hotel duplicate-candidate audit over the actual hotel rows in the snapshot. The spatial grid narrows candidate pairs; name, address (when supplied), and Haversine distance explain each score. The run is **analysis only**: it creates suggestions and a human-review queue, but does not merge or edit source records.
- Room-description normalization and sightseeing inclusion comparison (transfer, meal, access, duration, and cancellation text). These are algorithms exercised with operator input; they are not supplier data.
- Optional content enrichment by a source-linked Wikidata ID. Wikimedia Commons images are returned only when the file page exposes a reusable license; quality checks measure the actual image bytes. No stock-photo fallback is used.
- Local API documentation at `/docs`.

## Data limits (read before presenting the demo)

The bundled snapshot currently contains **159 hotel records and 90 visitor-place records** sourced from OpenStreetMap. These are map/source records, not partner supplier listings. The snapshot may be refreshed from the free public Overpass API, but results and availability depend on that service.

OpenStreetMap and Wikidata do not provide live hotel room prices, inventory availability, supplier cancellation/payment terms, hotel guest-review ratings, or booking reliability. The pilot displays those as unavailable and excludes them from ranking. To compare bookable options, TBO or supplier feeds with valid credentials, search dates, occupancy, and room/product terms are still required. Do not present the current sample as live rates, guest ratings, or completed canonical merges.

## Run on Windows

From the repository folder, run:

```powershell
.\run_demo.bat
```

On first run this creates `.venv`, installs the lightweight local-demo dependencies, starts the API and frontend, opens the map, and prints a short API walkthrough. Keep that terminal open. Press **Ctrl+C** there to stop the services.

Open these pages:

- Map: <http://127.0.0.1:5500/map_view.html>
- Match review and normalization tools: <http://127.0.0.1:5500/admin.html>
- API docs: <http://127.0.0.1:8000/docs>

The backend works with the bundled snapshot without Docker or a database. An internet connection is needed for the map tiles and optional Overpass refresh.

### Run the services manually

Terminal 1 (API):

```powershell
cd "$HOME\OneDrive\Desktop\TBO_Multi_Supplier_Optimization"
.\.venv\Scripts\python.exe -m uvicorn services.main:app --host 127.0.0.1 --port 8000
```

Terminal 2 (frontend):

```powershell
cd "$HOME\OneDrive\Desktop\TBO_Multi_Supplier_Optimization"
.\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

## Main API routes

- `GET /api/v1/data/status` — source and refresh status for the Delhi snapshot.
- `POST /api/v1/data/refresh` — request a rate-limited Overpass refresh.
- `GET /api/v1/inventory/search` — local search by text, destination, entity type, source category, and available fields.
- `GET /api/v1/inventory/{item_id}/supplier-comparison` — returns supplied offers if present; the OSM snapshot has none.
- `POST /api/v1/admin/dedup/batch-run` — scan current hotel source records and generate candidate suggestions. No records are merged.
- `GET /api/v1/review-queue` and `PUT /api/v1/review-queue/{id}` — inspect and decide candidate suggestions. The queue is in process memory and resets when the API restarts. A review decision does not write a canonical listing.
- `POST /api/v1/rooms/normalize` and `POST /api/v1/sightseeing/compare` — normalize operator-supplied descriptions.
- `POST /api/v1/enrichment/hotel/{item_id}` — normalize source fields and optionally query linked Wikidata/Commons records.

## Optional integrations

`requirements-optional.txt` contains packages for PostgreSQL/Redis/Celery and image quality assessment. The local demo does not require those services. Database persistence, production supplier adapters, real availability/rates, a canonical merge write-path, and customer review feeds are not connected in this prototype.

## Run checks locally

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
