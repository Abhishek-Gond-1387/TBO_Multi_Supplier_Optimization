"""Optional Celery ingestion worker; transformer weights load only on demand."""

from __future__ import annotations

import json
import os

from celery import Celery

from services.ingestion_validator import RawSupplierHotelPayload, calculate_data_quality_score

celery_app = Celery(
    "tbo_tasks",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_time_limit=600,
)


@celery_app.task(name="tasks.process_raw_supplier_hotel")
def process_raw_supplier_hotel(payload_json: str) -> dict:
    raw = json.loads(payload_json)
    payload = RawSupplierHotelPayload.model_validate(raw)
    result = {
        "status": "SUCCESS",
        "supplier_code": payload.supplier_code,
        "supplier_hotel_id": payload.supplier_hotel_id,
        "normalized_name": payload.name,
        "quality_score": calculate_data_quality_score(payload),
        "semantic_matching_enabled": os.getenv("ENABLE_SEMANTIC_MATCHING", "false").lower() == "true",
    }
    images = []
    if payload.images:
        from services.image_intelligence import deduplicate_image_catalog

        images = deduplicate_image_catalog(payload.images)
    result["curated_images"] = images
    if result["semantic_matching_enabled"]:
        from services.hotel_deduplication import _load_embedding_model

        text = f"{payload.name} {payload.city} {' '.join(payload.amenities)}"
        result["embedding"] = _load_embedding_model().encode(text).tolist()
    return result
