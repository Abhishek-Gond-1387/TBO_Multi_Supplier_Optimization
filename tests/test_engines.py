import pytest
from pydantic import ValidationError

from services.dynamic_ranking_engine import calculate_price_competitiveness, select_supplier_offer
from services.hotel_deduplication import compute_hotel_match_score
from services.ingestion_validator import RawSupplierHotelPayload, calculate_data_quality_score
from services.models import SupplierOffer
from services.room_normalizer import normalize_room_title
from services.sightseeing_difference_engine import extract_tour_inclusions, generate_inclusion_diff
from services.supplier_resilience import CircuitBreaker, CircuitOpenError, SlidingWindowRateLimiter
from services.voice_intent_parser import parse_voice_travel_query


def test_duplicate_hotel_names_and_nearby_gps_auto_match():
    score, features = compute_hotel_match_score(
        supplier_name="JW Marriott Marquis Dubai",
        supplier_addr="Sheikh Zayed Road, Business Bay, Dubai",
        supplier_lat=25.1856,
        supplier_lon=55.2580,
        canonical_name="JW Marriott Marquis Hotel",
        canonical_addr="Business Bay, Sheikh Zayed Rd, Dubai",
        canonical_lat=25.1858,
        canonical_lon=55.2582,
    )
    assert score >= 0.88
    assert features["geo_dist_m"] < 50


def test_same_hotel_name_far_away_is_rejected():
    score, _ = compute_hotel_match_score(
        supplier_name="Hilton Garden Inn",
        supplier_addr="Dubai",
        supplier_lat=25.1180,
        supplier_lon=55.2000,
        canonical_name="Hilton Garden Inn",
        canonical_addr="Ras Al Khaimah",
        canonical_lat=25.7900,
        canonical_lon=55.9700,
    )
    assert score == 0.0


def test_room_taxonomy_extracts_class_bed_view_meal_and_balcony():
    result = normalize_room_title("DLX DBL OCVW RO W/BALC")
    assert result["room_class"] == "Deluxe"
    assert result["bed_type"] == "Twin"
    assert result["view_type"] == "Ocean View"
    assert result["meal_plan"] == "Room Only"
    assert result["balcony"] == "true"


def test_sightseeing_inclusions_preserve_transfer_meal_access_and_policy_differences():
    basic = extract_tour_inclusions(
        "Burj Khalifa Level 124 Ticket",
        "Standard entry ticket. No transfer included.",
        ["Observation deck access"],
    )
    premium = extract_tour_inclusions(
        "Burj Khalifa Sky Lounge Level 148 with Private Chauffeur & Lunch",
        "VIP access with private hotel pickup, a 3-course lunch and free cancellation up to 24 hours.",
        ["Private car transfer", "Buffet lunch", "VIP Sky Lounge"],
    )
    assert basic["transfer"] == "NONE"
    assert premium["transfer"] == "PRIVATE"
    assert premium["meal"] == "LUNCH"
    assert premium["access"] == "VIP_LOUNGE"
    assert premium["cancellation"] == "FREE_24H"
    difference = generate_inclusion_diff(basic, premium)
    assert {"transfers", "meals", "access_type", "cancellation"}.issubset(difference)


def test_supplier_selection_and_price_competitiveness():
    assert calculate_price_competitiveness(80, 100) == 1.0
    offers = [
        SupplierOffer(supplier_name="Reliable", price=120, reliability_score=0.99),
        SupplierOffer(supplier_name="Flexible", price=130, reliability_score=0.96, cancellation_flexible=True),
    ]
    selected, ranked = select_supplier_offer(offers, 125)
    assert selected is not None
    assert selected.supplier_name in {"Reliable", "Flexible"}
    assert len(ranked) == 2


def test_supplier_payload_is_cleaned_scored_and_rejects_null_island():
    hotel = RawSupplierHotelPayload(
        supplier_code="TEST",
        supplier_hotel_id="123",
        name="  <b>Sample   Hotel</b>  ",
        street_address="A long street address",
        city="Dubai",
        country_code="ae",
        latitude=25.2,
        longitude=55.3,
        star_rating=4,
        amenities=[" WIFI ", "pool"],
    )
    assert hotel.name == "Sample Hotel"
    assert hotel.country_code == "AE"
    assert calculate_data_quality_score(hotel) == 65.0
    with pytest.raises(ValidationError):
        RawSupplierHotelPayload(
            supplier_code="TEST", supplier_hotel_id="bad", name="Bad Hotel", city="Nowhere",
            country_code="ZZ", latitude=0, longitude=0,
        )


def test_voice_query_extracts_destination_budget_stars_landmark_and_inclusions():
    result = parse_voice_travel_query(
        "Find 4-star hotels in Dubai near the beach with free breakfast and free cancellation under 150 dollars next weekend"
    )
    assert result["entity_type"] == "HOTEL"
    assert result["destination"] == "Dubai"
    assert result["star_rating"] == 4.0
    assert result["max_price"] == 150.0
    assert result["landmark"] == "Beach"
    assert "BREAKFAST" in result["inclusions"]
    assert "FREE_CANCELLATION" in result["inclusions"]
    assert result["date_window"] == "NEXT_WEEKEND"


def test_sliding_window_rate_limiter():
    limiter = SlidingWindowRateLimiter()
    assert limiter.allow("supplier", 2, now=1.0)
    assert limiter.allow("supplier", 2, now=1.1)
    assert not limiter.allow("supplier", 2, now=1.2)
    assert limiter.allow("supplier", 2, now=2.1)


@pytest.mark.asyncio
async def test_circuit_breaker_opens_and_recovers():
    breaker = CircuitBreaker(failure_threshold=1, recovery_seconds=0.01)

    async def fail():
        raise RuntimeError("supplier down")

    async def succeed():
        return "ok"

    with pytest.raises(RuntimeError):
        await breaker.call(fail)
    with pytest.raises(CircuitOpenError):
        await breaker.call(succeed)
    breaker.opened_at -= 1
    assert await breaker.call(succeed) == "ok"
    assert breaker.state == "CLOSED"
