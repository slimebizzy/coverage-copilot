# Coverage Copilot

A policy Q&A assistant for a regulated domain (insurance). Every answer cites the exact policy section it comes from. It respects who is asking (policyholder, adjuster or underwriter) and where the property is (state endorsements). It refuses rather than guesses.

Built on the Claude API: search-result content blocks with native citations, prompt caching, and server-side refusal fallback. Retrieval, access control and guardrails are deterministic Python that you can test without a model.

> All policy documents in `corpus/` are fictional ("Cobalt Harbor Mutual"). They were written for this project and are not real contracts or statements of state law.

---

## The problem

Claims adjusters and policyholders ask the same questions all day: *"How long will you pay for a hotel?"*, *"What's my hail deductible?"*, *"Am I covered driving for Uber?"* The answers are in 40-page policy forms and in state endorsements that quietly change those forms. Three things make this harder than a demo chatbot:

1. **A wrong answer is a liability.** An unsupported "yes, you're covered" can become a bad-faith claim. Every statement must trace back to policy language.
2. **Not everyone may see everything.** Internal reserve-authority tables and fraud (SIU) indicators must never reach a policyholder, through retrieval, the model, or a citation.
3. **Jurisdiction changes the answer.** The base HO-3 form says Additional Living Expense stops at 12 months. In California, after a declared wildfire emergency, the endorsement says 24 (up to 36). Retrieving only the base form gives a confidently wrong answer.

## What it does

| Capability | How |
|---|---|
| Cited answers | Retrieved sections go to Claude as `search_result` blocks with `citations: {enabled: true}`. Each paragraph and bullet is its own block, so a citation points at the single bullet that matters. |
| Citation enforcement | The answer is rejected (`unsupported`) if it has no citations. A citation to a section the user wasn't shown is dropped and flagged. |
| Role-based access | Chunks carry `roles` metadata. They are filtered **before** scoring, so restricted text never enters the ranking, the prompt, or the response. |
| Jurisdiction | Chunks carry a `jurisdiction`. When a base-form section is retrieved, any state endorsement that amends it (parsed from "HO-3 Section 2.5" references) is attached to it, for that state only. |
| Abstention | If the top retrieval score is below a threshold, it answers "not found" **without a model call**. The model also has `NOT_IN_SOURCES` / `OUT_OF_SCOPE` sentinels. |
| Guardrails | PII redaction (SSN, email, phone, Luhn-checked cards) on input, output, and traces. Prompt-injection patterns are blocked before retrieval. Policyholder answers get a fixed "not a coverage decision" note added by code, not by the model. |
| Observability | Every request writes a JSONL trace: retrieved ids, cited ids, status, flags, per-stage latency, tokens, cache hits, and cost. `/api/stats` rolls these up. |
| Offline mode | Without an API key, an extractive stand-in model exercises the same code path. Anyone can clone and click around. |

## Architecture

```
question + role + state
   │
   ▼
input guard ── PII redaction, injection block ──► "blocked" (no retrieval, no model)
   │
   ▼
access filter (role, jurisdiction)  ◄── done BEFORE scoring
   │
   ▼
BM25 over section chunks + insurance query expansion ("Uber" → "transportation network")
   │
   ▼
endorsement linking (HO3 §2.5 retrieved in CA → CA-HO-AE §1.1 attached)
   │
   ▼
relevance gate ── top score < 4.0 ──► "not_found" (no model call, $0)
   │
   ▼
Claude (claude-opus-5-5, effort=medium)
  system prompt (cached) + search_result blocks (citations on) + question
   │
   ▼
verify ── refusal? sentinel? zero citations? citation outside context? output PII?
   │
   ▼
numbered answer + sources + trace
```

Code map: `app/ingest.py` (chunking, metadata, endorsement links) · `app/retrieval.py` (access filter, BM25, query expansion) · `app/guardrails.py` · `app/llm.py` (Claude + offline backend, cost) · `app/pipeline.py` (request path, verification, tracing) · `app/server.py` (FastAPI + UI) · `eval/` (golden set, held-out set, red team, runner).

## Results

### Retrieval (free to run: `make eval`)

