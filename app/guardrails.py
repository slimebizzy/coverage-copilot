"""Deterministic input and output guards.

These run without a model call, so they are free, fast, and testable. The
model's own instructions are a second layer, not the only one.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple

MAX_QUESTION_CHARS = 2000

PII_PATTERNS = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "phone": re.compile(r"(?<!\d)(?:\+1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)"),
    "card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
}

INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore (all |any )?(the )?(previous|prior|above) (instructions|rules|directions)",
        r"disregard (your|the) (instructions|rules|system prompt)",
        r"(reveal|print|show|repeat) (me )?(your|the) (system prompt|instructions|hidden)",
        r"you are now (a|an|in) ",
        r"pretend (you are|to be) (an? )?(adjuster|underwriter|admin|employee)",
        r"\b(developer|admin|god) mode\b",
        r"i am (an? )?(adjuster|underwriter|employee|admin)[, ]+so (show|give|tell)",
    )
]


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for d in reversed(digits):
        n = int(d)
        if alt:
            n = n * 2 - 9 if n * 2 > 9 else n * 2
        total += n
        alt = not alt
    return total % 10 == 0


def redact_pii(text: str) -> Tuple[str, List[str]]:
    found: List[str] = []

    def sub(kind: str):
        def _r(m: "re.Match[str]") -> str:
            if kind == "card":
                digits = re.sub(r"\D", "", m.group(0))
                if not (13 <= len(digits) <= 16 and _luhn_ok(digits)):
                    return m.group(0)
            found.append(kind)
            return f"[REDACTED {kind.upper()}]"
        return _r

    for kind, pat in PII_PATTERNS.items():
        text = pat.sub(sub(kind), text)
    return text, found


@dataclass
class InputCheck:
    text: str
    blocked: bool = False
    reason: str = ""
    flags: List[str] = field(default_factory=list)


def check_input(question: str) -> InputCheck:
    q = question.strip()
    if not q:
        return InputCheck(q, blocked=True, reason="empty")
    if len(q) > MAX_QUESTION_CHARS:
        return InputCheck(q[:MAX_QUESTION_CHARS], blocked=True, reason="too_long")
    redacted, pii = redact_pii(q)
    flags = [f"pii:{k}" for k in pii]
    for pat in INJECTION_PATTERNS:
        if pat.search(redacted):
            return InputCheck(redacted, blocked=True, reason="prompt_injection", flags=flags + ["injection"])
    return InputCheck(redacted, flags=flags)


def scrub_output(text: str) -> Tuple[str, List[str]]:
    return redact_pii(text)
