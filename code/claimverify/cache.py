"""Content-addressed disk cache for model responses."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class ResponseCache:
    def __init__(self, cache_dir: Path, enabled: bool = True) -> None:
        self.cache_dir = cache_dir
        self.enabled = enabled
        if enabled:
            cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def make_key(model: str, prompt: str, image_hashes: list[str]) -> str:
        hasher = hashlib.sha256()
        hasher.update(model.encode("utf-8"))
        hasher.update(b"\x00")
        hasher.update(prompt.encode("utf-8"))
        for h in image_hashes:
            hasher.update(b"\x00")
            hasher.update(h.encode("utf-8"))
        return hasher.hexdigest()

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> dict | None:
        if not self.enabled:
            return None
        path = self._path(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def set(self, key: str, value: dict) -> None:
        if not self.enabled:
            return
        try:
            self._path(key).write_text(
                json.dumps(value, ensure_ascii=False), encoding="utf-8"
            )
        except OSError:
            pass