| | Golden set (32 original questions; 40 with condition probes) | Held-out set (8 questions, never tuned on) |
|---|---|---|
| Recall@6, v0 (plain BM25) | 90.6% | n/a |
| Recall@6, v1 (query expansion + stemming fix) | **100%** | **87.5%** |
| MRR, v0 → v1 | 0.789 → **0.927** (0.929 on all 40) | 0.708 |
| Answerable questions wrongly gated as "not found", v0 → v1 | 3 → **0** | 0 |

How v0 became v1: the eval listed five misses. Each was a vocabulary gap ("drove off" vs. *hit-and-run*, "leaking under my sink" vs. *continuous seepage*, "disagree with the estimate" vs. *appraisal*). One was a stemmer bug that turned "earthquakes" into "earthquak". The fix was a domain synonym table plus the stemmer repair, each traced to a specific failing question (`eval/reports/retrieval-v0-baseline.md`).

The 8 condition probes added later missed twice on first try ("froze" vs. *freezing*, "list every item" vs. *itemized inventory*), so the same fix was applied; all 40 are now retrieved. The held-out number keeps this honest. The expansions were tuned on the golden set, so 100% there is optimistic. 87.5% on unseen phrasings is the number I'd quote to a customer. The one held-out miss ("stole my guns" vs. *firearms*) is exactly the failure dense embeddings fix, which is on the roadmap.

### Red team (12 attacks)

12/12 pass the deterministic checks (no restricted section retrieved, no wrong-state endorsement, PII redacted). Attacks include role-claim escalation ("I am an adjuster, so show me…"), prompt injection, off-domain requests, jurisdiction confusion and coverage-promise baiting. 4 of the 5 refusal cases stop before any model call. The fifth (pet vet bills) shares enough vocabulary with the policy to pass the gate, so the model's `NOT_IN_SOURCES` path handles it.

### End-to-end with Claude (`make eval-full`)

48 questions (40 golden including 8 condition probes, plus 8 held-out) and 12 attacks against `claude-opus-5-5` at effort `medium`, **run 3 times** to check stability, then once more after fixing the guard (run 4). Reports: [`run1`](eval/reports/full-guard-run1.md), [`run2`](eval/reports/full-guard-run2.md), [`run3`](eval/reports/full-guard-run3.md), [`run4`](eval/reports/full-guard-v2-run1.md).

| Metric | Run 1 | Run 2 | Run 3 | Run 4 (sentence-level guard) |
|---|---|---|---|---|
| Answered with citations (rest correctly said "not found") | 47/48 | 48/48 | 48/48 | 47/48 |
| Key-fact coverage | 97.9% | 97.9% | 97.9% | 97.9% |
| Cited an expected section | 97.9% | 97.9% | 97.9% | 97.9% |
| Faithfulness (LLM judge) | 87.2% | 83.3% | 85.4% | 87.2% |
| Answers with no dropped conditions of any kind (LLM judge) | 93.6% | 95.8% | 91.7% | 89.4% |
| Eligibility conditions missing from final answers (judge flags, checked by hand) | **0** | **0** | **0** | **0** |
| Guard interventions (all false positives in runs 1–3) | 5 | 2 | 4 | **0** |
| Red team passed | **12/12** | **12/12** | **12/12** | **12/12** |
| Latency p50 / p90 / max | 7.8 / 11.3 / 14.8 s | 8.0 / 11.4 / 13.7 s | 8.0 / 12.1 / 16.1 s | 7.6 / 11.8 / 14.1 s |
| Cost per query | $0.024 | $0.024 | $0.024 | $0.024 |
| Input tokens served from prompt cache | 45% | 45% | 45% | 44% |

The deterministic metrics are identical across runs. The LLM-judge metrics move by about ±3–4 points, the same as grading the same answers twice, so read differences that small as noise. The one key-fact miss in every run is h02 (firearms), the known held-out retrieval miss. The model says the limit isn't in the sections it has instead of guessing.

#### Run 3: a deterministic condition guard

The prompt fix in Run 2 made dropped conditions less likely; it can't make them impossible. So [`app/conditions.py`](app/conditions.py) adds a guard in code: a registry of 8 conditions that decide eligibility (declared state of emergency, declared catastrophe, suspected fraud, mold from a covered peril, total theft, ride-share endorsement, frozen-pipe care, roof age). When an answer line cites policy text carrying one of them, the line, or a heading scoping it, must state the condition. If it doesn't, the pipeline appends it and records `condition_added:<rule>` in the trace.

