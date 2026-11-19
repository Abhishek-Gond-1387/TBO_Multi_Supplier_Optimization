# TBO Multi-Supplier Inventory Optimization Platform

An intelligent inventory optimization and discovery engine that normalizes, deduplicates, and ranks multi-supplier travel data across accommodations, tours, transit, and dining.

---

## Table of Contents

- [Overview](#overview)
- [Key Engineering Modules](#key-engineering-modules)
  - [1. Hotel Geo-Spatial Deduplication](#1-hotel-geo-spatial-deduplication)
  - [2. Room Taxonomy Normalization](#2-room-taxonomy-normalization)
  - [3. Experience Inclusion Diff Engine](#3-experience-inclusion-diff-engine)
  - [4. Dynamic Supplier Ranking](#4-dynamic-supplier-ranking)
  - [5. AI Travel Concierge](#5-ai-travel-concierge)
- [Frontend Interfaces](#frontend-interfaces)
- [System Architecture](#system-architecture)
- [API Reference](#api-reference)
- [Local Setup & Execution](#local-setup--execution)
- [Verification & Automated Tests](#verification--automated-tests)

---

## Overview

Travel aggregators routinely source identical hotels and sightseeing activities from multiple supplier APIs (such as TBO, Hotelbeds, Agoda, Booking.com, and Viator). Because suppliers format names, coordinates, room descriptions, and inclusions differently, platforms face several challenges:

- **Duplicate Listings:** Redundant entries with slightly different titles or GPS coordinates clutter search results.
- **Fragmented Room Codes:** Inconsistent supplier abbreviations (e.g. `DLX KNG CT-VW BB` vs `DELUXE KING CITY VIEW WITH BREAKFAST`) make fair comparisons difficult for users.
- **Inclusion Ambiguity:** Two tours with identical titles may include completely different perks (such as private transport vs shared bus, or fast-track entry vs standard queues).
- **Scale and Latency:** Querying broad geographic regions across thousands of live items requires responsive filtering and minimal latency.

This platform provides dedicated micro-engines to normalize raw supplier feeds, eliminate duplicates, identify subtle inclusion differences, and present optimized results through high-performance web interfaces.

---

## Key Engineering Modules

### 1. Hotel Geo-Spatial Deduplication

Located in [`services/hotel_deduplication.py`](services/hotel_deduplication.py):
- **Hybrid Similarity Scoring:** Evaluates listing pairs using normalized Jaro-Winkler text distance, token set overlap, and spatial Haversine distance.
- **Geo-Fencing:** Flags pairs exceeding 250 meters as distinct properties, preventing accidental merges of similarly named chain hotels in different neighborhoods.
- **Confidence Tiers:**
  - `Score >= 0.88`: Auto-merge candidate.
  - `0.65 <= Score < 0.88`: Routes to the Human-in-the-Loop review queue.
  - `Score < 0.65`: Treated as independent properties.

### 2. Room Taxonomy Normalization

Located in [`services/room_normalizer.py`](services/room_normalizer.py):
- Parses unstructured, abbreviated supplier room strings into standardized JSON attributes:
  - **Room Class:** Standard, Deluxe, Executive, Suite, Villa.
  - **Bed Configuration:** King, Queen, Twin, Double.
  - **View Type:** City View, Sea/Ocean View, Garden View, Courtyard.
  - **Meal Plan:** Room Only (RO), Bed & Breakfast (BB), Half Board (HB), Full Board (FB).
  - **Amenities:** Balcony, Club Lounge Access, Private Pool.

### 3. Experience Inclusion Diff Engine

Located in [`services/sightseeing_difference_engine.py`](services/sightseeing_difference_engine.py):
- Analyzes titles and descriptions of competing tour offers to compute clear inclusion vectors:
  - **Transfers:** None, Shared Coach, Private Chauffeur.
  - **Meals:** None, Breakfast, Lunch, Gourmet Dinner.
  - **Access Level:** General Admission, Skip-the-Line, VIP Access.
  - **Cancellation:** Free 24h, Free 48h, Non-Refundable.

### 4. Dynamic Supplier Ranking

Located in [`services/dynamic_ranking_engine.py`](services/dynamic_ranking_engine.py):
- Multi-factor scoring that balances:
  $$\text{Final Score} = w_1 \cdot \text{Price} + w_2 \cdot \text{Reliability} + w_3 \cdot \text{Quality} + w_4 \cdot \text{Flexibility} + w_5 \cdot \text{Relevance}$$
- Automatically highlights the cheapest supplier with rate parity indicators.

### 5. AI Travel Concierge

Located in [`services/ai_trip_planner.py`](services/ai_trip_planner.py):
- Generates day-by-day travel itineraries based on destination, duration, and pace.
- Provides 3-tier budget estimates (Budget, Midscale, Luxury) and plots sequential waypoints on the discovery map.

---

## Frontend Interfaces

The project provides three tailored web views:

1. **Discovery Map (`/map_view.html`):**
   - Interactive MapLibre GL exploration with clustered price pins.
   - 560px responsive left sidebar displaying verified photos, supplier rate comparisons, and live filters.
   - Built-in Web Speech API voice search and AI trip planner drawer.

2. **Landing Page (`/index.html`):**
   - High-performance kinetic presentation utilizing GSAP and Lenis smooth scrolling.
   - Highlights core platform features and destination showcases.

3. **Operations Review Hub (`/admin.html`):**
   - Dedicated portal for operational teams to inspect borderline duplicate listings.
   - Interactive testing tools for room code normalization and tour inclusion diffing.

---

## System Architecture

```
Supplier Ingestion Streams
  ├── TBO Preferred Feeds
  ├── Third-Party Bedbanks (Agoda, Hotelbeds, Booking.com)
  └── Experience Providers (Viator, Headout)
           │
           ▼
Ingestion & Normalization Layer
  ├── Ingestion Schema Validation
  ├── Room Taxonomy Standardizer
  └── Image Quality Assessor
           │
           ▼
Optimization Engines
  ├── Hybrid Geo-Spatial Deduplicator (<250m Haversine + Jaro-Winkler)
  ├── Tour Inclusion Diff Engine
  └── Multi-Factor Dynamic Ranking
           │
           ▼
Storage & Access Layer
  ├── Two-Tier Cache (In-Memory + Optional Redis)
  ├── Catalog Storage (SQLite / PostgreSQL)
  └── Operational Review Queue
           │
           ▼
Web Endpoints & APIs
  ├── FastAPI Application (/api/v1/*)
  ├── Discovery Map Interface (/map_view.html)
  ├── Landing Page (/index.html)
  └── Operations Hub (/admin.html)
```

---

## API Reference

The backend exposes RESTful endpoints under `/api/v1`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/search` | Search inventory across hotels, tours, transit, and dining with multi-supplier rates. |
| `GET` | `/api/v1/suggestions` | Fast autocomplete suggestions with category tagging. |
| `POST` | `/api/v1/hotels/deduplicate` | Compare two hotel records for similarity score and merge recommendation. |
| `POST` | `/api/v1/tours/diff` | Differentiate inclusion perks between two tour offerings. |
| `POST` | `/api/v1/ai/itinerary` | Generate day-by-day itinerary and multi-tier budget estimates. |
| `GET` | `/api/v1/review-queue` | List pending borderline duplicate matches requiring review. |
| `PUT` | `/api/v1/review-queue/{id}` | Approve or reject a candidate listing match. |
| `GET` | `/api/v1/analytics/summary` | Retrieve search volume, CTR, and conversion metrics. |
| `GET` | `/api/v1/health` | Service and dependency health status. |

---

## Local Setup & Execution

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Windows PowerShell, macOS Terminal, or Linux Shell

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Abhishek-Gond-1387/TBO_Multi_Supplier_Optimization.git
   cd TBO_Multi_Supplier_Optimization
   ```

2. **Set up a virtual environment:**
   ```powershell
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application:**
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn services.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   *(Or double-click `run_demo.bat` on Windows)*

5. **Access in browser:**
   - Landing Page: `http://127.0.0.1:8000/index.html`
   - Discovery Map: `http://127.0.0.1:8000/map_view.html`
   - Operations Hub: `http://127.0.0.1:8000/admin.html`
   - API Docs: `http://127.0.0.1:8000/docs`

---

## Verification & Automated Tests

Run the full pytest suite:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Audit the 1,000,000+ catalog and measure query latency:
```powershell
.\.venv\Scripts\python.exe scripts/verify_1m_inventory.py
```

Run the interactive terminal walkthrough:
```powershell
.\.venv\Scripts\python.exe scripts/demo.py
```

---

## License

This project is licensed under the [MIT License](LICENSE).
