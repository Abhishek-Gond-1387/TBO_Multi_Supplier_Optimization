"""
Generates a 1920x1080 high-resolution, modern 16:9 system architecture diagram
suitable for PowerPoint (PPT) slides and executive technical presentations.
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_architecture_diagram():
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), color="#080c16")
    draw = ImageDraw.Draw(img)

    # 1. Background Grid & Subtle Ambient Glow
    grid_color = "#0e1628"
    for x in range(0, W, 48):
        draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(0, H, 48):
        draw.line([(0, y), (W, y)], fill=grid_color, width=1)

    # Load Windows System Fonts
    font_path_regular = "C:/Windows/Fonts/segoeui.ttf"
    font_path_bold = "C:/Windows/Fonts/segoeuib.ttf"
    
    font_title = ImageFont.truetype(font_path_bold, 36)
    font_subtitle = ImageFont.truetype(font_path_regular, 17)
    font_col_header = ImageFont.truetype(font_path_bold, 18)
    font_card_title = ImageFont.truetype(font_path_bold, 15)
    font_card_body = ImageFont.truetype(font_path_regular, 12)
    font_badge = ImageFont.truetype(font_path_bold, 13)
    font_footer = ImageFont.truetype(font_path_regular, 13)

    # 2. Header Section
    draw.text((70, 42), "TBO Multi-Supplier Inventory Optimization Platform", fill="#ffffff", font=font_title)
    draw.text((70, 88), "END-TO-END ENTERPRISE ARCHITECTURE • DEDUPLICATION • RATE PARITY • 1,240,000+ CATALOG", fill="#00f0ff", font=font_subtitle)

    # Header Metric Badges (Top Right)
    badges = [
        ("● 24/24 Tests Pass", "#10b981", "#064e3b"),
        ("● 110 Indian Cities", "#38bdf8", "#0c4a6e"),
        ("● <250m Haversine", "#a855f7", "#581c87"),
        ("● Sub-50ms Latency", "#f59e0b", "#78350f"),
    ]
    bx = 1120
    for text, text_col, bg_col in badges:
        draw.rounded_rectangle([bx, 50, bx + 175, 84], radius=8, fill=bg_col, outline=text_col, width=1)
        draw.text((bx + 12, 58), text, fill=text_col, font=font_badge)
        bx += 190

    # 3. Pipeline Columns Setup
    cols = [
        {
            "num": "01",
            "name": "SUPPLIER STREAMS",
            "sub": "Heterogeneous Data Ingestion",
            "color": "#f59e0b",
            "cards": [
                ("TBO Preferred Inventory", "Domestic & global verified hotel feeds with instant booking parity."),
                ("Hotelbeds & WebBeds", "Wholesale bedbank streams with cryptic room codes and meal codes."),
                ("Agoda & Booking.com", "OTA live dynamic rate parity, cancellation terms & tax breakdowns."),
                ("Viator & Headout Activities", "Sightseeing tours, fast-track monuments, safaris & city day passes."),
                ("Transit & OpenStreetMap", "High-speed rail (Vande Bharat), metro hubs & airport EV corridors.")
            ]
        },
        {
            "num": "02",
            "name": "INGESTION & CLEANING",
            "sub": "Normalization & Quality",
            "color": "#00f0ff",
            "cards": [
                ("Pydantic Schema Validator", "Strict typing, coordinates geo-range checks (-90/90, -180/180) & slugging."),
                ("Room Taxonomy Parser", "Maps DLX KNG CT-VW BB into Class, Bed, View, Meal Plan & Balcony."),
                ("Laplacian Blur Variance", "Image intelligence rejecting blurry supplier photos (Var < 80.0 threshold)."),
                ("Dietary Classifier (Veg / Non-Veg)", "Detects Pure Veg, Jain, Non-Veg Tandoori, Mughlai & Coastal Seafood tags."),
                ("Token Normalizer & Slugger", "Standardizes property names, strips legal entities & normalizes addresses.")
            ]
        },
        {
            "num": "03",
            "name": "INTELLIGENT ENGINES",
            "sub": "Optimization & Diffing Core",
            "color": "#a855f7",
            "cards": [
                ("Geo-Spatial Deduplicator", "Jaro-Winkler string similarity + Haversine <250m geo-fence + pHash clustering."),
                ("Inclusion Difference Engine", "Diffs sightseeing offers: Shared vs Private Car, Buffet Lunch, Fast-Track."),
                ("Multi-Factor Dynamic Ranking", "Composite utility score: Price Parity + Reliability + Quality + Flexibility."),
                ("AI Travel Concierge & Voice", "Web Speech API intent parser + 3-tier budget day-by-day route generation."),
                ("Rate Parity Matrix", "Instant side-by-side comparison uncovering net supplier savings (avg ₹1,240).")
            ]
        },
        {
            "num": "04",
            "name": "STORAGE & CACHING",
            "sub": "Distributed Persistence",
            "color": "#10b981",
            "cards": [
                ("Two-Tier Distributed Cache", "High-speed In-Memory LRU + Redis cluster with TTL geo-viewport caching."),
                ("1,240,000+ Catalog Database", "High-throughput indexed spatial storage across 110 Indian hubs & UAE/Greece."),
                ("Human-in-the-Loop Queue", "Borderline duplicate pairs (0.65 <= score < 0.88) routed for manual decision."),
                ("Circuit Breaker & Resilience", "Isolates failing supplier endpoints after 5 errors with 30s auto-recovery."),
                ("Prometheus Telemetry", "Real-time metrics: Search latencies, CTR, conversion rates & audit trails.")
            ]
        },
        {
            "num": "05",
            "name": "CLIENT PLATFORMS",
            "sub": "Multi-Experience Frontend",
            "color": "#38bdf8",
            "cards": [
                ("Spatial Discovery Map", "/map_view.html: MapLibre GL vector tiles, 560px Airbnb sidebar & voice search."),
                ("Anti-Collision Price Pills", "Google Maps-grade price markers with 60px screen-space collision avoidance."),
                ("Kinetic Landing Experience", "/index.html: GSAP 3 + Lenis smooth scrolling, hero parallax & live statistics."),
                ("Operations Review Portal", "/admin.html: Operator split-screen match review, inclusion diff sandbox."),
                ("FastAPI Swagger Docs", "/docs: Interactive OpenAPI client testing for all B2B API endpoints.")
            ]
        }
    ]

    col_w = 330
    gap = 26
    start_x = 70
    start_y = 145
    card_h = 138
    card_gap = 14

    for c_idx, col in enumerate(cols):
        cx = start_x + c_idx * (col_w + gap)
        
        # Column Header Container
        draw.rounded_rectangle([cx, start_y, cx + col_w, start_y + 60], radius=10, fill="#0f172a", outline=col["color"], width=1)
        draw.text((cx + 14, start_y + 10), f"{col['num']}. {col['name']}", fill="#ffffff", font=font_col_header)
        draw.text((cx + 14, start_y + 35), col["sub"], fill=col["color"], font=font_card_body)

        # 5 Feature Cards per column
        for r_idx, (ctitle, cdesc) in enumerate(col["cards"]):
            cy = start_y + 74 + r_idx * (card_h + card_gap)
            card_box = [cx, cy, cx + col_w, cy + card_h]
            
            # Draw Glassmorphism Card
            draw.rounded_rectangle(card_box, radius=10, fill="#0e1726", outline="#1e293b", width=1)
            # Left accent highlight bar
            draw.rounded_rectangle([cx, cy, cx + 4, cy + card_h], radius=2, fill=col["color"])

            # Card Header with colored icon dot
            draw.ellipse([cx + 16, cy + 16, cx + 24, cy + 24], fill=col["color"])
            draw.text((cx + 32, cy + 12), ctitle, fill="#ffffff", font=font_card_title)

            # Word-wrapped Card Body
            words = cdesc.split()
            lines = []
            cur_line = []
            for w in words:
                cur_line.append(w)
                test_str = " ".join(cur_line)
                if len(test_str) > 42:
                    cur_line.pop()
                    lines.append(" ".join(cur_line))
                    cur_line = [w]
            if cur_line:
                lines.append(" ".join(cur_line))

            ly = cy + 44
            for line in lines[:4]:
                draw.text((cx + 16, ly), line, fill="#94a3b8", font=font_card_body)
                ly += 19

        # Draw Directional Pipeline Arrows Between Columns
        if c_idx < len(cols) - 1:
            arrow_x = cx + col_w + (gap // 2)
            arrow_y = start_y + 350
            draw.line([(arrow_x - 10, arrow_y), (arrow_x + 8, arrow_y)], fill="#334155", width=2)
            draw.polygon([(arrow_x + 8, arrow_y - 6), (arrow_x + 14, arrow_y), (arrow_x + 8, arrow_y + 6)], fill="#00f0ff")

    # 4. Footer Section
    draw.line([(70, 990), (W - 70, 990)], fill="#1e293b", width=1)
    draw.text((70, 1015), "Tech Stack: Python 3.10+ • FastAPI • MapLibre GL • GSAP 3 & Lenis • SQLite / PostgreSQL • Pydantic v2 • Web Speech API", fill="#64748b", font=font_footer)
    draw.text((W - 380, 1015), "Confidential • TBO Multi-Supplier Architecture Deck", fill="#64748b", font=font_footer)

    os.makedirs("assets", exist_ok=True)
    out_path = "assets/architecture_diagram.png"
    img.save(out_path, "PNG", quality=95)
    print(f"Architecture diagram generated successfully at: {out_path}")
    return out_path

if __name__ == "__main__":
    create_architecture_diagram()