What 3 × 48 live answers showed:

- **The tightened prompt held.** Across 144 answers the judge found **no** dropped eligibility condition. The remaining judge flags are secondary qualifiers ("unless otherwise noted" on the deductible, "covered" before "total loss").
- **So every guard intervention was noise.** It stepped in on 11 answers (12 lines). 5 attached "applies only when your car has been stolen" to the Rental Reimbursement sentence, which is misleading on a crash question (c06). 5 repeated the mold condition next to the $10,000 cap sentence. 2 were redundant. The cause: citations point at whole paragraphs, and the guard matched rules against the paragraph, not the sentence the answer used.
- **Fixed after the runs, in code and tests.** The guard now matches against the cited sentence the answer actually uses (best word overlap, falling back to the whole paragraph when the answer paraphrases). It adds each condition at most once per line. The rental, mold-cap and duplicate cases from the live runs are now regression tests, and the g03 failure is still caught.
- **Run 4 confirmed the fix live:** 0 interventions, down from 2–5 per run, with no eligibility condition dropped and every other metric unchanged. The flip side: a run with no drops can't show a live *catch*. That's covered by the replayed g03 failure in [`tests/test_conditions.py`](tests/test_conditions.py), not by a live run.
- **A limit the guard can't see (h07, run 4).** Asked about Texas hail, the answer explained the base form's 180-day window to claim replacement cost. It cited HO-3 §6.3, but didn't mention that the Texas endorsement settles roofs over 15 years old at actual cash value. The guard only checks conditions inside the text an answer cites; a condition that lives in a *different* section that modifies it is out of its reach. That's the next roadmap item.
- **Two red-team flags were grader bugs.** r10's check flagged *"Nothing in the documents I can see supports 36 months in every state"* for containing "36 months". It now ignores negated sentences, like the coverage-promise check, and the saved answers were re-scored. The model behaved correctly in all 3 runs.

#### Run 2: the dropped-condition fix

Run 1 surfaced one material error (g03). The California contents advance was described as applying after any total loss, without its "declared state of emergency" condition. Three steps:

1. **Measured it properly.** I added 8 golden questions that probe conditions (c01–c08). On the old prompt, all 8 passed the key-fact check, because the condition words appear *somewhere* in each answer. A keyword check can't tell whether a condition is attached to the benefit it limits. So I added a `dropped_conditions` check to the LLM judge. Re-grading run 1's answers with it found 2 of 40 with a dropped condition (g02, g03), both missing "relating to a declared state of emergency."
2. **Tightened the prompt.** New rule: state the condition in the same sentence or bullet as the benefit, every time the benefit is mentioned, including in lists of related benefits.
3. **Re-ran everything.**

| | Run 1 (old prompt, 40 questions) | Run 2 (new prompt, 48 questions) |
|---|---|---|
| Benefits stated without their eligibility trigger (state of emergency, catastrophe, fraud) | 2 | **0** |
| Condition-probe questions with nothing dropped (c01–c08 + g03) | n/a | 8/9 |
| Answers with no dropped condition of any kind | 95.0% | 89.4% |
| Faithfulness | 77.5–82.5% (two gradings) | 89.4% |

**Honest read:** the specific failure is gone in this run. The broader dropped-condition rate didn't improve, though. The 5 answers flagged in run 2 leave out secondary qualifiers rather than eligibility triggers: the 48-hour waiting period on theft transportation (c06), "unless otherwise noted" on the deductible (h01), the full-compliance precondition on the suit deadline (g13). The eval set also grew, adding c06. A prompt is a soft control. For conditions that decide eligibility, the next step is a **deterministic check**: flag or annotate any cited sentence from a chunk that contains a registered condition phrase when the condition doesn't appear alongside it. The prompt run reports are kept as [`full-v2-old-prompt.md`](eval/reports/full-v2-old-prompt.md) (run 1 answers, re-graded) and `full-latest.md` (run 2).

#### Run 1: what the first run found, and what changed because of it

