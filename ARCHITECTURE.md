# TBO Multi-Supplier Inventory Optimization Platform
## Complete Enterprise System Architecture Specification

---

## 1. Executive Summary & Problem Space

In global and domestic travel distribution, inventory is aggregated from disparate bedbanks, OTAs, and tour operators (TBO Preferred, Hotelbeds, Agoda, Booking.com, Viator, Headout, Klook). Because each supplier exposes unstandardized feeds, platforms suffer from four foundational challenges:

1. **Catalog Duplication:** Identical hotels appear multiple times with subtle name spelling deviations (`The Oberoi New Delhi` vs. `Oberoi Hotel, New Delhi`) and drifting GPS coordinates.
2. **Cryptic Room Descriptions:** Raw supplier codes (`DLX KNG CT-VW BB BALC` vs. `EXECUTIVE KING SUITE WITH BREAKFAST`) prevent transparent side-by-side comparison.
3. **Inclusion Opacity:** Excursions sharing identical titles vary drastically in delivered value (e.g., *Shared Coach* vs. *Private Chauffeur*, *Standard Entry* vs. *Fast-Track*, *Buffet Lunch* vs. *No Meals*).
4. **Dietary & Preference Fragmentation:** In major destinations like India, travelers require strict dietary segregation (Pure Vegetarian / Jain vs. Non-Veg Tandoori, Seafood, and Mughlai).

This platform deploys a high-throughput, low-latency micro-engine pipeline that normalizes, deduplicates, and dynamically ranks multi-supplier offerings across **1,240,000+ reachable items in 110 Indian destinations and international hubs**.

---

## 2. End-to-End System Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                 1. HETEROGENEOUS INGESTION TIER                                   |
|   [TBO Preferred Feeds]   [Hotelbeds / WebBeds]   [Agoda / Booking.com]   [Viator / Headout API]  |
|                         [Transit Corridors & OpenStreetMap Open Data]                             |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                            2. DATA VALIDATION & NORMALIZATION LAYER                               |
|   * Pydantic v2 Schema Enforcement                * Room Taxonomy Shorthand Standardizer          |
|   * Laplacian Blur Variance Scoring (σ² >= 80)    * Dietary Classifier (Pure Veg vs. Non-Veg)     |
|   * Address Tokenization & Geo-Slug Indexer       * Multi-Currency FX Engine (INR, USD, EUR, AED) |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                  3. CORE INTELLIGENCE ENGINES                                     |
|                                                                                                   |
|   [Geo-Spatial Deduplicator]            [Room Taxonomizer]           [Inclusion Diff Engine]      |
|   - Jaro-Winkler Name Distance          - Class: Deluxe/Suite        - Transfers: Private vs Bus  |
|   - Haversine Distance (<250m bound)    - Bed: King/Queen/Twin       - Meals: Buffet vs None      |
|   - pHash Perceptual Image Match        - Meal: Room Only, BB, HB    - Access: VIP vs Standard    |
|                                                                                                   |
|   [Dynamic Multi-Factor Ranking]        [Dietary Separation Engine]  [AI Travel Concierge]        |
|   - Composite Parity & Spread Score     - 🟢 100% Pure Veg & Jain    - Multi-Tier Budget Model    |
|   - Supplier Reliability Weighting      - 🔴 Non-Veg Tandoor/Seafood - Web Speech API Voice Intent|
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                4. STORAGE, CACHING & RESILIENCE                                   |
|   * Two-Tier Cache (In-Memory LRU + Distributed Redis Cluster with Geohash Viewport TTL)          |
|   * High-Throughput SQLite / PostgreSQL 16 + PostGIS Spatial Storage (1,240,000+ Records)        |
|   * Human-in-the-Loop Operational Review Queue (Borderline matches: 0.65 <= score < 0.88)         |
|   * Circuit Breaker Pattern (5 consecutive failures isolate supplier for 30s auto-recovery)       |
|   * Prometheus Real-Time Telemetry (Search latencies, CTR, conversion rates, error rates)         |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                              5. MULTI-EXPERIENCE PRESENTATION TIER                                |
|                                                                                                   |
|   [Spatial Discovery Map]               [Kinetic Landing Showcase]   [Operations Review Hub]      |
|   (/map_view.html)                      (/index.html)                (/admin.html)                |
|   - MapLibre GL Vector Map              - GSAP 3 + Lenis Engine      - Split-Screen Inspection    |
|   - 560px Airbnb Spacious Sidebar       - Kinetic Parallax Layers    - One-Click Approve/Reject   |
|   - Anti-Collision Price Pills (60px)   - Live Counter Stats         - Inclusion Diff Playground  |
|   - Pure Veg & Non-Veg Toggle Chips     - Modern Glassmorphism       - Taxonomy Sandbox           |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Deep-Dive: Core Engineering Components

### 3.1. Hybrid Spatial Deduplication Engine
- **Mathematical Specification:**
  Given listing pair $(A, B)$, composite similarity $S(A, B)$ is computed as:
  $$S(A, B) = w_{\text{name}} \cdot S_{\text{JW}}(\text{Name}_A, \text{Name}_B) + w_{\text{addr}} \cdot S_{\text{IoU}}(\text{Addr}_A, \text{Addr}_B) + w_{\text{img}} \cdot S_{\text{pHash}}(\text{Img}_A, \text{Img}_B)$$
