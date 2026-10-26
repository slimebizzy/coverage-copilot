# Eval report (full)

Generated 2026-10-26 11:45.

Model: `anthropic:claude-opus-5-5`

| Metric | Value |
|---|---|
| Golden questions | 40 |
| Answered | 100.0% |
| Key-fact coverage | 97.5% |
| Cited an expected section | 97.5% |
| Faithfulness (LLM judge) | 77.5% |
| Answers with no dropped conditions (LLM judge) | 95.0% |
| Latency p50 / p95 | 7017 ms / 98770 ms |
| Cost per query | $0.0214 |
| Red team passed | 12/12 |

## Failures

- `h02` status=answered facts=0% cited=['HO3 §2.3']
- `g02` dropped condition: "In California, the two-week civil authority limit in HO-3 Section 2.5 is replaced with a limit of four weeks" — the sources limit civil authority coverage to cases where access is prohibited because of direct damage to neighboring premises by a covered peril. The answer says only that nearby properties were damaged and omits the covered-peril requirement.
- `g02` dropped condition: "We will grant an extension of up to 12 additional months, for a total of 36 months, if you act in good faith..." — this bullet stands on its own, separate from the emergency bullet. It omits that the extension applies only to a loss relating to a state of emergency declared by the Governor.
- `g03` dropped condition: "If your home is a total loss, we will offer a payment under Coverage C of no less than 30% of the Coverage C limit, up to $250,000, without requiring an itemized inventory." — omits that the total loss must be a covered total loss relating to a declared state of emergency (Source [2]).
- `g02` unsupported: Coverage A is your dwelling coverage, and you can find its amount on your Declarations page. (The sources do not define Coverage A or say where its amount appears.)
- `g06` unsupported: Actual cash value accounts for depreciation, so the payment for an older roof would be lower. (The sources do not define actual cash value or mention depreciation.)
- `g14` unsupported: Some states change these rules through endorsements. (The sources do not mention state endorsements; all cited sections are listed as jurisdiction ALL.)
- `g24` unsupported: "If you or anyone in your car was hurt, this is the coverage that applies." The sources limit payment to bodily injury sustained by an insured and never define who counts as an insured, so they do not support coverage for anyone in the car.
- `g30` unsupported: "No state endorsement applies here": the sources do not address whether any state endorsement exists or applies. They only show that the cited sections are jurisdiction ALL.
- `g31` unsupported: Screen for these before you consider the referral thresholds (the sources specify no order for checking ineligibility versus referral thresholds)
- `h01` unsupported: Give prompt notice to us or our agent.
- `h01` unsupported: Protect the property from further damage and make reasonable and necessary repairs to protect it.
- `h01` unsupported: Prepare an inventory of damaged personal property showing the quantity, description, actual cash value and amount of loss, with bills, receipts and related documents.
- `h01` unsupported: Send to us, within 60 days after our request, your signed, sworn proof of loss.
- `h03` unsupported: Wind or hail are given as examples of covered perils for the roof damage; the sources do not list any covered perils.
- `h03` unsupported: The advice to take photos and avoid permanent repairs until the damage has been documented is not in the HO-3 sources, which only require showing the damaged property as often as reasonably required.
- `h08` unsupported: No state endorsement applies here, so this is based on the base HO-3 form. (The sources do not establish whether any state endorsement applies.)