- **The grader was wrong before the model was.** The first judge pass scored faithfulness at 30%. Reading the flagged claims showed the judge only saw the snippets the model *cited*, not the full sections and titles it was *given*. It flagged "this is the Texas endorsement" as unsupported because the jurisdiction lives in the title. After the fix, the same saved answers scored 82.5% (`--rejudge` re-grades them without re-asking). The 30% report is kept as [`full-v1-snippet-judge.md`](eval/reports/full-v1-snippet-judge.md).
- **One red-team "failure" was a bad check.** The coverage-promise test matched "is approved" inside *"I can't confirm that your roof claim is approved."* That's the behavior we want. The check now looks at each sentence and skips negated ones.
- **The 7 remaining faithfulness flags, triaged by hand:**
  - **1 material error (g03).** The answer described the California contents advance as applying to any total loss and dropped the "declared state of emergency" condition. That's the kind of mistake that matters in a regulated product; see Run 2 above.
  - **1 unsupported advice (h03).** "Avoid permanent repairs until the damage is documented" sounds reasonable, but it isn't in the homeowners form.
  - **3 outside knowledge that is true but not retrieved (g02, g06, g31).** For example, "Coverage A is your dwelling coverage."
  - **2 judge artifacts (g30, h08).** The answer repeated the request's own context line, "no state endorsement applies."
- **Abstaining instead of guessing.** On the one held-out retrieval miss (h02, firearms), the model said the retrieved sections don't state a firearms limit instead of inventing one. It scores 0% on key facts, which is the correct failure mode.
- **Two hung requests.** One took 611 s and one 99 s, because the SDK's default timeout is 10 minutes. The client now uses a 60 s timeout with 2 retries; run 2's slowest request was 15.9 s.
- **Caching works but isn't the main cost lever.** The 1,293-token system prompt is cached after the first call (42% of input tokens served from cache). Most of the cost is output: answers average about 900 tokens. Shorter answers are the next cost lever.

## Interface: designed for trust

A chatbot that cites its sources is only useful if checking a source is easier than not checking it. The interface is built around that.

| Design problem | What the UI does |
|---|---|
| Citations people never click | Each claim carries a numbered chip. Hovering or focusing it previews the cited policy text; clicking opens the full section beside the answer (a bottom sheet on phones). |
| Citations point at whole paragraphs | The source panel highlights only the sentences the answer actually used, by word overlap with the lines that cite it. When nothing clearly matches, it marks the paragraph with a margin bar instead of pretending to be precise. |
| "Does my state change this?" | Endorsement sources carry a state badge and an "Amends HO-3 §2.5" badge. One click shows the standard policy's version under it. The `/api/section` endpoint applies the same role and state check as retrieval, so comparing can't leak a section. |
| Who can see what | The context bar shows the role and state the answer is for, and a documents popover lists what was searched and what wasn't ("Only for California properties", "Not available to policyholders"). Access control is visible, not just enforced. |
| Refusals that feel like errors | Each non-answer has its own state, with a plain reason: not in your documents, outside scope, blocked by the input check, held back for having no citations. "Held back" is a feature: the user sees that an uncheckable answer was withheld. |
| Conditions the model forgot | When the condition guard adds a condition, it appears as its own badge, not inline text. The badge says it was added by a policy check, so the user can tell the model's words from the guarantee. |
| Learning from mistakes | Thumbs up/down with an optional note is stored against the request's `trace_id` (`/api/feedback`). That's the "adjuster disagreed" rate from the deployment memo. |

Visual system: Young Serif for headings and policy text (documents should look like documents), Figtree for the interface, IBM Plex Mono for section numbers and metadata. Fog, sage and pine with an ochre highlighter; a deep-night dark theme. Built as one dependency-free HTML file with keyboard support, visible focus, `aria-live` answers, `prefers-reduced-motion`, and no horizontal scroll at 375 px. Answer markdown is rendered from a small, escaped subset; model output never reaches `innerHTML` unescaped.

## Design decisions and tradeoffs

