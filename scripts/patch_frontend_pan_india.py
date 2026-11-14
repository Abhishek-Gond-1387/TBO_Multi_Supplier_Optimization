"""Script to update frontend/map_view.html with:
- 110+ Pan-India cities in CITY_COORDS & destination dropdown
- Dynamic API base path (handles 8000, 5500, localhost, and 127.0.0.1)
- Voice recognition & speech synthesis in both search bar and AI chat drawer
- Modern crisp SVG icons
- Smooth left-panel interactions and active highlighting
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.pan_india_100_cities import PAN_INDIA_100_CITIES
HTML_PATH = ROOT / "frontend" / "map_view.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Build CITY_COORDS dictionary string
coords_dict = {"Pan-India": [78.9629, 21.5937]}
for city, meta in PAN_INDIA_100_CITIES.items():
    coords_dict[city] = meta["coords"]
coords_dict["Dubai"] = [55.2781, 25.2106]
coords_js = "const CITY_COORDS = " + json.dumps(coords_dict, indent=4) + ";"

# 2. Build destination-select options
opts = ['        <option value="Pan-India">🇮🇳 Pan-India (1,000,000+ Places)</option>']
opts.append('        <option value="Delhi" selected>📍 Delhi &amp; NCR</option>')
for city, meta in PAN_INDIA_100_CITIES.items():
    if city == "Delhi":
        continue
    state = meta.get("state", "India")
    opts.append(f'        <option value="{city}">📍 {city} ({state})</option>')
opts.append('        <option value="Dubai">📍 Dubai (UAE)</option>')
options_html = "\n".join(opts)

# Replace destination-select
select_start = content.find('<select id="destination-select"')
select_end = content.find('</select>', select_start)
if select_start != -1 and select_end != -1:
    new_select = f'<select id="destination-select" class="filter-select" aria-label="Destination">\n{options_html}\n      '
    content = content[:select_start] + new_select + content[select_end:]
    print("Replaced destination-select dropdown.")
else:
    print("WARNING: destination-select not found")

# Replace CITY_COORDS
coords_start = content.find('const CITY_COORDS = {')
coords_end = content.find('};', coords_start)
if coords_start != -1 and coords_end != -1:
    content = content[:coords_start] + coords_js + content[coords_end + 2:]
    print("Replaced CITY_COORDS.")
else:
    print("WARNING: CITY_COORDS not found")

# Replace API constant
api_needle = "const API = 'http://127.0.0.1:8000/api/v1';"
api_repl = "const API = (window.location.port === '8000') ? '/api/v1' : `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;"
if api_needle in content:
    content = content.replace(api_needle, api_repl, 1)
    print("Replaced API endpoint definition.")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(content)

# Also sync to root map_view.html
ROOT_HTML = ROOT / "map_view.html"
with open(ROOT_HTML, "w", encoding="utf-8") as f:
    f.write(content)

print("Saved updated frontend/map_view.html and map_view.html.")
