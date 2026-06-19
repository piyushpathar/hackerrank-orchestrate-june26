"""Image loading, media-type detection, optional downscaling, and hashing."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from pathlib import Path

_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}


@dataclass(frozen=True)
class LoadedImage:
    image_id: str
    media_type: str
    data_b64: str
    content_hash: str
    exists: bool


def _detect_media_type(data: bytes) -> str:
    for magic, mime in _MAGIC.items():
        if data.startswith(magic):
            return mime
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _maybe_downscale(data: bytes, media_type: str, max_dim: int) -> tuple[bytes, str]:
    try:
        import io
        from PIL import Image  # type: ignore
    except Exception:
        return data, media_type
    try:
        with Image.open(io.BytesIO(data)) as im:
            if max(im.size) <= max_dim:
                return data, media_type
            im = im.convert("RGB")
            im.thumbnail((max_dim, max_dim))
            buf = io.BytesIO()
            im.save(buf, format="WEBP", quality=85)
            return buf.getvalue(), "image/webp"
    except Exception:
        return data, media_type


def load_image(image_id: str, path: Path, max_dim: int = 1024) -> LoadedImage:
    if not path.exists():
        return LoadedImage(image_id, "image/jpeg", "", "", exists=False)
    raw = path.read_bytes()
    content_hash = hashlib.sha256(raw).hexdigest()
    media_type = _detect_media_type(raw)
    data, media_type = _maybe_downscale(raw, media_type, max_dim)
    return LoadedImage(
        image_id=image_id,
        media_type=media_type,
        data_b64=base64.b64encode(data).decode("ascii"),
        content_hash=content_hash,
        exists=True,
    )
