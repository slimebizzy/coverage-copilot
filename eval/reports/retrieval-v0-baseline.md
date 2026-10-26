# Eval report (retrieval)

Generated 2026-10-26 01:23.

Corpus: 84 chunks. Top-k = 6. No-answer gate: top BM25 score < 4.0.

| Metric | Value |
|---|---|
| Golden questions | 32 |
| Recall@6 (expected sections retrieved) | 90.6% |
| MRR | 0.789 |
| Answerable questions wrongly gated as not-found | 3 |
| Red team: access control, jurisdiction and PII checks passed | 12/12 |
| Red team: refusals stopped before any model call | 4/5 |

## Retrieval misses

- `g08` Does my homeowners policy cover earthquakes? expected ['HO3 §5.1'], got ['HO3 §5.5', 'HO3 §3.2', 'HO3 §5.3', 'HO3 §5.1'] (gated)
- `g11` How much cash is covered if it's destroyed in a fire? expected ['HO3 §2.4'], got ['HO3 §5.1', 'HO3 §3.3', 'HO3 §1.3', 'HO3 §2.3']
- `g13` A pipe has been slowly leaking under my sink for a month. Am I covered? expected ['HO3 §4.1'], got ['HO3 §3.4', 'PAP §7.3', 'HO3 §2.5', 'HO3 §6.6']
- `g16` I disagree with the adjuster's estimate. What can I do? expected ['HO3 §6.5'], got ['HO3 §2.3', 'PAP §2.4', 'PAP §7.3'] (gated)
- `g24` Someone hit my car and drove off. What do I need to do? expected ['PAP §4.2'], got ['PAP §2.4', 'HO3 §5.5', 'PAP §4.2', 'PAP §7.1'] (gated)
