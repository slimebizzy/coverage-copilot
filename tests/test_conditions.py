from app.conditions import RULES, enforce, rules_by_chunk
from app.ingest import load_corpus
from app.llm import Citation, LLMResult, TextPart
from app.pipeline import Pipeline

CHUNKS = {c.chunk_id: c for c in load_corpus()}
CONTENTS_ADVANCE = CHUNKS["CA-HO-AE §2.1"].blocks[0]
WEAR_AND_TEAR = next(b for b in CHUNKS["HO3 §4.1"].blocks if b.startswith("- Wear and tear"))
FROZEN = next(b for b in CHUNKS["HO3 §4.1"].blocks if b.startswith("- Freezing"))


def seg(text, cited=()):
    return {"text": text, "refs": [1] if cited else [], "cited": list(cited)}


def test_every_rule_matches_some_policy_text():
    matched = {r.name for rules in rules_by_chunk(list(CHUNKS.values())).values() for r in rules}
    assert matched == {r.name for r in RULES}


def test_g03_failure_gets_the_condition_appended():
    # The run-1 g03 answer: a related-benefits bullet that dropped the condition.
    segs = [seg("**Related protections**\n- If your home is a total loss, "),
            seg("we will offer a payment of no less than 30% of the Coverage C limit.", [CONTENTS_ADVANCE])]
    flags = enforce(segs)
    assert flags == ["condition_added:state_of_emergency"]
    assert segs[1]["conditions"] == ["Applies only to a loss relating to a declared state of emergency."]


def test_condition_in_the_same_line_is_left_alone():
    segs = [seg("- After a total loss relating to a declared state of emergency, "),
            seg("we will offer a payment of no less than 30%.", [CONTENTS_ADVANCE])]
    assert enforce(segs) == []


def test_condition_in_a_scoping_heading_counts():
    segs = [seg("**If a state of emergency is declared:**\n- Contents: "),
            seg("no less than 30% without an inventory.", [CONTENTS_ADVANCE])]
    assert enforce(segs) == []


def test_condition_in_an_unrelated_paragraph_does_not_count():
    segs = [seg("A state of emergency may extend your hotel coverage.\n- Contents: "),
            seg("no less than 30% without an inventory.", [CONTENTS_ADVANCE])]
    assert enforce(segs) == ["condition_added:state_of_emergency"]


def test_unconditional_bullet_in_a_conditional_section_is_untouched():
    segs = [seg("Wear and tear isn't covered: ", [WEAR_AND_TEAR])]
    assert enforce(segs) == []
    segs = [seg("Frozen pipes while you're away aren't covered. ", [FROZEN])]
    assert enforce(segs) == ["condition_added:frozen_pipes_care"]


class OneAnswer:
    name = "scripted"

    def answer(self, system, messages):
        return LLMResult([TextPart("You can get at least 30% of your contents limit with no inventory.",
                                   [Citation(0, CONTENTS_ADVANCE, "CA-HO-AE §2.1", "t")])],
                         "end_turn", "claude-opus-5-5", {})


def test_pipeline_applies_the_guard_and_flags_it():
    a = Pipeline(llm=OneAnswer(), trace_path=None).ask(
        "If my house burns down, do I have to list every item I lost?", "policyholder", "CA")
    assert a.status == "answered"
    assert "declared state of emergency" in a.answer
    assert "condition_added:state_of_emergency" in a.flags
    assert a.segments[0]["conditions"] == ["Applies only to a loss relating to a declared state of emergency."]
    assert a.answer.endswith("[Applies only to a loss relating to a declared state of emergency.]")
    assert all("cited" not in s for s in a.segments)


def test_sibling_bullet_does_not_scope_by_design():
    # Accepting sibling bullets would also accept the run-1 g03 failure, where a
    # sibling stated the condition for a different benefit.
    segs = [seg("**Related help**\n- Hotel: 24 months relating to a declared state of emergency.\n- Belongings: "),
            seg("we will offer a payment of no less than 30% of the Coverage C limit without an itemized inventory.",
                [CONTENTS_ADVANCE])]
    assert enforce(segs) == ["condition_added:state_of_emergency"]


# Interventions from the first 3 live runs that were wrong or redundant.
RENTAL = CHUNKS["PAP §5.3"].blocks[0]
MOLD = CHUNKS["HO3 §3.4"].blocks[0]


def test_rental_reimbursement_sentence_does_not_get_the_theft_condition():
    segs = [seg("- If you bought it: ", []),
            seg("If a Rental Reimbursement endorsement is shown in the Declarations, its daily and maximum "
                "limits apply instead.", [RENTAL])]
    assert enforce(segs) == []


def test_mold_cap_sentence_does_not_get_the_covered_peril_condition():
    segs = [seg("- That $10,000 is the most we will pay regardless of the number of locations or claims "
                "during the policy period.", [MOLD])]
    assert enforce(segs) == []


def test_mold_benefit_sentence_still_needs_its_condition():
    segs = [seg("- We will pay up to $10,000 in total for direct physical loss caused by fungi, mold, "
                "wet or dry rot, or bacteria.", [MOLD])]
    assert enforce(segs) == ["condition_added:covered_peril_mold"]


def test_a_condition_is_added_once_per_line():
    segs = [seg("- In addition to our limit of liability, we will pay up to $20 per day", [RENTAL]),
            seg(" and without application of a deductible, up to a maximum of $600.", [RENTAL])]
    assert enforce(segs) == ["condition_added:total_theft"]
