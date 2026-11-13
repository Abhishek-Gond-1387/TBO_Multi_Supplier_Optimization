"""Perceptual image hashing and simple image metadata helpers."""

from __future__ import annotations

from io import BytesIO

import imagehash
from PIL import Image, ImageStat


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
