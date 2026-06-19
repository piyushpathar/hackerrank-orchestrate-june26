"""Runtime configuration from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = REPO_ROOT / "dataset"
DEFAULT_CACHE_DIR = REPO_ROOT / "code" / ".cache"

PRICING = {
    "claude-3-5-sonnet-latest": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-latest": {"input": 0.80, "output": 4.0},
    "gpt-4o": {"input": 2.50, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Config:
    provider: str
    model: str
    max_workers: int
    max_retries: int
    request_timeout: float
    max_output_tokens: int
    cache_dir: Path
    use_cache: bool
    image_max_dim: int

    @property
    def pricing(self) -> dict[str, float]:
        return PRICING.get(self.model, {"input": 0.0, "output": 0.0})


def _auto_provider() -> tuple[str, str]:
    if _env("ANTHROPIC_API_KEY"):
        return "anthropic", _env("CLAIMVERIFY_MODEL", "claude-3-5-sonnet-latest")
    if _env("OPENAI_API_KEY"):
        return "openai", _env("CLAIMVERIFY_MODEL", "gpt-4o")
    return "heuristic", "heuristic-v1"


def load_config() -> Config:
    forced = _env("CLAIMVERIFY_PROVIDER")
    if forced == "anthropic":
        provider, model = "anthropic", _env("CLAIMVERIFY_MODEL", "claude-3-5-sonnet-latest")
    elif forced == "openai":
        provider, model = "openai", _env("CLAIMVERIFY_MODEL", "gpt-4o")
    elif forced == "heuristic":
        provider, model = "heuristic", "heuristic-v1"
    else:
        provider, model = _auto_provider()

    return Config(
        provider=provider,
        model=model,
        max_workers=int(_env("CLAIMVERIFY_WORKERS", "4")),
        max_retries=int(_env("CLAIMVERIFY_MAX_RETRIES", "4")),
        request_timeout=float(_env("CLAIMVERIFY_TIMEOUT", "60")),
        max_output_tokens=int(_env("CLAIMVERIFY_MAX_TOKENS", "1024")),
        cache_dir=Path(_env("CLAIMVERIFY_CACHE_DIR", str(DEFAULT_CACHE_DIR))),
        use_cache=_env("CLAIMVERIFY_NO_CACHE") is None,
        image_max_dim=int(_env("CLAIMVERIFY_IMAGE_MAX_DIM", "1024")),
    )
