# Eval report (retrieval)

Generated 2026-10-26 01:24.

Corpus: 84 chunks. Top-k = 6. No-answer gate: top BM25 score < 4.0.

| Metric | Value |
|---|---|
| Golden questions | 32 |
| Recall@6 (expected sections retrieved) | 100.0% |
| MRR | 0.927 |
| Answerable questions wrongly gated as not-found | 0 |
| Red team: access control, jurisdiction and PII checks passed | 12/12 |
| Red team: refusals stopped before any model call | 4/5 |

## Retrieval misses

None.

## Held-out set (never used for tuning)

Recall@6 87.5%, MRR 0.708, wrongly gated 0 of 8.

- `h02` Someone stole my guns from the house. What's the limit? expected ['HO3 §2.4'], got ['HO3 §2.3', 'PAP §2.5', 'PAP §2.4', 'PAP §7.3']
