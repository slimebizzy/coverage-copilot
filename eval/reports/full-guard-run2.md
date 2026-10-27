# Eval report (full)

Generated 2026-10-26 20:03.

Model: `anthropic:claude-opus-5-5`

| Metric | Value |
|---|---|
| Golden questions | 48 |
| Answered | 100.0% |
| Key-fact coverage | 97.9% |
| Cited an expected section | 97.9% |
| Faithfulness (LLM judge) | 83.3% |
| Answers with no dropped conditions (LLM judge) | 95.8% |
| Answers where the condition guard added an eligibility condition | 2 |
| Latency p50 / p95 | 8029 ms / 11550 ms |
| Cost per query | $0.0240 |
| Red team passed | 12/12 |

## Failures

- `h02` status=answered facts=0% cited=['HO3 §2.3']
- `g09` guard added: covered_peril_mold
- `g21` guard added: total_theft, total_theft, total_theft
- `g03` dropped condition: "we will offer a payment under Coverage C of no less than 30% of the Coverage C limit, up to $250,000, without requiring an itemized inventory" omits the condition that the total loss of the dwelling must be a covered loss (source §2.1: 'covered total loss of the dwelling').
- `h01` dropped condition: "We will pay only that part of the total of all loss payable that exceeds the deductible amount shown in the Declarations." — omits the source's 'Unless otherwise noted in this policy' qualifier and that a separate windstorm or hail deductible may apply if shown by endorsement
- `g01` unsupported: Coverage A is the dwelling limit shown on your Declarations page (the sources do not define Coverage A or say where its limit appears).
- `g02` unsupported: Your Coverage A (dwelling) limit is shown on your Declarations page.
- `g06` unsupported: Actual cash value accounts for depreciation, so it's typically less than the cost of a new roof.
- `g06` unsupported: Your hail deductible is a percentage of your dwelling coverage, as shown on your Declarations page. (The sources give this only as an example, not as a general rule for how the deductible is set.)
- `g31` unsupported: "Referral thresholds apply to otherwise eligible risks" (and the instruction to check eligibility first): neither UWG §3.1 nor §1.3 states that referral thresholds apply only to eligible risks or that eligibility must be checked before referral.
- `c01` unsupported: Your Coverage C limit is shown on your Declarations page.
- `c01` unsupported: Beyond that amount, you should expect the standard inventory requirement to apply (the sources do not say how the remainder of a belongings claim is handled after the advance).
- `c07` unsupported: Actual cash value is the depreciated value.
- `h02` unsupported: Coverage A is the limit on your house itself (the sources never define Coverage A).
- `h02` unsupported: Many homeowners policies set a separate, lower dollar limit for stolen guns (not in the sources).
- `h08` unsupported: No state endorsement applies here, so these are the base HO-3 and internal guideline timelines. The sources are marked jurisdiction ALL but say nothing about whether any state endorsement applies.
