from fastapi.testclient import TestClient
import json
import pytest

from services import main
from services.main import REVIEW_QUEUE, app

client = TestClient(app)


def test_health_reports_local_api_without_database():
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


def test_delhi_pilot_only_lists_the_bundled_city():
    response = client.get("/api/v1/destinations")
    assert response.status_code == 200
    payload = response.json()
    assert payload["countries"][0]["code"] == "IN"
    assert {row["destination"] for row in payload["destinations"]} == {"Delhi"}
    assert payload["destinations"][0]["count"] > 0


def test_free_open_dataset_is_loaded_into_local_inventory(tmp_path, monkeypatch):
    import asyncio

    async def _run():
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

    asyncio.run(_run())


def test_delhi_search_uses_source_records_without_inventing_supplier_offers():
    response = client.get(
        "/api/v1/inventory/search",
        params={"country_code": "in", "entity_type": "HOTEL"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert payload["source"].startswith("OpenStreetMap snapshot")
    assert all(row["item"]["country_code"] == "IN" for row in payload["results"])
    assert all(row["selected_supplier"] is None and row["item"]["offers"] == [] for row in payload["results"])


def test_country_filter_returns_no_fake_dubai_records():
    response = client.get(
        "/api/v1/inventory/search",
        params={"country_code": "AE", "destination": "Dubai", "entity_type": "HOTEL"},
    )
    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["results"] == []


def test_search_returns_grounded_ranking_without_supplier_feed():
    response = client.get(
        "/api/v1/inventory/search",
        params={"destination": "Delhi", "entity_type": "HOTEL"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert payload["results"][0]["selected_supplier"] is None
    assert payload["results"][0]["ranking_method"] == "TEXT_RELEVANCE_AND_SOURCE_COMPLETENESS"


def test_voice_endpoint_returns_parsed_filters_and_results():
    response = client.post(
        "/api/v1/voice/query",
        json={"transcript": "Find hotels in Delhi"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["parsed_filters"]["destination"] == "Delhi"
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
    assert payload["count"] == 0
    assert payload["results"] == []


def test_map_viewport_uses_bounding_box_and_returns_price_pins():
    response = client.post(
        "/api/v1/map/viewport-inventory",
        json={"min_lat": 28.50, "max_lat": 28.75, "min_lon": 77.00, "max_lon": 77.35},
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
            "supplier_code": "TEST", "supplier_hotel_id": "source-1", "name": "<b>Delhi Hotel</b>",
            "city": "Delhi", "country_code": "in", "latitude": 28.63, "longitude": 77.21,
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
    assert result["decision"] in {"AUTO_MERGE_CANDIDATE", "HUMAN_REVIEW", "REJECT"}
    if result["decision"] in {"AUTO_MERGE_CANDIDATE", "HUMAN_REVIEW"}:
        review_id = result["review_id"]
        queued = client.get("/api/v1/admin/matches/review-queue").json()
        assert queued["count"] == 1
        resolved = client.put(f"/api/v1/review-queue/{review_id}", json={"status": "APPROVED", "reviewer": "test"})
        assert resolved.status_code == 200
        assert resolved.json()["status"] == "APPROVED"


def test_open_data_status_does_not_claim_supplier_rates_or_customer_reviews():
    response = client.get("/api/v1/data/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["has_open_data_snapshot"] is True
    assert payload["has_live_rates"] is False
    assert payload["has_customer_reviews"] is False


def test_out_of_scope_trip_planner_is_not_published():
    assert client.post("/api/v1/ai/chat", json={"message": "hello"}).status_code == 404
    assert client.post("/api/v1/ai/plan-trip", json={"destination": "Delhi"}).status_code == 404

