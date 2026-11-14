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

### 3. Google Maps-Grade Discovery Interface (Airbnb / OYO Spacious View)
- **10,800+ Live Verified Places:** Rich inventory with real HD travel photos, verified guest ratings, and live currency conversion (INR, USD, EUR, AED).
  - **Delhi & NCR:** 6,529 hotels & sightseeing tours
  - **Mumbai:** 1,200 items
  - **Goa:** 1,000 items
  - **Jaipur:** 800 items
  - **Agra:** 500 items
  - **Dubai:** 600+ items
- **Anti-Collision Price Pills (No Clutter, No Numbers on Dots):** Smooth Google Maps-style price pills with icons (🏨 / 🎡) positioned with 60px screen-space collision avoidance.
- **Spacious Airbnb / OYO Layout:** 560px wide left sidebar, large 220px photography header, guest favorite tags, strike-through pricing, and 1-click supplier rate comparisons.
- **As-You-Type Autocomplete Suggestions:** Instant live search suggestions grouped by Hotels, Sightseeing Tours, and Neighborhoods.
- **Satellite & Vector Map Layers:** One-click toggle between Google Roadmap vector styling and Esri World Imagery Satellite Hybrid view.
- **Voice Search Control:** Live browser Web Speech API integration with listening animation and backend NLP query parser.

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

## 🧪 Automated Testing

Run the full pytest suite:
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
All **22 automated unit and API integration tests** pass 100%.

---

## 📤 Push Changes to GitHub

```powershell
git add .
git commit -m "feat: 10,800+ inventory, airbnb/oyo spacious card view, anti-collision price markers, admin review hub"
git push origin main
```
