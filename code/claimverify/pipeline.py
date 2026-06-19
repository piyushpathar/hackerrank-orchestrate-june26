"""Per-claim orchestration: build request, call provider (with cache + retry),
normalize, and apply deterministic post-processing.

Post-processing guarantees three contract requirements regardless of provider:
1. user-history risk flags are merged in,
2. prompt-injection attempts are flagged as ``text_instruction_present``,
3. the output is coerced to the exact allowed values and schema.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from .cache import ResponseCache
from .config import Config
from .data import ClaimInput, EvidenceRequirement, UserHistory, requirements_for_object
from .images import LoadedImage, load_image
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schema import Prediction, normalize_risk_flags
from .signals import detect_text_instruction, history_risk_flags
from .providers import AnalyzeRequest, ModelResult


@dataclass
class ClaimResult:
    claim: ClaimInput
    prediction: Prediction
    input_tokens: int = 0
    output_tokens: int = 0
    images_sent: int = 0
    cached: bool = False
    error: str | None = None


def _load_images(claim: ClaimInput, max_dim: int) -> list[LoadedImage]:
    return [load_image(image_id, path, max_dim) for image_id, path in claim.resolve_images()]


def _apply_postprocessing(
    prediction: Prediction, claim: ClaimInput, history: UserHistory | None
) -> Prediction:
    flags = set(
        f for f in normalize_risk_flags(prediction.risk_flags).split(";") if f != "none"
    )
    flags.update(history_risk_flags(history))
    if detect_text_instruction(claim.user_claim):
        flags.add("text_instruction_present")
    prediction.risk_flags = normalize_risk_flags(sorted(flags))
    return prediction.normalized(claim.claim_object)


def _call_with_retry(provider, req: AnalyzeRequest, config: Config) -> ModelResult:
    last_error: Exception | None = None
    for attempt in range(config.max_retries):
        try:
            return provider.analyze(req)
        except Exception as exc:  # noqa: BLE001 - retried/raised below
            last_error = exc
            if attempt == config.max_retries - 1:
                break
            time.sleep(min(2 ** attempt, 30))
    raise last_error  # type: ignore[misc]


def process_claim(
    claim: ClaimInput,
    provider,
    config: Config,
    cache: ResponseCache,
    requirements: list[EvidenceRequirement],
    history_index: dict[str, UserHistory],
) -> ClaimResult:
    history = history_index.get(claim.user_id)
    obj_requirements = requirements_for_object(requirements, claim.claim_object)
    images = _load_images(claim, config.image_max_dim)
    image_ids = [img.image_id for img in images]

    user_prompt = build_user_prompt(claim, obj_requirements, history, image_ids)
    cache_key = cache.make_key(
        config.model, user_prompt, [img.content_hash for img in images]
    )

    cached_payload = cache.get(cache_key)
    if cached_payload is not None:
        prediction = _apply_postprocessing(
            Prediction.from_dict(cached_payload), claim, history
        )
        return ClaimResult(claim=claim, prediction=prediction, cached=True)

    req = AnalyzeRequest(
        claim=claim,
        requirements=obj_requirements,
        history=history,
        images=images,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    try:
        result = _call_with_retry(provider, req, config)
    except Exception as exc:  # noqa: BLE001 - degrade gracefully, never crash the batch
        fallback = Prediction(
            evidence_standard_met=False,
            evidence_standard_met_reason="Automated review failed; manual review required.",
            risk_flags="manual_review_required",
            claim_status="not_enough_information",
            claim_status_justification=f"Model call failed: {type(exc).__name__}.",
            valid_image=any(img.exists for img in images),
        )
        prediction = _apply_postprocessing(fallback, claim, history)
        return ClaimResult(claim=claim, prediction=prediction, error=str(exc))

    raw = dict(result.payload)
    raw["supporting_image_ids"] = _join_ids(raw.get("supporting_image_ids"))
    cache.set(cache_key, raw)

    prediction = _apply_postprocessing(Prediction.from_dict(raw), claim, history)
    return ClaimResult(
        claim=claim,
        prediction=prediction,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        images_sent=result.images_sent,
    )


def _join_ids(value: object) -> str:
    if value is None:
        return "none"
    if isinstance(value, (list, tuple, set)):
        ids = [str(v).strip() for v in value if str(v).strip()]
        return ";".join(ids) if ids else "none"
    text = str(value).strip()
    return text or "none"
