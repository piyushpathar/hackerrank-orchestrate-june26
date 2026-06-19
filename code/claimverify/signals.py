"""Deterministic text signals from conversation and history."""

from __future__ import annotations

import re

from .data import UserHistory

_INJECTION_PATTERNS = [
    r"ignore (all |any |previous |above )?(instructions|previous)",
    r"approve (this|the|my)? ?claim",
    r"mark (this|it|the row|as)",
    r"skip (manual )?review",
    r"follow (the )?note",
    r"note (is enough|says)",
    r"usko follow",
    r"approve kar (do|dena)",
    r"accept this quickly",
    r"should be approved",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


def detect_text_instruction(user_claim: str) -> bool:
    return bool(_INJECTION_RE.search(user_claim or ""))


def history_risk_flags(history: UserHistory | None) -> list[str]:
    if history is None:
        return []
    flags: list[str] = []
    if history.has_risk_flag:
        flags.append("user_history_risk")
    if history.needs_manual_review:
        flags.append("manual_review_required")
    return flags
