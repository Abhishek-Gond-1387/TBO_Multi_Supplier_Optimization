# TBO Multi-Supplier Inventory Optimization Platform

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MapLibre GL](https://img.shields.io/badge/MapLibre_GL-4.7+-1E293B?style=for-the-badge&logo=maplibre&logoColor=white)](https://maplibre.org/)
[![Tests](https://img.shields.io/badge/Tests-Passing%20(24%2F24)-10B981?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge)](LICENSE)

<br/>

**An enterprise-grade inventory intelligence engine that automates cross-supplier deduplication, standardizes cryptic room codes, resolves tour inclusion differences, and provides real-time rate parity across 1,240,000+ travel items.**

[Explore Map Interface](http://127.0.0.1:8000/map_view.html) • [View Landing Experience](http://127.0.0.1:8000/index.html) • [Operations Portal](http://127.0.0.1:8000/admin.html) • [API Documentation](http://127.0.0.1:8000/docs)

</div>

---

## 📋 Executive Overview

In the global B2B travel distribution ecosystem, inventory is ingested from fragmented bedbanks and activity aggregators (e.g., TBO Preferred, Hotelbeds, Agoda, Booking.com, Viator, Headout). Each supplier formats product names, geolocation coordinates, room codes, and tour perks differently.

This heterogeneity leads to substantial business inefficiencies:
- **Redundant Listings:** The same hotel appears multiple times due to minor spelling variances, alternate addresses, or coordinates drifting up to 200 meters.
- **Cryptic Room Descriptions:** Fragmented supplier codes (`DLX KNG CT-VW BB BALC` vs. `EXECUTIVE SUITE KING BED WITH BREAKFAST`) prevent consumers and travel agents from comparing true equivalents.
- **Inclusion Opacity:** Identically named excursions vary drastically in deliverable value (e.g., *Shared Coach* vs. *Private Chauffeur*, *Standard Entry* vs. *VIP Fast-Track Access*).
- **Rate Parity Blindspots:** Without instant normalization, platforms fail to showcase the lowest net price or most reliable fulfillment partner.

**TBO Multi-Supplier Optimization Engine** resolves these issues through deterministic spatial deduplication, rule-based taxonomy parsers, automated inclusion diffing, and sub-50ms vector query execution across 110 Indian destinations and international hubs.

---

## 🏗️ System Architecture & Data Pipeline

The platform uses a layered micro-service architecture designed for asynchronous ingestion, low-latency in-memory ranking, and responsive spatial mapping:

```
+---------------------------------------------------------------------------------------+
|                                HETEROGENEOUS INGESTION                                |
|  [TBO Preferred]   [Hotelbeds / WebBeds]   [Agoda / Booking.com]   [Viator / Headout] |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                              NORMALIZATION & VALIDATION                               |
|  * Pydantic Schema Validation                   * Text Normalization & Slugification   |
|  * Image Quality Scoring (Laplacian Variance)   * Room Shorthand Parser                |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                                  CORE ENGINE LAYER                                    |
|                                                                                       |
|  [Geo-Spatial Deduplicator]       [Room Taxonomizer]        [Inclusion Diff Engine]  |
|  - Jaro-Winkler (>0.88 auto)      - Class & Bed Type        - Transfers Breakdown     |
|  - Haversine (<250m bound)        - View & Meal Standard    - Meal Tier Analysis      |
|  - Address Token Overlap          - Feature Extraction      - VIP / Fast-Track Perks  |
|                                                                                       |
|  [Dynamic Ranking Engine]                                   [AI Travel Concierge]     |
|  - Rate Parity & Spread Scoring                             - Multi-Tier Budgets      |
|  - Supplier Reliability Weighting                           - Day-by-Day Routing      |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                               DATA ACCESS & CLIENT APIS                               |
|  * SQLite / PostgreSQL Data Tier                * Two-Tier Memory & Redis Cache       |
|  * Human-in-the-Loop Review Queue               * Prometheus Real-Time Metrics        |
|                                                                                       |
|  [Spatial Discovery Map]          [Kinetic Landing]         [Operations Review Hub]   |
|  (/map_view.html)                 (/index.html)             (/admin.html)             |
+---------------------------------------------------------------------------------------+
```

---

## ⚙️ Core Technical Modules

### 1. Hybrid Spatial Deduplication Engine
**File:** [`services/hotel_deduplication.py`](services/hotel_deduplication.py)

Evaluates prospective duplicate pairs across independent signals:
1. **Name Similarity ($S_{\text{name}}$):** Cleaned, case-folded Jaro-Winkler metric with prefix bonuses.
2. **Address Similarity ($S_{\text{addr}}$):** Set-token intersection over union (IoU) across postal tokens.
3. **Spatial Distance ($D_{\text{geo}}$):** Great-circle Haversine distance in meters:
   $$D = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)$$
4. **Hard Distance Boundary:** If $D_{\text{geo}} > 250\text{ m}$, similarity score is capped at zero, preventing erroneous merges of airport branches or chain outlets.

**Decision Matrix:**
| Composite Score | Action | Automated Workflow |
| :--- | :--- | :--- |
| **$\ge 0.88$** | **AUTO-MERGE** | Consolidates into single canonical ID; lowest supplier rate featured. |
| **$0.65 - 0.87$** | **REVIEW QUEUE** | Dispatched to operator review hub for human confirmation. |
| **$< 0.65$** | **KEEP SEPARATE** | Registered as independent inventory entities. |

---

### 2. Standardized Room Taxonomy Parser
**File:** [`services/room_normalizer.py`](services/room_normalizer.py)

Ingests fragmented, supplier-specific room names and outputs standardized taxonomy objects:

```json
// Input (Raw Supplier Payload)
{ "raw_room_name": "DLX KNG STE OCN-VW BRKFST BALC NON-REF" }

// Output (Normalized Taxonomy)
{
  "normalized_title": "Deluxe King Suite Ocean View",
  "room_class": "Suite",
  "tier": "Deluxe",
  "bed_type": "King",
  "view_type": "Ocean View",
  "meal_plan": "Bed & Breakfast",
  "has_balcony": true,
  "is_flexible": false,
  "confidence": 0.98
}
```

---

### 3. Experience Inclusion Difference Engine
**File:** [`services/sightseeing_difference_engine.py`](services/sightseeing_difference_engine.py)

When consumers compare two tours with matching titles, the inclusion engine compares the underlying deliverable components:

| Feature Dimension | Supplier A (e.g., Viator) | Supplier B (e.g., GetYourGuide) | Diff Detected |
| :--- | :--- | :--- | :---: |
| **Transfer Type** | Shared AC Coach | Private Luxury Chauffeur | ⚠️ **Meaningful Diff** |
| **Meal Plan** | None Included | 3-Course Buffet Lunch | ⚠️ **Meaningful Diff** |
| **Monument Access** | Standard General Admission | Skip-the-Line Fast Track | ⚠️ **Meaningful Diff** |
| **Cancellation** | Free cancellation up to 24h | Non-refundable | ⚠️ **Meaningful Diff** |
| **Duration** | 4 Hours (Half Day) | 4 Hours (Half Day) | Identical |

---

### 4. Dynamic Multi-Factor Ranking Engine
**File:** [`services/dynamic_ranking_engine.py`](services/dynamic_ranking_engine.py)

Sorts search results dynamically based on a composite utility score:
$$\text{Score} = w_r \cdot S_{\text{relevance}} + w_p \cdot S_{\text{price}} + w_s \cdot S_{\text{reliability}} + w_q \cdot S_{\text{quality}} + w_f \cdot S_{\text{flexibility}}$$

- **Rate Parity Matrix:** Automatically surfaces the lowest verified net rate among TBO Preferred, Agoda, Hotelbeds, Booking.com, and Viator.
- **Circuit Breaker Integration:** If a supplier's API fails or exceeds 800ms latency, the engine gracefully downgrades its ranking weight without halting search execution.

---

## 🖥️ User Experience & Frontend Suite

The platform includes three distinct web clients designed for consumers, travel agents, and operations specialists:

```
+---------------------------------------------------------------------------------------+
| 1. Google Maps-Grade Spatial Discovery (/map_view.html)                               |
| - High-performance MapLibre GL map viewport with live clustering.                     |
| - 560px spacious sidebar with verified photography, amenities, and rate comparisons. |
| - Anti-collision price pills rendered with 60px minimum screen-space distance.         |
| - Web Speech API voice search integration and interactive filter drawer.              |
+---------------------------------------------------------------------------------------+
| 2. Modern Animated Landing Showcase (/index.html)                                     |
| - GSAP 3 & Lenis smooth scroll engine for fluid responsive typography.                |
| - Floating hero parallax layers, interactive destination counters, and feature cards. |
+---------------------------------------------------------------------------------------+
| 3. Operations & Review Portal (/admin.html)                                           |
| - Split-screen inspection interface for borderline duplicate pairs.                   |
| - One-click operator actions: Approve Canonical Link or Reject Match.                 |
| - Real-time inclusion diff playground and room code normalizer sandbox.               |
+---------------------------------------------------------------------------------------+
```

---

## 📡 REST API Reference

Base URL: `http://127.0.0.1:8000/api/v1`

### 1. Inventory Search
```http
GET /api/v1/search?destination=Delhi&entity_type=HOTEL&sort_by=price_asc
```
Returns deduplicated listings, rate parity comparisons, and lowest supplier offers.

### 2. Prefix Autocomplete
```http
GET /api/v1/suggestions?q=Taj
```
Returns matching properties, cities, and landmarks with category badges and thumbnail links.

### 3. Hotel Pair Deduplication Check
```http
POST /api/v1/hotels/deduplicate
Content-Type: application/json

{
  "hotel_a": { "name": "The Taj Mahal Hotel", "latitude": 28.6052, "longitude": 77.2255 },
  "hotel_b": { "name": "Taj Mahal Hotel New Delhi", "latitude": 28.6054, "longitude": 77.2251 }
}
```

### 4. Tour Inclusions Comparison
```http
POST /api/v1/tours/diff
Content-Type: application/json

{
  "left_title": "Taj Mahal & Agra Fort Tour with Private Car",
  "right_title": "Taj Mahal Agra Fort Tour Standard Coach"
}
```

### 5. Automated AI Itinerary Generator
```http
POST /api/v1/ai/itinerary
Content-Type: application/json

{
  "destination": "Goa",
  "duration_days": 3,
  "pace": "moderate"
}
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- PowerShell 5.1+ (Windows) or Bash (macOS/Linux)

### 1. Clone & Enter Repository
```powershell
Set-Location "$HOME\OneDrive\Desktop\TBO_Multi_Supplier_Optimization"
```

### 2. Verify Environment & Dependencies
```powershell
# Create virtual environment if not present
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### 3. Launch the Backend Server
```powershell
.\.venv\Scripts\python.exe -m uvicorn services.main:app --host 127.0.0.1 --port 8000 --reload
```
*(Alternatively, execute `.\run_demo.bat` for one-click startup on Windows)*

### 4. Access Interfaces in Browser
- **Discovery Map:** [http://127.0.0.1:8000/map_view.html](http://127.0.0.1:8000/map_view.html)
- **Landing Page:** [http://127.0.0.1:8000/index.html](http://127.0.0.1:8000/index.html)
- **Operations Hub:** [http://127.0.0.1:8000/admin.html](http://127.0.0.1:8000/admin.html)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Testing & Verification

Run the complete automated test suite (24 unit and API integration tests):
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Audit catalog volume, multi-supplier coverage, and response latency:
```powershell
.\.venv\Scripts\python.exe scripts/verify_1m_inventory.py
```

Run the interactive terminal walkthrough:
```powershell
.\.venv\Scripts\python.exe scripts/demo.py
```

---

## 🔒 Security & Operational Resilience

- **Circuit Breakers:** Configured with a failure threshold of 5 attempts and a 30-second recovery window to protect against downstream provider timeouts.
- **Supplier API Isolation:** Strict 800ms per-request timeouts prevent slow supplier feeds from degrading overall client response times.
- **Zero Paid Cloud Dependencies:** Designed to operate self-contained with OpenStreetMap vector tiles, local SQLite storage, and open-source models.
- **Token Security:** Production-ready JWT access tokens (HMAC-SHA256) and AES-256 symmetric encryption for stored supplier credentials.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
