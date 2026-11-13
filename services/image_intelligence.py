"""Perceptual image hashing and simple image metadata helpers."""

from __future__ import annotations

from io import BytesIO
import ipaddress
import socket
from typing import Any
from urllib.parse import urlsplit

import imagehash
from PIL import Image, ImageFilter, ImageStat


def perceptual_hash(image_bytes: bytes) -> str:
    with Image.open(BytesIO(image_bytes)) as image:
        return str(imagehash.phash(image.convert("RGB")))


def compare_image_hashes(left_hash: str, right_hash: str, max_distance: int = 6) -> dict:
    distance = imagehash.hex_to_hash(left_hash) - imagehash.hex_to_hash(right_hash)
    return {"hamming_distance": distance, "looks_duplicate": distance <= max_distance}


def image_metadata(image_bytes: bytes) -> dict[str, int | float]:
    with Image.open(BytesIO(image_bytes)) as image:
        rgb = image.convert("RGB")
        brightness = sum(ImageStat.Stat(rgb).mean) / 3
        return {
            "width": image.width,
            "height": image.height,
            "brightness": round(brightness, 2),
        }


def compute_image_metrics(image_bytes: bytes) -> dict[str, Any]:
    with Image.open(BytesIO(image_bytes)) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        phash = str(imagehash.phash(rgb))
        try:
            import cv2
            import numpy as np

            decoded = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
            if decoded is None:
                raise ValueError("Unsupported image payload")
            gray = cv2.cvtColor(decoded, cv2.COLOR_BGR2GRAY)
            laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        except ImportError:
            edge = rgb.convert("L").filter(ImageFilter.FIND_EDGES)
            laplacian_var = float(ImageStat.Stat(edge).var[0])
        resolution_score = min(1.0, (width * height) / (1920 * 1080)) * 50.0
        blur_score = min(50.0, laplacian_var / 5.0)
        return {
            "phash": phash,
            "width": width,
            "height": height,
            "laplacian_var": round(laplacian_var, 2),
            "quality_score": round(resolution_score + blur_score, 2),
            "is_blurry": laplacian_var < 80.0,
        }


def deduplicate_image_assets(
    assets: list[tuple[str, bytes]], max_hamming_distance: int = 6
) -> list[dict[str, Any]]:
    """Deduplicate supplied image bytes without hidden network requests."""
    unique: list[dict[str, Any]] = []
    for source, payload in assets:
        metrics = compute_image_metrics(payload)
        candidate = {"source": source, **metrics}
        match = next(
            (
                index
                for index, item in enumerate(unique)
                if imagehash.hex_to_hash(metrics["phash"])
                - imagehash.hex_to_hash(item["phash"])
                <= max_hamming_distance
            ),
            None,
        )
        if match is None:
            if not metrics["is_blurry"]:
                unique.append(candidate)
        elif metrics["quality_score"] > unique[match]["quality_score"]:
            unique[match] = candidate
    return sorted(unique, key=lambda item: item["quality_score"], reverse=True)


def _is_public_image_url(url: str) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    try:
        addresses = {entry[4][0] for entry in socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))}
        return bool(addresses) and all(ipaddress.ip_address(address).is_global for address in addresses)
    except (OSError, ValueError):
        return False


def deduplicate_image_catalog(image_urls: list[str], max_hamming_distance: int = 6) -> list[str]:
    """Fetch a bounded number of public images and return quality-ranked unique URLs."""
    import requests

    assets = []
    for url in image_urls[:50]:
        if not _is_public_image_url(url):
            continue
        try:
            with requests.get(
                url,
                headers={"User-Agent": "TBO-MultiSupplier-Platform/0.2"},
                timeout=(2, 6),
                stream=True,
                allow_redirects=False,
            ) as response:
                response.raise_for_status()
                if not response.headers.get("Content-Type", "").lower().startswith("image/"):
                    continue
                payload = bytearray()
                for chunk in response.iter_content(64 * 1024):
                    payload.extend(chunk)
                    if len(payload) > 8 * 1024 * 1024:
                        payload.clear()
                        break
                if payload:
                    assets.append((url, bytes(payload)))
        except (requests.RequestException, OSError, ValueError):
            continue
    return [item["source"] for item in deduplicate_image_assets(assets, max_hamming_distance)]
