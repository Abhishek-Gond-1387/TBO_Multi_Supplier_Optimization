# TBO Multi-Supplier Inventory Optimization & Discovery Platform

<div align="center">

[![Python checks](https://github.com/Abhishek-Gond-1387/TBO_Multi_Supplier_Optimization/actions/workflows/tests.yml/badge.svg)](https://github.com/Abhishek-Gond-1387/TBO_Multi_Supplier_Optimization/actions/workflows/tests.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![MapLibre GL](https://img.shields.io/badge/MapLibre_GL-4.7+-blue.svg?style=flat&logo=maplibre&logoColor=white)](https://maplibre.org)
[![GSAP 3](https://img.shields.io/badge/Animations-GSAP_3_&_Lenis-88CE02.svg?style=flat&logo=greensock&logoColor=white)](https://greensock.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Enterprise-Grade Real-Time Multi-Supplier Rate Parity, Spatial Geo-Deduplication, Cryptic Taxonomy Normalization & Pan-India Travel Discovery Engine**

[Live Map View](http://127.0.0.1:8000/map_view.html) • [Interactive Landing Page](http://127.0.0.1:8000/index.html) • [Operations Review Hub](http://127.0.0.1:8000/admin.html) • [Swagger API Docs](http://127.0.0.1:8000/docs)

</div>

---

## 📌 Executive Summary

Modern travel aggregation platforms integrate inventory across heterogeneous global and domestic bedbanks (TBO Preferred, Hotelbeds, Agoda, Booking.com, Expedia, Viator, Headout, Klook). However, fragmented supplier APIs introduce four critical operational bottlenecks:

1. **Duplicate Supplier Listings:** Redundant listings with minor spelling deviations, slightly displaced GPS coordinates, and alternate address strings inflate catalog clutter.
2. **Cryptic Room Type Incoherence:** Unstandardized supplier codes (e.g., `DLX KNG CT-VW BB BALC` vs. `EXEC STE 1KNG CLB LVL`) prevent meaningful side-by-side room comparison.
3. **Opaque Tour & Activity Inclusions:** Identically titled sightseeing tours vary drastically in inclusions (e.g., *Shared Coach* vs. *Private Luxury Chauffeur*, *General Admission* vs. *VIP Fast-Track Access*, *Buffet Lunch* vs. *No Meals*).
4. **Latency & Catalog Scale:** Consumers expect sub-50ms search latency across millions of accommodations, experiences, dining options, and transit junctions.

**TBO Multi-Supplier Inventory Optimization Platform** solves these challenges using a high-throughput Python backend, hybrid spatial deduplication algorithms, an intelligent rule-based room taxonomizer, an inclusion diffing engine, and an interactive Google Maps-grade spatial exploration frontend with smooth kinetic animations.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Data Sources ["Heterogeneous Supplier Streams"]
        S1["TBO Preferred Inventory"]
        S2["Hotelbeds / WebBeds"]
        S3["Agoda / Booking.com"]
        S4["Viator / Headout / Klook"]
        S5["OpenStreetMap / Transit Hubs"]
    end

    subgraph Ingestion ["Ingestion & Normalization Layer"]
        IV["Ingestion Schema Validator"]
        RN["Room Taxonomy Normalizer<br/>(Class, Bed, View, Meal, Balcony)"]
        IQ["Laplacian Blur & Content Intelligence"]
    end

    subgraph Core Engines ["Optimization & Processing Engines"]
        DEDUP["Hybrid Geo-Spatial Deduplicator<br/>(Jaro-Winkler + Haversine &lt;250m + pHash)"]
        DIFF["Nuanced Tour Inclusion Diff Engine<br/>(Transfers, Meals, Access, Cancellation)"]
        RANK["Dynamic Multi-Factor Ranking Engine<br/>(Parity, Reliability, Conversion, Quality)"]
        PLANNER["Personal AI Travel Concierge<br/>(Multi-Tier Budget Allocation & Routes)"]
    end

    subgraph Storage ["Scalable Storage & Caching"]
        CACHE["Two-Tier Distributed Cache<br/>(Memory + Redis Fallback)"]
        DB["Pan-India Catalog Database<br/>(1,240,000+ Reachable Records)"]
        REV["Human-in-the-Loop Review Queue"]
    end

    subgraph Frontend ["Multi-Experience Frontend Suite"]
        LANDING["Kinetic Landing Experience<br/>(GSAP 3, Lenis Smooth Scroll)"]
        MAP["Google Maps-Grade Spatial Discovery<br/>(MapLibre GL, Anti-Collision Price Pills)"]
        ADMIN["Operations & Matching Hub<br/>(Split-Screen Review & Live Diffing)"]
    end

    Data Sources --> IV
    IV --> RN & IQ
    RN & IQ --> DEDUP & DIFF
    DEDUP --> REV
    DEDUP & DIFF --> RANK & PLANNER
    RANK & PLANNER --> CACHE & DB
    CACHE & DB --> LANDING & MAP & ADMIN
```

---

## 🌟 Core Technical Capabilities

### 1. Hybrid Hotel Deduplication & Clustering
- **Multi-Signal Similarity:** Combines weighted Jaro-Winkler string distance on normalized names, token sort ratio on address strings, and spatial Haversine distance thresholded at `<250 meters`.
- **Perceptual Image Hashing (pHash):** Evaluates listing photography to match duplicate properties even when supplier names deviate substantially.
- **Laplacian Blur Quality Scoring:** Discards low-resolution or blurred supplier photography based on Laplacian operator variance ($\sigma^2 < 80.0$).
- **Human-in-the-Loop Queue:** Borderline similarity matches ($0.65 \le \text{score} < 0.88$) automatically feed into an operations review dashboard for single-click operator approval or separation.

### 2. Standardized Room Taxonomy Normalizer
Converts cryptic, supplier-specific room shorthand into structured, queryable attributes:
```json
{
  "raw_code": "EXEC STE 1KNG CT-VW BB BALC",
  "normalized": {
    "room_class": "Executive Suite",
    "bed_type": "King",
    "view_type": "City View",
    "meal_plan": "Bed & Breakfast",
    "has_balcony": true,
    "confidence_score": 0.96
  }
}
```

### 3. Nuanced Tour Inclusion Differentiation Engine
Sightseeing and activities across Viator, GetYourGuide, and Headout often share similar titles but differ drastically in value. Our diff engine computes exact inclusion vectors across:
- **Transfers:** `None` vs. `Shared AC Coach` vs. `Private Luxury Chauffeur`
- **Meals:** `None` vs. `Continental Breakfast` vs. `Buffet Lunch` vs. `Gourmet 3-Course Dinner`
- **Access Level:** `Standard General Admission` vs. `Skip-The-Line Fast Track` vs. `VIP Lounge Access / Level 148`
- **Duration:** `1-2 Hours Express` vs. `Half-Day (4h)` vs. `Full-Day (8h)`
- **Cancellation:** `Free 24h Prior` vs. `Free 48h Prior` vs. `Non-Refundable`

### 4. Pan-India 1,240,000+ Reachable Live Inventory
Covers **110 Indian Cities, Heritage Regions, and Transit Corridors**, alongside major international hubs (Dubai, Abu Dhabi, Santorini, Athens):
- 🏨 **520,000+ Stays:** 5-Star Luxury Palaces, Heritage Havelis, Boutique Business, and Budget Stays.
- 🎡 **334,000+ Sightseeing & Tours:** Fast-Track Monument Entry, Guided Safaris, Cultural Trails.
- 🚆 **210,000+ Transit Hubs:** Vande Bharat Express corridors, Metro stations, and Airport Junctions.
- 🍽️ **173,000+ Iconic Dining Spots:** Heritage Royal Dining, Street Food Trails, and Coastal Kitchens.

### 5. Multi-Experience Frontend Suite
- **Interactive Landing Page (`/index.html`):** Built with **GSAP 3**, **ScrollTrigger**, and **Lenis smooth scrolling** for fluid typography, floating parallax layers, and micro-interactions.
- **Spatial Discovery Map (`/map_view.html`):** 560px wide Airbnb/OYO-style sidebar with infinite scroll, 60px screen-space anti-collision price pills, real-time autocomplete suggestions, and Web Speech API voice search.
- **Operations & Review Hub (`/admin.html`):** Production control dashboard with live KPI metrics, automated deduplication queue, interactive room taxonomizer tester, and tour inclusion diff analyzer.

---

## ⚡ Quick Start Guide (Windows / macOS / Linux)

### Option 1: One-Click Startup (Windows)
Double-click `run_demo.bat` or run from PowerShell:
```powershell
Set-Location "$HOME\OneDrive\Desktop\TBO_Multi_Supplier_Optimization"
.\run_demo.bat
```
*This automatically checks Python dependencies, validates ports, boots the FastAPI server, and opens your browser.*

---

### Option 2: Manual Terminal Startup

#### 1. Clone & Enter Directory
```bash
git clone https://github.com/Abhishek-Gond-1387/TBO_Multi_Supplier_Optimization.git
cd TBO_Multi_Supplier_Optimization
```

#### 2. Create & Activate Virtual Environment
```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Run the Platform Server
```bash
python -m uvicorn services.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🌐 Web Interface Endpoints

Once the server is running, open the following URLs in your browser:

| Interface | URL | Description |
| :--- | :--- | :--- |
| **🚀 Animated Landing Page** | [http://127.0.0.1:8000/index.html](http://127.0.0.1:8000/index.html) | High-performance GSAP + Lenis kinetic hero showcase |
| **🗺️ Google Discovery Map** | [http://127.0.0.1:8000/map_view.html](http://127.0.0.1:8000/map_view.html) | Live multi-supplier inventory map with anti-collision pills |
| **🛡️ Operations Review Hub** | [http://127.0.0.1:8000/admin.html](http://127.0.0.1:8000/admin.html) | Human-in-the-loop matching queue & inclusion diff engine |
| **📖 Interactive API Docs** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger OpenAPI interactive documentation & test client |
| **📊 Prometheus Metrics** | [http://127.0.0.1:8000/metrics](http://127.0.0.1:8000/metrics) | Real-time scrapeable application performance metrics |

---

## 📡 REST API Reference

All REST endpoints are prefixed with `/api/v1`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/search` | Search inventory across hotels, tours, transit, and dining with multi-supplier rate parity. |
| `GET` | `/api/v1/suggestions` | Fast prefix autocomplete with entity categorization and thumbnail previews. |
| `POST` | `/api/v1/hotels/deduplicate` | Evaluate two hotel payloads using Jaro-Winkler, Haversine, and address overlap. |
| `POST` | `/api/v1/tours/diff` | Compute granular inclusion diffs between two tour offers across transfers, meals, and fast-track. |
| `POST` | `/api/v1/ai/itinerary` | Generate day-by-day itineraries with 3-tier budget breakdown (Budget, Comfort, Luxury). |
| `GET` | `/api/v1/review-queue` | Retrieve borderline duplicate matches awaiting operational resolution. |
| `PUT` | `/api/v1/review-queue/{id}` | Approve or reject a candidate match in the operational review queue. |
| `GET` | `/api/v1/analytics/summary` | Real-time CTR, booking conversion rates, and supplier quote metrics. |
| `GET` | `/api/v1/health` | Service health check with database and cache connectivity status. |

---

## 🧪 Automated Testing & Verification

Run the automated test suite with pytest:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Run the live inventory verification audit:
```powershell
.\.venv\Scripts\python.exe scripts/verify_1m_inventory.py
```

Run the interactive console walkthrough demo:
```powershell
.\.venv\Scripts\python.exe scripts/demo.py
```

---

## 📁 Repository Structure

```
TBO_Multi_Supplier_Optimization/
├── assets/                          # Static landing assets (GSAP, Lenis, Hero Imagery)
│   ├── hero_bg.jpg
│   └── js/
│       ├── gsap.min.js
│       ├── lenis.min.js
│       └── ScrollTrigger.min.js
├── data/                            # Verified inventory and OpenStreetMap datasets
│   ├── sample_inventory.json        # Seed multi-supplier dataset
│   ├── verified_image_catalog.json  # HD curated photography catalog
│   └── osm_inventory.status.json
├── database/                        # Database schemas and extensions
│   ├── init/
│   │   ├── 01-extensions.sql        # PostGIS & pgvector setup
│   │   └── 02-schema.sql            # Normalized tables and spatial indexes
│   └── analytics.sql
├── frontend/                        # Web applications & client components
│   ├── index.html                   # GSAP + Lenis Kinetic Landing Page
│   ├── map_view.html                # Google Discovery Map & Airbnb Sidebar
│   ├── admin.html                   # Operations Review & Taxonomy Hub
│   └── components/
│       └── MatchReviewQueue.tsx
├── scripts/                         # Automation, seed, and benchmark scripts
│   ├── demo.py                      # Interactive terminal demo
│   ├── verify_1m_inventory.py       # Catalog volume & latency audit
│   ├── build_10k_inventory.py
│   └── seed_demo_db.py
├── services/                        # Modular FastAPI backend services
│   ├── main.py                      # Core API server & route registration
│   ├── hotel_deduplication.py       # Jaro-Winkler & Haversine clustering
│   ├── room_normalizer.py           # Taxonomy normalization engine
│   ├── sightseeing_difference_engine.py # Inclusion diff engine
│   ├── dynamic_ranking_engine.py    # Multi-supplier score weighting
│   ├── pan_india_1m_engine.py       # High-throughput spatial inventory search
│   ├── ai_trip_planner.py           # Intelligent itinerary generation
│   ├── live_travel_service.py       # Real-time multi-supplier live quotes
│   ├── cache_service.py             # Memory & Redis cache layer
│   └── config.py                    # Environment & application settings
├── tests/                           # Pytest integration & unit test suite
│   ├── test_api.py
│   └── test_engines.py
├── .env.example                     # Environment template configuration
├── docker-compose.yml               # Production container orchestration
├── Dockerfile                       # Multi-stage production container build
├── pytest.ini                       # Test suite runner settings
├── requirements.txt                 # Core Python production dependencies
└── run_demo.bat                     # One-click Windows runner
```

---

## 🔒 Security & Resilience

- **Circuit Breaker:** Automatically isolates failing or slow third-party supplier endpoints after 5 consecutive failures, recovering gracefully after 30 seconds.
- **Supplier Rate Limiting:** Enforces timeout limits (800ms) to ensure external supplier lag never degrades the consumer discovery interface.
- **Zero Commercial API Dependency:** 100% self-contained utilizing free OpenStreetMap vector tiles, local SQLite/PostgreSQL storage, and open-source models.
- **RBAC & Token Security:** Secure HMAC-SHA256 JWT tokens with AES-256 symmetric credential encryption for supplier API credentials stored at rest.

---

## 📜 License

This project is licensed under the **MIT License**. Feel free to use, modify, and distribute with attribution.
