"""Model backends. `AnthropicLLM` calls Claude; `FakeLLM` is an offline stand-in
used by tests and by the demo when no API credentials are configured."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

MODEL = os.getenv("COPILOT_MODEL", "claude-opus-5-5")
EFFORT = os.getenv("COPILOT_EFFORT", "medium")

# USD per million tokens. Cache writes (5-minute TTL) bill at 1.25x input.
PRICES = {
    "claude-opus-5-5": {"input": 4.00, "output": 20.00, "cache_read": 0.20},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00, "cache_read": 0.20},
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50, "cache_read": 0.01},
}


@dataclass
class Citation:
    search_result_index: int
    cited_text: str
    source: str
    title: Optional[str]


@dataclass
class TextPart:
    text: str
    citations: List[Citation] = field(default_factory=list)


@dataclass
class LLMResult:
    parts: List[TextPart]
    stop_reason: str
    model: str
    usage: Dict[str, int]
    request_id: Optional[str] = None

    @property
    def text(self) -> str:
        return "".join(p.text for p in self.parts)


def cost_usd(model: str, usage: Dict[str, int]) -> float:
    p = PRICES.get(model)
    if not p:
        return 0.0
    return (
        usage.get("input_tokens", 0) * p["input"]
        + usage.get("cache_creation_input_tokens", 0) * p["input"] * 1.25
        + usage.get("cache_read_input_tokens", 0) * p["cache_read"]
        + usage.get("output_tokens", 0) * p["output"]
    ) / 1_000_000


class LLM(Protocol):
    name: str

    def answer(self, system: str, messages: List[Dict[str, Any]]) -> LLMResult: ...


class AnthropicLLM:
    def __init__(self, model: str = MODEL, effort: str = EFFORT):
        import anthropic

        # The SDK default is a 10-minute timeout; one hung request in the first eval
        # took 611 s. A chat answer that slow is a failure anyway.
        self.client = anthropic.Anthropic(timeout=60.0, max_retries=2)
        self.model, self.effort = model, effort
        self.name = f"anthropic:{model}"

    def answer(self, system: str, messages: List[Dict[str, Any]]) -> LLMResult:
        resp = self.client.beta.messages.create(
            model=self.model,
            max_tokens=8000,
            # The system prompt is identical on every request, so it is the cache prefix.
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=messages,
            output_config={"effort": self.effort},
            # If a safety classifier declines, the API retries on a fallback model in the same call.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        parts: List[TextPart] = []
        for block in resp.content:
            if block.type != "text":
                continue
            cites = [
                Citation(c.search_result_index, c.cited_text, c.source, c.title)
                for c in (block.citations or [])
                if c.type == "search_result_location"
            ]
            parts.append(TextPart(block.text, cites))
        u = resp.usage
        usage = {
            "input_tokens": u.input_tokens,
            "output_tokens": u.output_tokens,
            "cache_creation_input_tokens": u.cache_creation_input_tokens or 0,
            "cache_read_input_tokens": u.cache_read_input_tokens or 0,
        }
        return LLMResult(parts, resp.stop_reason or "", resp.model, usage, resp._request_id)


class FakeLLM:
    """Extractive answers built from the retrieved blocks, cited the same way
    Claude cites them. Good enough to exercise every code path offline."""

    name = "fake:extractive"

    def answer(self, system: str, messages: List[Dict[str, Any]]) -> LLMResult:
        content = messages[-1]["content"]
        results = [b for b in content if isinstance(b, dict) and b.get("type") == "search_result"]
        if not results:
            return LLMResult([TextPart("NOT_IN_SOURCES")], "end_turn", self.name, {})
        parts = [TextPart("Offline demo answer (no model call). The most relevant policy language is: ")]
        for i, r in enumerate(results[:2]):
            block = r["content"][0]["text"]
            parts.append(TextPart(block, [Citation(i, block, r["source"], r["title"])]))
            parts.append(TextPart(" "))
        return LLMResult(parts, "end_turn", self.name, {})


def default_llm() -> LLM:
    backend = os.getenv("COPILOT_LLM", "auto")
    has_creds = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))
    if backend == "anthropic" or (backend == "auto" and has_creds):
        return AnthropicLLM()
    return FakeLLM()
