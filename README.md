# TBO Multi-Supplier Inventory Optimization & Google Discovery Platform

[![Python checks](https://github.com/Abhishek-Gond-1387/TBO_Multi_Supplier_Optimization/actions/workflows/tests.yml/badge.svg)](https://github.com/Abhishek-Gond-1387/TBO_Multi_Supplier_Optimization/actions/workflows/tests.yml)

A high-performance real-time multi-supplier optimization platform integrating **Hotels** and **Sightseeing / Experiences** across major destinations (Delhi & NCR, Mumbai, Goa, Jaipur, Agra, and Dubai) with a Google Maps-grade spatial exploration interface, live autocomplete suggestions, voice search, room taxonomy normalization, tour inclusion diffing, and dynamic supplier ranking.

---

## 🌟 Key Features & Problem Solutions

### 1. Sightseeing & Experiences Optimization
- **Cross-Supplier Matching:** Accurately deduplicate and match tours and experiences across suppliers (Viator, GetYourGuide, Headout, Klook, TBO Experiences).
- **Nuanced Inclusion Differentiation:** Distinguishes meaningful product variations:
  - **Transfers:** `None` vs `Shared AC Coach` vs `Private Luxury Chauffeur`
  - **Meals:** `None` vs `Breakfast` vs `Buffet Lunch` vs `Gourmet 3-Course Dinner`
  - **Access Types:** `Standard General Admission` vs `Skip-The-Line Fast Track` vs `VIP Lounge Access / Level 148`
  - **Durations:** 1h to Full Day (8h)
  - **Cancellation Terms:** `Free 24h` vs `Free 48h` vs `Non-refundable`
- **Inclusion Diff Engine:** Explains why higher-priced options provide value without confusing customers.

### 2. Hotel Inventory Optimization
- **Deduplication & Consolidation:** Hybrid Jaro-Winkler, spatial Haversine distance (<250m), address token overlap, and perceptual image hashing (pHash) consolidate duplicate listings.
- **Equivalent Room Type Normalization:** Maps raw fragmented supplier codes (e.g., `DLX KNG CT-VW BB BALC`, `EXEC STE 1KNG CLB LVL`) into a standardized taxonomy (Class: Deluxe/Suite, Bed: King/Queen, View: City/Ocean/Garden, Meal: Bed & Breakfast, Balcony).
- **Multi-Supplier Rates Matrix:** Side-by-side comparison across TBO Preferred, Hotelbeds, Agoda, Expedia, and WebBeds factoring in base rates, taxes, payment terms (`PAY_NOW` vs `PAY_AT_HOTEL`), cancellation deadlines, and supplier reliability scores.
- **Content & Image Intelligence:** Quality scoring based on Laplacian blur variance and HD resolution thresholds.

### 3. Pan-India 1,000,000+ Live Multi-Supplier Discovery Platform
- **1,240,000+ Reachable Live Inventory across 110 Indian Cities:**
  - 🏨 **520,000+ Hotels & Stays:** Luxury 5-Star Heritage, Boutique Business, Comfort Midscale & Budget.
  - 🎡 **334,000+ Sightseeing & Experiences:** Fast-Track Monument Entry, Guided Heritage Trails & Safaris.
  - 🚕 **210,000+ Transit Hubs & Corridors:** High-Speed Vande Bharat Rail, Metro Junctions & Airport Shuttles.
  - 🍽️ **173,000+ Iconic Dining Spots:** Heritage Royal Dining, Street Food Trails & Coastal Kitchens.
- **Real-Time Rate Parity Matrix:** Instant live rates across TBO Preferred, Agoda, Hotelbeds, Booking.com, Viator, and MakeMyTrip.
- **Personal AI Travel Concierge:** Dynamic day-by-day itinerary planner with 3-tier pricing (Budget, Mid-Level, Luxury), authentic regional dining spots, and audio voice readout.
- **Spacious Airbnb / OYO Layout:** 560px wide left sidebar, large 220px photography header, guest favorite tags, strike-through pricing, and 1-click supplier rate comparisons.
- **Anti-Collision Price Pills:** Google Maps-style price pills with icons positioned with 60px screen-space collision avoidance.
- **Voice Assistance:** Web Speech API integration in both search bar and conversational AI agent drawer.

---

## 🚀 How to Run the Project (चलने का तरीका)

### Option 1: One-Click Run (Windows)

Double-click or run from PowerShell:
```powershell
Set-Location "$HOME\OneDrive\Desktop\TBO_Multi_Supplier_Optimization"
.\run_demo.bat
```
This automatically verifies dependencies, starts the FastAPI server + Web frontend, and opens the browser.

---

### Option 2: Manual Terminal Commands

#### Terminal 1: Start the Backend API & Web App
```powershell
cd "$HOME\OneDrive\Desktop\TBO_Multi_Supplier_Optimization"
.\.venv\Scripts\python.exe -m uvicorn services.main:app --host 127.0.0.1 --port 8000
```

#### Terminal 2: Start the Frontend Server (Optional)
```powershell
cd "$HOME\OneDrive\Desktop\TBO_Multi_Supplier_Optimization"
.\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

#### Open in Your Browser:
- **Google Discovery Map:** [http://127.0.0.1:8000/map_view.html](http://127.0.0.1:8000/map_view.html) (or [http://127.0.0.1:5500/map_view.html](http://127.0.0.1:5500/map_view.html))
- **Operations & Match Review Hub:** [http://127.0.0.1:8000/admin.html](http://127.0.0.1:8000/admin.html)
- **Interactive Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🔍 Verify 1,000,000+ Live Inventory (PowerShell)

Run the comprehensive audit to inspect the 1,000,000+ SQLite database, query latencies, and multi-supplier quotes:
```powershell
.\.venv\Scripts\python.exe scripts/verify_1m_inventory.py
```

Run the interactive live walkthrough demo:
```powershell
.\.venv\Scripts\python.exe scripts/demo.py
```

---

## 🧪 Automated Testing

Run the full pytest suite:
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
All **24 automated unit and API integration tests** pass 100%.

---

## 📤 Push Changes to GitHub

```powershell
git add .
git commit -m "feat: 1,000,000+ live multi-supplier inventory, verification suite, and airbnb spacious discovery"
git push origin main
```
