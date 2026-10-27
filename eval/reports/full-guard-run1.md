# Eval report (full)

Generated 2026-10-26 20:03.

Model: `anthropic:claude-opus-5-5`

| Metric | Value |
|---|---|
| Golden questions | 48 |
| Answered | 97.9% |
| Key-fact coverage | 97.9% |
| Cited an expected section | 97.9% |
| Faithfulness (LLM judge) | 87.2% |
| Answers with no dropped conditions (LLM judge) | 93.6% |
| Answers where the condition guard added an eligibility condition | 5 |
| Latency p50 / p95 | 7794 ms / 12249 ms |
| Cost per query | $0.0237 |
| Red team passed | 12/12 |

## Failures

- `h02` status=not_found facts=0% cited=[]
- `g03` guard added: state_of_emergency
- `g09` guard added: covered_peril_mold
- `g21` guard added: total_theft
- `c03` guard added: covered_peril_mold
- `c06` guard added: total_theft
- `g02` dropped condition: Opening summary: "with a possible extension to 36 months" leaves out the conditions that you act in good faith and with reasonable diligence and encounter reconstruction delays beyond your control (CA Endorsement §1.1).
- `g16` dropped condition: "The company will pay only that part of the total of all loss payable that exceeds the deductible amount shown in the Declarations" omits the source condition "Unless otherwise noted in this policy".
- `c01` dropped condition: "If your home is a total loss relating to a declared state of emergency ... you can get an advance on your belongings without an itemized list" leaves out the condition that the total loss must be a covered loss.
- `g06` unsupported: Describing HO-3 Section 6.3 as 'the base policy's replacement cost provision': source [3] only says roofs 15 years old or less are settled under HO-3 Section 6.3 and does not say what that section provides.
- `g17` unsupported: The policy's claim requirements in that section include 'its duties after a loss'. Source [1] refers only to 'all of the terms under this Section', and no source identifies those terms as duties after a loss.
- `g22` unsupported: Your comprehensive deductible may be different from your collision deductible. The sources mention only 'any applicable deductible shown in the Declarations' and do not describe separate comprehensive and collision deductibles.
- `c01` unsupported: Your Coverage C limit is shown on your Declarations page.
- `c07` unsupported: Actual cash value generally means the value after depreciation (the sources do not define actual cash value).
- `h08` unsupported: Appraisal "does not resolve coverage disputes" — no source addresses whether appraisal resolves coverage disputes.
- `h08` unsupported: "No state endorsement applies here, so the base HO-3 timeframe governs" — no source addresses state endorsements or their applicability.
