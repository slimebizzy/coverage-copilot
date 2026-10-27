"""HTTP API and chat UI. Run: uvicorn app.server:app --reload"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Literal, Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from .pipeline import ROLES, STATES, TRACE_PATH, Pipeline  # noqa: E402
from .retrieval import can_access  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Coverage Copilot")
pipeline = Pipeline()


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class AskRequest(BaseModel):
    question: str = Field(max_length=4000)
    role: Literal["policyholder", "adjuster", "underwriter"] = "policyholder"
    state: Optional[str] = None
    history: List[Turn] = Field(default_factory=list, max_length=20)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/meta")
def meta() -> Dict[str, object]:
    return {
        "roles": list(ROLES),
        "states": list(STATES),
        "backend": pipeline.llm.name,
        "offline": pipeline.llm.name.startswith("fake"),
        "documents": documents(),
    }


def documents() -> List[Dict[str, object]]:
    seen: Dict[str, Dict[str, object]] = {}
    for c in pipeline.chunks:
        seen.setdefault(c.doc_id, {"id": c.doc_id, "title": c.doc_title, "jurisdiction": c.jurisdiction,
                                   "roles": c.roles, "version": c.version, "internal": c.is_internal})
    return list(seen.values())


@app.post("/api/ask")
def ask(req: AskRequest) -> Dict[str, object]:
    ans = pipeline.ask(req.question, req.role, req.state, [t.model_dump() for t in req.history])
    return ans.to_dict()


@app.get("/api/section")
def section(id: str, role: Literal["policyholder", "adjuster", "underwriter"] = "policyholder",
            state: Optional[str] = None) -> Dict[str, object]:
    """One section, for "compare with the standard policy". Same access rule as
    retrieval: a section the caller can't see is a 404, not a 403, so its
    existence doesn't leak either."""
    chunk = pipeline.retriever.index.by_id.get(id)
    if chunk is None or not can_access(chunk, role, state if state in ("CA", "TX") else None):
        raise HTTPException(status_code=404, detail="not found")
    return {"chunk_id": chunk.chunk_id, "doc_title": chunk.doc_title, "section": chunk.section,
            "heading": chunk.heading, "jurisdiction": chunk.jurisdiction, "doc_version": chunk.version,
            "blocks": chunk.blocks, "internal": chunk.is_internal}


class Feedback(BaseModel):
    trace_id: str = Field(pattern=r"^[0-9a-f]{12}$")
    rating: Literal["up", "down"]
    note: str = Field(default="", max_length=1000)


FEEDBACK_PATH = TRACE_PATH.parent / "feedback.jsonl"


@app.post("/api/feedback")
def feedback(fb: Feedback) -> Dict[str, bool]:
    """Thumbs up/down joined to the request trace by trace_id. The "adjuster
    disagreed" rate in the deployment memo comes from here."""
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with FEEDBACK_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), **fb.model_dump()}) + "\n")
    return {"ok": True}


@app.get("/api/stats")
def stats() -> Dict[str, object]:
    """Rolling numbers from the trace log: the seed of Project 3's dashboard."""
    if not TRACE_PATH.exists():
        return {"requests": 0}
    rows = [json.loads(line) for line in TRACE_PATH.read_text().splitlines()[-1000:] if line.strip()]
    by_status: Dict[str, int] = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    totals = sorted(r["latency_ms"].get("total", 0) for r in rows)
    pct = lambda p: totals[min(len(totals) - 1, int(p * len(totals)))] if totals else 0  # noqa: E731
    cache_read = sum(r["usage"].get("cache_read_input_tokens", 0) for r in rows)
    input_total = sum(r["usage"].get("input_tokens", 0) + r["usage"].get("cache_read_input_tokens", 0)
                      + r["usage"].get("cache_creation_input_tokens", 0) for r in rows)
    return {
        "requests": len(rows),
        "by_status": by_status,
        "latency_ms_p50": pct(0.5),
        "latency_ms_p95": pct(0.95),
        "total_cost_usd": round(sum(r["cost_usd"] for r in rows), 4),
        "cache_hit_ratio": round(cache_read / input_total, 3) if input_total else None,
    }
