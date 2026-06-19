"""Dataset loading: claims, user history, evidence requirements."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from .config import DATASET_DIR


@dataclass(frozen=True)
class UserHistory:
    user_id: str
    past_claim_count: int = 0
    accept_claim: int = 0
    manual_review_claim: int = 0
    rejected_claim: int = 0
    last_90_days_claim_count: int = 0
    history_flags: str = "none"
    history_summary: str = ""

    @property
    def has_risk_flag(self) -> bool:
        return "user_history_risk" in self.history_flags

    @property
    def needs_manual_review(self) -> bool:
        return "manual_review_required" in self.history_flags


@dataclass(frozen=True)
class EvidenceRequirement:
    requirement_id: str
    claim_object: str
    applies_to: str
    minimum_image_evidence: str


@dataclass
class ClaimInput:
    user_id: str
    image_paths: str
    user_claim: str
    claim_object: str
    expected: dict[str, str] = field(default_factory=dict)

    @property
    def image_path_list(self) -> list[str]:
        return [p.strip() for p in self.image_paths.split(";") if p.strip()]

    def resolve_images(self, dataset_dir: Path = DATASET_DIR) -> list[tuple[str, Path]]:
        resolved: list[tuple[str, Path]] = []
        for rel in self.image_path_list:
            path = (dataset_dir / rel).resolve()
            image_id = Path(rel).stem
            resolved.append((image_id, path))
        return resolved


def _to_int(value: str, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def load_user_history(path: Path | None = None) -> dict[str, UserHistory]:
    path = path or DATASET_DIR / "user_history.csv"
    history: dict[str, UserHistory] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            uid = row["user_id"].strip()
            history[uid] = UserHistory(
                user_id=uid,
                past_claim_count=_to_int(row.get("past_claim_count", 0)),
                accept_claim=_to_int(row.get("accept_claim", 0)),
                manual_review_claim=_to_int(row.get("manual_review_claim", 0)),
                rejected_claim=_to_int(row.get("rejected_claim", 0)),
                last_90_days_claim_count=_to_int(row.get("last_90_days_claim_count", 0)),
                history_flags=(row.get("history_flags") or "none").strip(),
                history_summary=(row.get("history_summary") or "").strip(),
            )
    return history


def load_evidence_requirements(path: Path | None = None) -> list[EvidenceRequirement]:
    path = path or DATASET_DIR / "evidence_requirements.csv"
    requirements: list[EvidenceRequirement] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            requirements.append(EvidenceRequirement(
                requirement_id=row["requirement_id"].strip(),
                claim_object=row["claim_object"].strip().lower(),
                applies_to=row["applies_to"].strip(),
                minimum_image_evidence=row["minimum_image_evidence"].strip(),
            ))
    return requirements


def requirements_for_object(
    requirements: list[EvidenceRequirement], claim_object: str
) -> list[EvidenceRequirement]:
    claim_object = claim_object.lower()
    return [r for r in requirements if r.claim_object in (claim_object, "all")]


def load_claims(path: Path, has_labels: bool = False) -> list[ClaimInput]:
    from .schema import OUTPUT_COLUMNS
    label_cols = [c for c in OUTPUT_COLUMNS if c not in {
        "user_id", "image_paths", "user_claim", "claim_object"
    }]
    claims: list[ClaimInput] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            expected = (
                {c: (row.get(c) or "").strip() for c in label_cols}
                if has_labels else {}
            )
            claims.append(ClaimInput(
                user_id=row["user_id"].strip(),
                image_paths=row["image_paths"].strip(),
                user_claim=row["user_claim"].strip(),
                claim_object=row["claim_object"].strip().lower(),
                expected=expected,
            ))
    return claims
