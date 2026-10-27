# Eval report (full)

Generated 2026-10-26 20:21.

Model: `anthropic:claude-opus-5-5`

| Metric | Value |
|---|---|
| Golden questions | 48 |
| Answered | 97.9% |
| Key-fact coverage | 97.9% |
| Cited an expected section | 97.9% |
| Faithfulness (LLM judge) | 87.2% |
| Answers with no dropped conditions (LLM judge) | 89.4% |
| Answers where the condition guard added an eligibility condition | 0 |
| Latency p50 / p95 | 7604 ms / 11922 ms |
| Cost per query | $0.0238 |
| Red team passed | 12/12 |

## Failures

- `h02` status=not_found facts=0% cited=[]
- `g04` dropped condition: "Cosmetic roof damage is not covered." — omits that the exclusion applies only to cosmetic damage to roof surfacing caused by hail (heading states it broadly for any cosmetic roof damage)
- `g05` dropped condition: "Your deductible would be $6,000 for a loss caused by windstorm or hail" leaves out the conditions in that sentence that the Coverage A limit is $300,000 and that the Declarations show a 2% windstorm or hail deductible. They appear only in the next sentence.
- `g16` dropped condition: "we will pay only that part of the total of all loss payable that exceeds the deductible amount shown in the Declarations" omits the source's qualifier "Unless otherwise noted in this policy"
- `c08` dropped condition: "The exception is a declared catastrophe where the claim involves no suspected fraud." — omits that the raised authority applies only to windstorm and hail claims
- `h07` dropped condition: "You may make a claim on an actual cash value basis and then make a claim for any additional replacement cost within 180 days after the loss" omits the Texas endorsement §2.2 exception: hail or windstorm loss to roof surfacing more than 15 years old is settled at actual cash value, not replacement cost.
- `g02` unsupported: Your Coverage A (dwelling) limit is shown on your Declarations page.
- `g07` unsupported: Whether you have the water backup endorsement, and its limit, would be shown on your policy's Declarations page (the sources do not mention the Declarations page).
- `g11` unsupported: The answer says the 10%/$1,000 limit applies to cash kept at 'another residence you own.' The source says 'an insured's residence other than the residence premises' and does not require ownership.
- `g23` unsupported: Physical Damage coverage pays for damage to your own car. (The sources do not define Physical Damage coverage.)
- `g23` unsupported: The 14 days count from the date you became the owner, not from when you picked up the car or registered it. (The sources do not address pickup or registration dates.)
- `g23` unsupported: For an additional car, coverage starts on the date you become the owner, but only if you contact us within that 14-day window. (The source does not make the start of coverage conditional on contacting the insurer within 14 days.)
- `c05` unsupported: Actual cash value takes depreciation (wear and age) into account, so the payment would typically be less than the cost of a new roof. The sources do not define actual cash value or describe how it is calculated.
- `h08` unsupported: No state endorsement applies here, so the base HO-3 20-day window governs. The sources do not address state endorsements or whether any apply.
