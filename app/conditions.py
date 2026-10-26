"""Deterministic guard for eligibility conditions.

A prompt can make the model *likely* to keep "relating to a declared state of
emergency" next to the benefit it limits; this makes it *certain*. Each rule
pairs a phrase in the policy text with the words that show the condition was
carried into the answer. If an answer line cites a section containing the
phrase but doesn't carry the condition, the pipeline appends it.

Only conditions that decide eligibility belong here. Secondary qualifiers
(waiting periods, "unless otherwise noted") are left to the prompt and the eval.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .ingest import Chunk


@dataclass(frozen=True)
class ConditionRule:
    name: str
    in_source: "re.Pattern[str]"  # the condition as written in the policy
    in_answer: "re.Pattern[str]"  # evidence the answer kept it
    qualifier: str                # appended when it didn't


def _rx(p: str) -> "re.Pattern[str]":
    return re.compile(p, re.IGNORECASE)


RULES: Tuple[ConditionRule, ...] = (
    ConditionRule("state_of_emergency",
                  _rx(r"(relating to a declared state of emergency|relates to a state of emergency declared)"),
                  _rx(r"(state of emergency|declared emergency|emergency declaration)"),
                  "Applies only to a loss relating to a declared state of emergency."),
    ConditionRule("declared_catastrophe",
                  _rx(r"during a declared catastrophe"),
                  _rx(r"catastrophe"),
                  "Applies only during a declared catastrophe."),
    ConditionRule("suspected_fraud",
                  _rx(r"unless the claim involves suspected fraud"),
                  _rx(r"fraud"),
                  "Does not apply if the claim involves suspected fraud."),
    ConditionRule("covered_peril_mold",
                  _rx(r"only when the fungi or rot results from a covered peril"),
                  _rx(r"covered (peril|cause)"),
                  "Applies only when the mold or rot results from a covered peril."),
    ConditionRule("total_theft",
                  _rx(r"because of the total theft of your covered auto"),
                  _rx(r"theft|stolen"),
                  "Applies only when your car has been stolen."),
    ConditionRule("rideshare_endorsement",
                  _rx(r"unless a Ride-Share and Delivery endorsement is shown"),
                  _rx(r"endorsement"),
                  "Unless a Ride-Share and Delivery endorsement is shown in your Declarations."),
    ConditionRule("frozen_pipes_care",
                  _rx(r"unless you used reasonable care to maintain heat"),
                  _rx(r"reasonable care|maintain(ed)? heat|shut off the water"),
                  "Unless you used reasonable care to maintain heat or shut off and drain the water."),
    ConditionRule("roof_age_15",
                  _rx(r"if the roof surfacing is more than 15 years old"),
                  _rx(r"15 years|fifteen years"),
                  "Applies to roof surfacing more than 15 years old."),
)


def rules_for(cited_text: str) -> List[ConditionRule]:
    return [r for r in RULES if r.in_source.search(cited_text)]


def rules_by_chunk(chunks: Sequence[Chunk]) -> Dict[str, List[ConditionRule]]:
    """Which sections carry which conditions (used to audit the registry)."""
    out: Dict[str, List[ConditionRule]] = {}
    for c in chunks:
        if rules_for(c.text):
            out[c.chunk_id] = rules_for(c.text)
    return out


_HEADING = re.compile(r"^\s*(\*\*.+\*\*:?|#+ .+|.+:)\s*$")


def _scope(full: str, start: int, end: int) -> str:
    """The line holding [start, end) plus the nearest heading above it, which is
    how answers scope a bullet ("**California, declared emergency only:**")."""
    line_start = full.rfind("\n", 0, start) + 1
    line_end = full.find("\n", end)
    line = full[line_start: line_end if line_end != -1 else len(full)]
    for prev in reversed(full[:line_start].splitlines()):
        if not prev.strip():
            continue
        if _HEADING.match(prev):
            return prev + "\n" + line
        if not prev.lstrip().startswith(("-", "*", "•")) and not _HEADING.match(prev):
            break  # a body paragraph, not a heading: the bullet isn't scoped by it
    return line


def enforce(segments: List[dict]) -> List[str]:
    """Mutates `segments` in place, appending qualifiers that are missing.

    `segments` are [{text, refs, cited}] in answer order, where `cited` holds the
    exact source text each segment's citations point at. Rules are matched
    against that text, not the whole section, so a section with one conditional
    bullet doesn't attach the condition to its other bullets. Returns flags
    naming each condition that was added."""
    full = "".join(s["text"] for s in segments)
    offsets, pos = [], 0
    for s in segments:
        offsets.append((pos, pos + len(s["text"])))
        pos += len(s["text"])

    flags: List[str] = []
    for seg, (start, end) in zip(segments, offsets):
        needed = {r.name: r for t in seg.get("cited", []) for r in rules_for(t)}
        if not needed:
            continue
        scope = _scope(full, start, end)
        for rule in needed.values():
            if not rule.in_answer.search(scope):
                seg["text"] = seg["text"].rstrip() + f" [{rule.qualifier}]"
                flags.append(f"condition_added:{rule.name}")
    return flags
