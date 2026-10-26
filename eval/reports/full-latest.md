# Eval report (full)

Generated 2026-10-26 11:55.

Model: `anthropic:claude-opus-5-5`

| Metric | Value |
|---|---|
| Golden questions | 48 |
| Answered | 97.9% |
| Key-fact coverage | 97.9% |
| Cited an expected section | 97.9% |
| Faithfulness (LLM judge) | 89.4% |
| Answers with no dropped conditions (LLM judge) | 89.4% |
| Latency p50 / p95 | 7781 ms / 13998 ms |
| Cost per query | $0.0233 |
| Red team passed | 12/12 |

## Failures

- `h02` status=not_found facts=0% cited=[]
- `g02` dropped condition: "with a possible extension to 36 months" (opening summary): drops the condition that you act in good faith and with reasonable diligence and encounter reconstruction delays beyond your control.
- `g13` dropped condition: "any lawsuit must be started within two years after the date of loss" omits the condition that no action can be brought unless there has been full compliance with all of the policy terms under this Section (§6.6).
- `c06` dropped condition: "The policy will pay up to $20 per day, to a maximum of $600, for temporary transportation expenses" — the bullet leaves out that, if a Rental Reimbursement endorsement is shown in the Declarations, that endorsement's daily and maximum limits apply instead. This appears only in a later section.
- `c06` dropped condition: "The policy will pay up to $20 per day, to a maximum of $600 ... because of the total theft of your covered auto" — the bullet leaves out that only expenses incurred from 48 hours after the theft until the auto is returned or its loss is paid are covered. This appears only in a separate bullet.
- `h01` dropped condition: "Your deductible applies. We will pay only that part of the total of all loss payable that exceeds the deductible amount shown in the Declarations." — omits "unless otherwise noted in this policy" and that a separate windstorm or hail deductible may apply if shown by endorsement
- `h07` dropped condition: "the replacement cost claim lets you recover the rest": drops the conditions that the insurer pays no more than actual cash value until actual repair or replacement is complete, and that full replacement cost applies only if the insurance is 80% or more of full replacement cost.
- `g02` unsupported: Your Coverage A (dwelling) limit is on your Declarations page (no source says where the Coverage A limit appears).
- `g05` unsupported: Losses from other causes, such as fire, use your regular policy deductible. (The sources say only that the windstorm or hail deductible replaces the HO-3 §6.1 deductible for wind or hail losses. They do not state which deductible applies to fire or other perils.)
- `g06` unsupported: Actual cash value generally means depreciation is taken into account.
- `g06` unsupported: The wind/hail deductible is 'usually a percentage of your dwelling limit'; the sources only give a 2% example and do not say this is usual.
- `g07` unsupported: Your Declarations page shows whether you have the water backup endorsement (the sources do not mention the Declarations page for this endorsement).
- `h07` unsupported: Actual cash value is the depreciated value, so the replacement cost claim lets you recover the rest. (The sources do not define actual cash value or say the replacement cost claim recovers the full difference.)
