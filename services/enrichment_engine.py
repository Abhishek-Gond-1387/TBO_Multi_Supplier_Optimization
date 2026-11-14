"""Evidence-preserving hotel content normalization and image curation.

This module never invents amenities, ratings, descriptions, image metrics, or
external enrichment. It reports what source feeds supplied and what remains
missing so an operator can distinguish normalized claims from verified facts.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, urlsplit

import requests

AMENITY_TAXONOMY: dict[str, tuple[str, tuple[str, ...]]] = {
    "wifi": ("Connectivity", (r"wi[- ]?fi", r"internet", r"wlan", r"broadband")),
    "pool": ("Recreation", (r"pool", r"swimming")),
    "fitness": ("Wellness", (r"fitness", r"gym", r"workout")),
    "spa": ("Wellness", (r"spa", r"massage", r"sauna", r"steam room")),
    "dining": ("Dining", (r"restaurant", r"dining", r"bar", r"lounge", r"cafe")),
    "breakfast": ("Dining", (r"breakfast", r"buffet", r"morning meal")),
    "parking": ("Transport", (r"parking", r"valet", r"garage")),
    "airport_shuttle": ("Transport", (r"airport\s*shuttle", r"airport\s*transfer", r"airport\s*pickup")),
    "front_desk": ("Service", (r"front desk", r"reception", r"concierge")),
    "air_conditioning": ("Room comfort", (r"air condition", r"climate control", r"\ba/c\b", r"\bac\b")),
    "business": ("Business", (r"business center", r"meeting room", r"conference")),
    "room_service": ("Service", (r"room service", r"in-room dining")),
    "ev_charging": ("Transport", (r"ev charging", r"electric vehicle")),
    "pet_friendly": ("Policy", (r"pet-friendly", r"pets allowed", r"dog-friendly")),
}

SCENE_PATTERNS: dict[str, tuple[str, ...]] = {
    "FACADE_EXTERIOR": ("exterior", "facade", "building", "entrance", "architecture"),
    "LOBBY_RECEPTION": ("lobby", "reception", "atrium", "check-in"),
    "GUEST_ROOM": ("room", "bedroom", "suite", "bed", "balcony"),
    "BATHROOM": ("bathroom", "shower", "tub", "vanity"),
    "POOL_OUTDOOR": ("pool", "swimming", "sun deck"),
    "RESTAURANT_DINING": ("restaurant", "dining", "bar", "buffet", "breakfast", "cafe"),
    "SPA_WELLNESS": ("spa", "massage", "gym", "fitness", "sauna"),
}


def hamming_distance(hash1: str, hash2: str) -> int:
    """Compare two measured hexadecimal perceptual hashes."""
    try:
        return (int(hash1, 16) ^ int(hash2, 16)).bit_count()
    except (TypeError, ValueError):
        return 64


def classify_image_scene(filename_or_url: str, tags: list[str] | None = None) -> tuple[str, float]:
    """Classify only when source text contains an explicit scene hint."""
    text = f"{filename_or_url} {' '.join(tags or [])}".casefold()
    for scene, words in SCENE_PATTERNS.items():
        if any(word in text for word in words):
            return scene, 0.8
    return "UNCLASSIFIED", 0.0


def assess_image_quality(
    url: str,
    width: int | None = None,
    height: int | None = None,
    laplacian_var: float | None = None,
) -> dict[str, Any]:
    """Score measured image metadata; unknown dimensions are never assumed."""
    if width is None or height is None or laplacian_var is None:
        return {"url": url, "status": "NOT_ASSESSED", "quality_score": None}
    if width <= 0 or height <= 0:
        return {"url": url, "status": "INVALID_IMAGE_METADATA", "quality_score": None}
    aspect_ratio = round(width / height, 2)
    aspect_score = 20.0 if 1.3 <= aspect_ratio <= 1.85 else 10.0
    resolution_score = min(40.0, width * height / (1920 * 1080) * 40.0)
    sharpness_score = min(40.0, max(0.0, laplacian_var) / 120.0 * 40.0)
    total = round(aspect_score + resolution_score + sharpness_score, 1)
    return {
        "url": url, "status": "ASSESSED", "width": width, "height": height,
        "aspect_ratio": aspect_ratio, "laplacian_variance": round(laplacian_var, 1),
        "is_blurry": laplacian_var < 80.0,
        "is_low_res": width < 800 or height < 600,
        "quality_score": total,
        "quality_tier": "HIGH_DEF" if total >= 80 else "STANDARD" if total >= 60 else "LOW_QUALITY",
    }


def curate_canonical_gallery(raw_images: list[dict[str, Any]], target_count: int = 6) -> list[dict[str, Any]]:
    """Deduplicate supplied image metadata without manufacturing pHashes or quality."""
    candidates: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for image in raw_images:
        url = str(image.get("url", "")).strip()
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or url in seen_urls:
            continue
        seen_urls.add(url)
        quality = assess_image_quality(
            url, image.get("width"), image.get("height"), image.get("laplacian_var")
        )
        phash = image.get("phash")
        duplicate = False
        if phash:
            for existing in candidates:
                if existing.get("phash") and hamming_distance(str(phash), str(existing["phash"])) <= 6:
                    duplicate = True
                    if quality.get("quality_score") and quality["quality_score"] > (existing.get("quality") or {}).get("quality_score", -1):
                        existing.update(url=url, phash=phash, quality=quality, supplier=image.get("supplier"))
                    break
        if not duplicate and not quality.get("is_blurry", False):
            scene, confidence = classify_image_scene(url, image.get("tags", []))
            candidates.append({
                "url": url, "phash": phash, "scene": scene,
                "scene_confidence": confidence, "quality": quality,
                "supplier": image.get("supplier"), "source": image.get("source"),
                "license_url": image.get("license_url"),
            })
    candidates.sort(
        key=lambda row: (row["quality"].get("quality_score") is not None, row["quality"].get("quality_score") or 0),
        reverse=True,
    )
    return candidates[:max(0, target_count)]


def standardize_amenities(raw_amenities: list[str]) -> list[dict[str, Any]]:
    """Normalize source-reported amenity labels without asserting verification."""
    normalized: dict[str, dict[str, Any]] = {}
    for item in raw_amenities:
        original = str(item).strip()
        clean = re.sub(r"[^a-z0-9/+\-]+", " ", original.casefold()).strip()
        if not clean:
            continue
        match = next(
            ((code, category) for code, (category, patterns) in AMENITY_TAXONOMY.items()
             if any(re.search(pattern, clean) for pattern in patterns)),
            None,
        )
        if match:
            code, category = match
            label = code.replace("_", " ").title()
        else:
            code = re.sub(r"\s+", "_", clean)[:40]
            category = "Other source-reported feature"
            label = original
        row = normalized.setdefault(code, {
            "code": code, "category": category, "name": label,
            "verification_status": "SOURCE_REPORTED", "source_values": [],
        })
        if original not in row["source_values"]:
            row["source_values"].append(original)
    return list(normalized.values())


def synthesize_canonical_hotel_record(
    hotel_id: str, name: str, destination: str, supplier_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create an evidence-preserving normalized view from records actually supplied."""
    descriptions = list(dict.fromkeys(
        str(record.get("description", "")).strip()
        for record in supplier_records
        if str(record.get("description", "")).strip()
    ))
    amenities: list[str] = []
    images: list[dict[str, Any]] = []
    property_classes: list[float] = []
    sources: list[str] = []
    for record in supplier_records:
        source = str(record.get("supplier_name") or record.get("source") or "unknown")
        if source not in sources:
            sources.append(source)
        amenities.extend(str(value) for value in (record.get("amenities") or []))
        try:
            rating = float(record.get("property_classification"))
            if 0 < rating <= 5:
                property_classes.append(rating)
        except (TypeError, ValueError):
            pass
        for image in record.get("images") or []:
            if isinstance(image, str):
                images.append({"url": image, "supplier": source})
            elif isinstance(image, dict):
                images.append({**image, "supplier": source})
    gallery = curate_canonical_gallery(images)
    present = {
        "name": bool(name.strip()), "destination": bool(destination.strip()),
        "description": bool(descriptions), "amenities": bool(amenities),
        "images": bool(images), "property_classification": bool(property_classes),
    }
    missing = [field for field, has_value in present.items() if not has_value]
    return {
        "status": "PARTIAL_SOURCE_ENRICHMENT" if missing else "SOURCE_FIELDS_NORMALIZED",
        "canonical_id": hotel_id, "name": name, "destination": destination,
        "source_count": len(supplier_records), "sources": sources,
        "source_descriptions": descriptions,
        "structured_amenities": standardize_amenities(amenities),
        "property_classification_values": sorted(set(property_classes)),
        "canonical_gallery": gallery,
        "hero_image": gallery[0]["url"] if gallery else "",
        "gallery_count": len(gallery),
        "content_completeness": {
            "score_pct": round((sum(present.values()) / len(present)) * 100, 1),
            "present_fields": [field for field, has_value in present.items() if has_value],
            "missing_fields": missing,
        },
        "external_enrichment": {"status": "NOT_CONNECTED", "sources": []},
    }