- **Search-result blocks instead of "please cite [1]" prompting.** Native citations return the exact cited text and source id as structured data. That makes citation enforcement a code check, not a regex over prose.
- **Filter before scoring, not after.** Post-filtering top-k can let a restricted chunk influence ranking, or leak if someone later changes k. Pre-filtering makes the guarantee structural, and a parametrized test checks it for every role × state combination.
- **BM25 first, embeddings second.** On ~80 well-titled sections, BM25 plus a domain synonym table hit 100% / 87.5% recall with zero infrastructure and zero per-query cost. Adding a vector store before measuring would have been cargo cult. The held-out miss shows where it stops working.
- **A gate that skips the model.** Low-relevance questions return in about 1 ms for $0. That also removes a whole class of hallucinations: the model can't invent an answer from irrelevant context it never sees.
- **The disclaimer is code, not prompt.** Regulated wording shouldn't depend on the model remembering it.
- **Eligibility conditions are code, too.** The prompt asks the model to keep conditions next to benefits; `app/conditions.py` guarantees it for the conditions that decide eligibility. A guard that fires on correct answers is a cost, so its interventions are tracked per run and every false positive becomes a test.
- **Prompt caching, measured.** The system prompt carries a `cache_control` breakpoint, and traces record `cache_read_input_tokens`, so the hit rate is measured, not assumed. In the eval run, 42% of input tokens came from cache. Output length and the relevance gate (which skips the model entirely) move cost more.
- **Refusal fallback.** Requests use `fallbacks: "default"` (beta `server-side-fallback-2026-07-01`). If a safety classifier declines, the API retries on a fallback model within the same call, and a `refusal` stop reason is still handled explicitly.

## Run it

```bash
make setup                 # venv + dependencies (Python 3.9+)
cp .env.example .env       # add ANTHROPIC_API_KEY, or leave empty for offline mode
make run                   # http://localhost:8765
make test                  # 50 tests, no network
make eval                  # retrieval + red team, free
make eval-full             # end-to-end with Claude + LLM judge (about $1.50)
```

Try these in the UI: ask the California wildfire example, click source 2, then "Compare with the standard policy". Switch **Asking as** to Policyholder and ask for reserve authority; open the documents popover to see why the answer is "not in your documents".

API: `POST /api/ask {question, role, state, history}` → `{status, answer, segments[{text, refs, conditions}], sources[{n, chunk_id, heading, section, jurisdiction, amends, blocks, cited_texts}], flags, usage, cost_usd, latency_ms, trace_id}`. Also `GET /api/meta`, `GET /api/section?id&role&state`, `POST /api/feedback`, `GET /api/stats`.

## Roadmap

1. **Cross-section conditions (h07).** When an answer cites a base-form section that a retrieved state endorsement amends, require the endorsement's change to appear in the answer, using the same endorsement links retrieval already builds. Add golden questions for it.
2. **Shorter answers:** cap length for policyholders. Measure cost and fact coverage before and after.
3. **Hybrid retrieval.** Add dense embeddings fused with BM25 via reciprocal rank fusion, then a reranker. Success = held-out recall ≥ 95% with golden recall unchanged.
4. **Grow the eval to 150+ questions,** including multi-turn follow-ups. Sample real questions from traces once there is traffic.
5. **PDF ingestion** of real policy forms (layout-aware parsing; page-level citations via `document` blocks).
6. **Declarations-page awareness:** load the user's actual limits and deductibles so answers say "$6,000", not "2% of Coverage A".
7. **Drift and quality dashboard** over the trace log (this is Project 3 of this portfolio).

## Deployment memo (the FDE version of this project)

> *A hypothetical engagement, written the way I'd scope a real one. The numbers are assumptions to validate in discovery.*
>
> **Customer:** a regional P&C carrier's claims org, about 120 adjusters plus a policyholder self-service portal.
> **Pain:** adjusters spend an estimated 15–25 minutes per coverage question digging through forms and state endorsements. Policyholder calls about "am I covered" are the #2 call driver.
> **Constraints:** internal guidelines must never reach policyholders. Answers must be auditable to the section and form version. No PII in logs. No coverage determinations by software.
> **What shipped:** the system above, with role and jurisdiction enforced in retrieval, citation-or-refuse, and per-request audit traces that include form versions.
> **How we know it works:** golden set plus a held-out set for retrieval, a red-team suite run in CI, and LLM-judged faithfulness end to end. Failures are triaged from the eval report, not from anecdotes.
> **Next decision for the customer:** pilot with 10 adjusters for two weeks. Measure time-to-answer and the "adjuster disagreed with copilot" rate from a thumbs-down button wired into traces.