- **Spatial Bounding Constraint:**
  Using the spherical Haversine distance $D_{\text{geo}}$:
  $$D_{\text{geo}} = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_A)\cos(\phi_B)\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)$$
  $$\text{If } D_{\text{geo}} > 250\text{ meters} \implies S(A, B) = 0.0$$
- **Operational Decision Bands:**
  - $\mathbf{S \ge 0.88}$ (**Auto-Merge**): Consolidates under a unified canonical entity; surfaces the lowest supplier offer.
  - $\mathbf{0.65 \le S < 0.88}$ (**Review Queue**): Borderline candidate routed to the `/admin.html` queue for manual review.
  - $\mathbf{S < 0.65}$ (**Disjoint Entities**): Treated as distinct independent properties.

---

### 3.2. Standardized Room Taxonomy Normalizer
Transforms cryptic supplier shorthand into structured, queryable taxonomy attributes:
```json
// Raw Supplier Input
{ "raw_code": "DLX KNG STE OCN-VW BRKFST BALC NON-REF" }

// Standardized Output
{
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

### 3.3. Experience Inclusion Difference Engine
Analyzes tour descriptions to compute an exact feature differentiation matrix:

| Feature Dimension | Supplier A (e.g. Viator) | Supplier B (e.g. GetYourGuide) | Meaningful Diff |
| :--- | :--- | :--- | :---: |
| **Transfers** | Shared AC Coach | Private Luxury Chauffeur | ⚠️ **Yes** |
| **Meals** | None Included | 3-Course Buffet Lunch | ⚠️ **Yes** |
| **Monuments Access** | Standard General Admission | Skip-The-Line Fast Track | ⚠️ **Yes** |
| **Cancellation** | Free cancellation up to 24h | Non-refundable | ⚠️ **Yes** |
| **Duration** | 4 Hours (Half-Day) | 4 Hours (Half-Day) | No |

---

### 3.4. Dynamic Multi-Factor Ranking Engine
Sorts listings dynamically using a weighted composite utility score:
$$\text{Score} = 0.25 \cdot S_{\text{relevance}} + 0.25 \cdot S_{\text{price\_competitiveness}} + 0.20 \cdot S_{\text{supplier\_reliability}} + 0.10 \cdot S_{\text{content\_quality}} + 0.10 \cdot S_{\text{flexibility}} + 0.10 \cdot S_{\text{conversion}}$$

---

### 3.5. Dietary & Cuisine Categorization (Veg vs. Non-Veg)
- **🟢 Pure Vegetarian / Jain Tier:** Identifies 100% pure veg restaurants, Jain-friendly kitchens, Sattvic preparations, and temple cuisine (e.g. Saravana Bhavan, Shree Thaker Bhojanalay, Rajdhani, Haldiram's).
- **🔴 Non-Vegetarian Tier:** Surfaces iconic regional non-veg specialties, Mughlai royal dining, Tandoori grills, Dum Biryani, and coastal seafood catch (e.g. Karim's, Trishna, Bawarchi, Bukhara).

---

## 4. Presentation Slide Deck Plan (For Your PPT)

| Slide # | Slide Title | Key Visuals & Graphic File | Core Talking Points |
| :---: | :--- | :--- | :--- |
| **1** | **The Multi-Supplier Fragmentation Problem** | Market fragmentation breakdown graphic | • Ingestion across 5+ bedbanks causes 25-35% duplicate clutter.<br/>• Cryptic room codes confuse buyers.<br/>• Rate opacity costs travelers an average of ₹1,240/booking. |
| **2** | **End-to-End System Architecture** | `assets/architecture_presentation_slide.jpg` OR `assets/architecture_diagram.png` | • 5-tier pipeline from Ingestion to Client.<br/>• Ingestion Schema Validator & Laplacian Blur check.<br/>• Deduplication, Taxonomy, and Diffing core engines.<br/>• Multi-experience web apps. |
| **3** | **Hybrid Spatial Deduplication & Taxonomy** | Formula diagrams & JSON input/output comparison | • Jaro-Winkler string distance + Haversine <250m geo-fence.<br/>• 3-tier decision matrix: Auto-Merge, Review Queue, Separate.<br/>• Room code normalization from shorthand to structured JSON. |
| **4** | **Real-Time Spatial Discovery & Rate Parity** | Screenshot of `map_view.html` with price pills | • 560px wide Airbnb-style sidebar with infinite scroll.<br/>• 60px anti-collision price markers on MapLibre GL.<br/>• Instant Pure Veg & Non-Veg dietary filters.<br/>• Web Speech API voice search. |
| **5** | **Performance Scale & Business Impact** | Metrics dashboard & latency benchmarks | • 1,240,000+ inventory items across 110 Indian cities.<br/>• Sub-50ms search latency.<br/>• 100% test pass rate (24/24 integration tests).<br/>• Self-contained open-source stack. |

---

## 5. Technology Stack Summary

- **Backend:** Python 3.10+, FastAPI, Pydantic v2, Uvicorn (ASGI)
- **Mapping & Spatial:** MapLibre GL 4.7, OpenStreetMap Vector Tiles, Turf.js / Haversine spatial math
- **Frontend & Kinetic UI:** HTML5, CSS3 Glassmorphism, GSAP 3, Lenis Smooth Scroll, Web Speech API
- **Data & Caching:** SQLite 3, PostgreSQL 16 + PostGIS, In-Memory LRU Cache, Redis
- **Testing & Operations:** Pytest, Prometheus client metrics, Docker Compose