def fetch_wikidata_enrichment(entity_id: str) -> dict[str, Any]:
    """Fetch free, attributed entity facts by a Wikidata ID supplied by OSM."""
    if not re.fullmatch(r"Q\d+", str(entity_id)):
        raise ValueError("A valid Wikidata QID is required")
    response = requests.get(
        "https://www.wikidata.org/w/api.php",
        params={
            "action": "wbgetentities", "ids": entity_id, "props": "labels|descriptions|claims",
            "languages": "en", "format": "json",
        },
        headers={"User-Agent": "TBO-Delhi-Inventory-Pilot/1.0 (open data enrichment)"},
        timeout=(3, 8),
    )
    response.raise_for_status()
    entity = response.json().get("entities", {}).get(entity_id, {})
    if "missing" in entity:
        return {"source": "Wikidata", "entity_id": entity_id, "status": "NOT_FOUND"}
    claims = entity.get("claims", {})
    image_file = None
    image_claims = claims.get("P18", [])
    if image_claims:
        image_file = image_claims[0].get("mainsnak", {}).get("datavalue", {}).get("value")
    website = None
    website_claims = claims.get("P856", [])
    if website_claims:
        website = website_claims[0].get("mainsnak", {}).get("datavalue", {}).get("value")
    return {
        "source": "Wikidata", "entity_id": entity_id, "status": "FOUND",
        "label": entity.get("labels", {}).get("en", {}).get("value"),
        "description": entity.get("descriptions", {}).get("en", {}).get("value"),
        "commons_file": image_file, "official_website": website,
        "source_url": f"https://www.wikidata.org/wiki/{entity_id}",
    }


