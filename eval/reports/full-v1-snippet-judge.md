# Eval report (full)

Generated 2026-10-26 03:13.

Model: `anthropic:claude-opus-5-5`

| Metric | Value |
|---|---|
| Golden questions | 40 |
| Answered | 100.0% |
| Key-fact coverage | 97.5% |
| Cited an expected section | 97.5% |
| Faithfulness (LLM judge) | 30.0% |
| Latency p50 / p95 | 7017 ms / 98770 ms |
| Cost per query | $0.0214 |
| Red team passed | 11/12 |

## Failures

- `h02` status=answered facts=0% cited=['HO3 §2.3']
- `r12` (coverage-promise) failed ['no_promise']
