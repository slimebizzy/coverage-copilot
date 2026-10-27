# Eval report (full)

Generated 2026-10-26 20:03.

Model: `anthropic:claude-opus-5-5`

| Metric | Value |
|---|---|
| Golden questions | 48 |
| Answered | 100.0% |
| Key-fact coverage | 97.9% |
| Cited an expected section | 97.9% |
| Faithfulness (LLM judge) | 85.4% |
| Answers with no dropped conditions (LLM judge) | 91.7% |
| Answers where the condition guard added an eligibility condition | 4 |
| Latency p50 / p95 | 7973 ms / 12322 ms |
| Cost per query | $0.0238 |
| Red team passed | 12/12 |

## Failures

- `h02` status=answered facts=0% cited=['HO3 §2.3']
- `g09` guard added: covered_peril_mold
- `g21` guard added: total_theft
- `c03` guard added: covered_peril_mold
- `c06` guard added: total_theft
- `g16` dropped condition: "We will pay only that part of the total of all loss payable that exceeds the deductible amount shown in the Declarations" — omits that a separate windstorm or hail deductible may apply if shown by endorsement, and the 'unless otherwise noted in this policy' qualifier
- `g30` dropped condition: "full repair or replacement cost is paid only if... 80% or more" — omits that payment is up to the limit of liability and no more than actual cash value until actual repair or replacement is complete
- `c05` dropped condition: "replacement cost applies only if the roof surfacing is 15 years old or less": omits that the age rule applies only to loss to roof surfacing caused by windstorm or hail.
- `h01` dropped condition: "Your payment is reduced by your deductible. The policy pays only that part of the total of all loss payable that exceeds the deductible amount shown in the Declarations." leaves out the source's qualifier that this deductible provision applies "unless otherwise noted in this policy".
- `g06` unsupported: Actual cash value generally accounts for the roof's age and wear, so a roof over 15 years old would typically receive less.
- `g13` unsupported: The answer says the policy covers "sudden physical damage to your home and other structures." Source [1] says "direct physical loss" and says nothing about it having to be sudden.
- `g14` unsupported: No state endorsement applies here, so this is the base policy language. The sources are marked jurisdiction ALL, but nothing in them says that no state endorsement applies to this claim.
- `g32` unsupported: No state-specific guideline applies since no location was given. The sources show only that UWG §1.3 is jurisdiction ALL. They say nothing about whether any state-specific guidelines exist or apply.
- `c01` unsupported: Your Coverage C limit is on your Declarations page (no source mentions the Declarations page).
- `c01` unsupported: For anything you claim beyond the advance, the standard inventory requirement still applies (the sources do not say how the advance interacts with the inventory duty for amounts beyond it).
- `c05` unsupported: Actual cash value generally means depreciation is taken into account. (The sources do not define actual cash value.)
- `h02` unsupported: Many homeowners policies set a separate, smaller limit for theft of firearms.
- `h02` unsupported: Coverage A is the coverage on your home itself.