def resolve_commons_file(file_title: str) -> dict[str, Any] | None:
    """Resolve a Commons file and its license/credit; reject unlicensed assets."""
    title = str(file_title).strip()
    if not title:
        return None
    if not title.casefold().startswith("file:"):
        title = f"File:{title}"
    response = requests.get(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query", "titles": title, "prop": "imageinfo",
            "iiprop": "url|extmetadata", "iiurlwidth": 1200, "format": "json",
        },
        headers={"User-Agent": "TBO-Delhi-Inventory-Pilot/1.0 (open data image license check)"},
        timeout=(3, 8),
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    image_info = next(iter(page.get("imageinfo", [])), {})
    if not image_info:
        return None
    metadata = image_info.get("extmetadata", {})
    def plain(key: str) -> str | None:
        raw = metadata.get(key, {}).get("value")
        return re.sub(r"<[^>]*>", " ", str(raw)).strip() if raw else None
    license_name = plain("LicenseShortName")
    license_url = plain("LicenseUrl")
    # Commons licenses are reusable, but attribution and share-alike terms matter.
    reusable = bool(license_name and ("cc" in license_name.casefold() or "public domain" in license_name.casefold() or "gnu" in license_name.casefold() or "free art" in license_name.casefold()))
    if not reusable:
        return {"status": "LICENSE_NOT_CONFIRMED", "file_title": title, "source_page": page.get("canonicalurl")}
    return {
        "status": "LICENSE_CONFIRMED", "file_title": title,
        "image_url": image_info.get("thumburl") or image_info.get("url"),
        "source_page": page.get("canonicalurl") or f"https://commons.wikimedia.org/wiki/{quote(title.replace(' ', '_'))}",
        "license_name": license_name, "license_url": license_url,
        "artist": plain("Artist"), "credit": plain("Credit"),
        "attribution_required": True,
    }
