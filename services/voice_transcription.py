"""Optional local Faster-Whisper transcription for audio supplied by the client."""

from __future__ import annotations

import base64
import os
import tempfile
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=2)
def _model(model_size: str):
    from faster_whisper import WhisperModel

    return WhisperModel(
        model_size,
        device=os.getenv("WHISPER_DEVICE", "cpu"),
        compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
        download_root=os.getenv("HF_HOME", "./models_cache"),
    )


def transcribe_base64(audio_base64: str, model_size: str = "tiny") -> str:
    """Decode a bounded audio payload and transcribe it locally; no network API is called."""
    raw = base64.b64decode(audio_base64, validate=True)
    if not raw or len(raw) > 15 * 1024 * 1024:
        raise ValueError("Audio must be between 1 byte and 15 MB")
    if model_size not in {"tiny", "base", "small"}:
        raise ValueError("Choose a supported Whisper model size: tiny, base, or small")
    model = _model(model_size)
    with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as audio_file:
        audio_file.write(raw)
        audio_path = Path(audio_file.name)
    try:
        segments, _ = model.transcribe(str(audio_path), vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments).strip()
    finally:
        audio_path.unlink(missing_ok=True)
