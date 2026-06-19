"""Output schema, allowed values, and normalization."""

from __future__ import annotations

from dataclasses import asdict, dataclass

OUTPUT_COLUMNS = [
    "user_id", "image_paths", "user_claim", "claim_object",
    "evidence_standard_met", "evidence_standard_met_reason", "risk_flags",
    "issue_type", "object_part", "claim_status", "claim_status_justification",
    "supporting_image_ids", "valid_image", "severity",
]

CLAIM_STATUS = {"supported", "contradicted", "not_enough_information"}
ISSUE_TYPES = {
    "dent", "scratch", "crack", "glass_shatter", "broken_part", "missing_part",
    "torn_packaging", "crushed_packaging", "water_damage", "stain", "none", "unknown",
}
OBJECT_PARTS = {
    "car": {"front_bumper", "rear_bumper", "door", "hood", "windshield", "side_mirror",
            "headlight", "taillight", "fender", "quarter_panel", "body", "unknown"},
    "laptop": {"screen", "keyboard", "trackpad", "hinge", "lid", "corner", "port",
               "base", "body", "unknown"},
    "package": {"box", "package_corner", "package_side", "seal", "label", "contents",
                "item", "unknown"},
}
RISK_FLAGS = {
    "none", "blurry_image", "cropped_or_obstructed", "low_light_or_glare",
    "wrong_angle", "wrong_object", "wrong_object_part", "damage_not_visible",
    "claim_mismatch", "possible_manipulation", "non_original_image",
    "text_instruction_present", "user_history_risk", "manual_review_required",
}
SEVERITY = {"none", "low", "medium", "high", "unknown"}


def _coerce_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def normalize_enum(value: object, allowed: set[str], default: str) -> str:
    if value is None:
        return default
    token = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    return token if token in allowed else default


def normalize_risk_flags(flags: object) -> str:
    if flags is None:
        return "none"
    if isinstance(flags, str):
        raw = [f for f in flags.replace(",", ";").split(";")]
    elif isinstance(flags, (list, tuple, set)):
        raw = [str(f) for f in flags]
    else:
        raw = [str(flags)]
    seen: list[str] = []
    for item in raw:
        token = item.strip().lower().replace(" ", "_").replace("-", "_")
        if token in RISK_FLAGS and token != "none" and token not in seen:
            seen.append(token)
    return ";".join(seen) if seen else "none"


@dataclass
class Prediction:
    evidence_standard_met: bool = False
    evidence_standard_met_reason: str = ""
    risk_flags: str = "none"
    issue_type: str = "unknown"
    object_part: str = "unknown"
    claim_status: str = "not_enough_information"
    claim_status_justification: str = ""
    supporting_image_ids: str = "none"
    valid_image: bool = False
    severity: str = "unknown"

    def normalized(self, claim_object: str) -> "Prediction":
        parts = OBJECT_PARTS.get(claim_object, set()) | {"unknown"}
        return Prediction(
            evidence_standard_met=_coerce_bool(self.evidence_standard_met),
            evidence_standard_met_reason=str(self.evidence_standard_met_reason or "").strip(),
            risk_flags=normalize_risk_flags(self.risk_flags),
            issue_type=normalize_enum(self.issue_type, ISSUE_TYPES, "unknown"),
            object_part=normalize_enum(self.object_part, parts, "unknown"),
            claim_status=normalize_enum(self.claim_status, CLAIM_STATUS, "not_enough_information"),
            claim_status_justification=str(self.claim_status_justification or "").strip(),
            supporting_image_ids=str(self.supporting_image_ids or "none").strip() or "none",
            valid_image=_coerce_bool(self.valid_image),
            severity=normalize_enum(self.severity, SEVERITY, "unknown"),
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Prediction":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_row(self) -> dict[str, str]:
        row = asdict(self)
        row["evidence_standard_met"] = "true" if self.evidence_standard_met else "false"
        row["valid_image"] = "true" if self.valid_image else "false"
        return {k: str(v) for k, v in row.items()}
