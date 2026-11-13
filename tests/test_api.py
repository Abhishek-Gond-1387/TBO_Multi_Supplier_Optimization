from fastapi.testclient import TestClient
import json
import pytest

from services import main
from services.main import REVIEW_QUEUE, app

client = TestClient(app)


def test_health_reports_sample_mode_without_database():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"]["configured"] is False


def test_public_map_configuration_defaults_to_free_vector_map_style():
    response = client.get("/api/v1/config/map")
    assert response.status_code == 200
    assert response.json()["style_url"] == "https://tiles.openfreemap.org/styles/liberty"
    assert "OpenStreetMap contributors" in response.json()["attribution"]
    assert response.json()["default_destination"] == "Delhi"
    assert response.json()["default_latitude"] == 28.6139
    assert response.json()["default_longitude"] == 77.2090
    assert response.json()["default_zoom"] == 11


def test_destinations_start_with_india_then_include_dubai():
    response = client.get("/api/v1/destinations")
    assert response.status_code == 200
    payload = response.json()
    assert payload["countries"][0]["code"] == "IN"
    assert {"Delhi", "Mumbai", "Goa", "Jaipur"}.issubset(
        {row["destination"] for row in payload["destinations"] if row["country_code"] == "IN"}
    )
    assert any(row["destination"] == "Dubai" and row["country_code"] == "AE" for row in payload["destinations"])


@pytest.mark.asyncio
async def test_free_open_dataset_is_loaded_into_local_inventory(tmp_path, monkeypatch):
    dataset = tmp_path / "osm_inventory.json"
    dataset.write_text(json.dumps({
        "hotels": [{
            "source_id": "osm/node/987", "name": "Open Delhi Guesthouse", "city": "Delhi",
            "country_code": "IN", "latitude": 28.63, "longitude": 77.21, "amenities": ["wifi"],
        }],
        "attractions": [],
    }), encoding="utf-8")
    monkeypatch.setattr(main, "OPEN_DATA_INVENTORY_PATH", dataset)
    rows = await main.load_inventory()
    open_row = next(row for row in rows if row.source_id == "osm/node/987")
    assert open_row.entity_type == "HOTEL"
    assert open_row.destination == "Delhi"
    assert open_row.country_code == "IN"
    assert open_row.offers == []


def test_india_search_filters_to_inr_supplier_offers():
    response = client.get(
        "/api/v1/inventory/search",
        params={"country_code": "in", "currency": "INR", "entity_type": "HOTEL"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert all(row["item"]["country_code"] == "IN" for row in payload["results"])
    assert all(row["selected_supplier"]["currency"] == "INR" for row in payload["results"])


def test_country_filter_can_switch_from_india_to_dubai():
    response = client.get(
        "/api/v1/inventory/search",
        params={"country_code": "AE", "destination": "Dubai", "currency": "USD", "entity_type": "HOTEL"},
    )
    assert response.status_code == 200
    assert response.json()["count"] >= 1
    assert all(row["item"]["country_code"] == "AE" for row in response.json()["results"])


def test_search_returns_ranked_supplier_offers():
    response = client.get(
        "/api/v1/inventory/search",
        params={"destination": "Dubai", "entity_type": "HOTEL", "max_price": 150},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert payload["results"][0]["selected_supplier"]
    assert payload["results"][0]["rank_factors"]["supplier_reliability"] >= 0


def test_voice_endpoint_returns_parsed_filters_and_results():
    response = client.post(
        "/api/v1/voice/query",
        json={"transcript": "Find 3-star hotels in Dubai with breakfast under 150 dollars"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["parsed_filters"]["destination"] == "Dubai"
    assert payload["count"] >= 1
    assert payload["voice_reply"].startswith("I found")


def test_voice_endpoint_searches_india_and_rupee_budget():
    response = client.post(
        "/api/v1/voice/query",
        json={"transcript": "Find hotels in India under 8000 rupees with breakfast"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["parsed_filters"]["country_code"] == "IN"
    assert payload["parsed_filters"]["currency"] == "INR"
    assert payload["count"] >= 1
    assert all(row["item"]["country_code"] == "IN" for row in payload["results"])


def test_map_viewport_uses_bounding_box_and_returns_price_pins():
    response = client.post(
        "/api/v1/map/viewport-inventory",
        json={"min_lat": 25.10, "max_lat": 25.30, "min_lon": 55.05, "max_lon": 55.40},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["hotels"]
    assert all("min_price" in item for item in payload["hotels"])


def test_room_and_sightseeing_endpoints():
    room = client.post("/api/v1/rooms/normalize", json={"raw_name": "DLX DBL OCVW RO W/BALC"})
    assert room.status_code == 200
    assert room.json()["room_class"] == "Deluxe"
    sightseeing = client.post(
        "/api/v1/sightseeing/compare",
        json={
            "left_title": "At The Top Level 124",
            "left_description": "General admission, no transfer.",
            "right_title": "Sky Lounge Level 148 with Private Transfer and Lunch",
            "right_description": "VIP access with private transfer and lunch.",
        },
    )
    assert sightseeing.status_code == 200
    assert "transfers" in sightseeing.json()["differences"]


def test_ingestion_validation_endpoint():
    response = client.post(
        "/api/v1/ingest/hotels/validate",
        json={
            "supplier_code": "DEMO", "supplier_hotel_id": "demo-1", "name": "<b>Demo Hotel</b>",
            "city": "Dubai", "country_code": "ae", "latitude": 25.2, "longitude": 55.3,
            "star_rating": 4, "amenities": ["wifi", "pool"],
        },
    )
    assert response.status_code == 200
    assert response.json()["normalized_payload"]["name"] == "Demo Hotel"
    assert response.json()["data_quality_score"] > 0


def test_manual_review_flow_is_actionable():
    REVIEW_QUEUE.clear()
    response = client.post(
        "/api/v1/matches/compare",
        json={
            "left": {"name": "Address Sky View Downtown", "destination": "Dubai", "address": "Sheikh Zayed Road, Downtown Dubai", "latitude": 25.2106, "longitude": 55.2781},
            "right": {"name": "Address Downtown Sky View", "destination": "Dubai", "address": "Downtown Dubai, Sheikh Zayed Road", "latitude": 25.2120, "longitude": 55.2800},
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["decision"] in {"AUTO_MERGE", "HUMAN_REVIEW", "REJECT"}
    if result["decision"] == "HUMAN_REVIEW":
        review_id = result["review_id"]
        queued = client.get("/api/v1/admin/matches/review-queue").json()
        assert queued["count"] == 1
        resolved = client.put(f"/api/v1/review-queue/{review_id}", json={"status": "APPROVED", "reviewer": "test"})
        assert resolved.status_code == 200
        assert resolved.json()["status"] == "APPROVED"
