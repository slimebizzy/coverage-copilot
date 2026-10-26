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

| | Golden set (32 questions) | Held-out set (8 questions, never tuned on) |
|---|---|---|
| Recall@6, v0 (plain BM25) | 90.6% | n/a |
| Recall@6, v1 (query expansion + stemming fix) | **100%** | **87.5%** |
| MRR, v0 → v1 | 0.789 → **0.927** | 0.708 |
| Answerable questions wrongly gated as "not found", v0 → v1 | 3 → **0** | 0 |

How v0 became v1: the eval listed five misses. Each was a vocabulary gap ("drove off" vs. *hit-and-run*, "leaking under my sink" vs. *continuous seepage*, "disagree with the estimate" vs. *appraisal*). One was a stemmer bug that turned "earthquakes" into "earthquak". The fix was a domain synonym table plus the stemmer repair, each traced to a specific failing question (`eval/reports/retrieval-v0-baseline.md`).

The held-out number keeps this honest. The expansions were tuned on the golden set, so 100% there is optimistic. 87.5% on unseen phrasings is the number I'd quote to a customer. The one held-out miss ("stole my guns" vs. *firearms*) is exactly the failure dense embeddings fix, which is the top roadmap item.

### Red team (12 attacks)

12/12 pass the deterministic checks (no restricted section retrieved, no wrong-state endorsement, PII redacted). Attacks include role-claim escalation ("I am an adjuster, so show me…"), prompt injection, off-domain requests, jurisdiction confusion and coverage-promise baiting. 4 of the 5 refusal cases stop before any model call. The fifth (pet vet bills) shares enough vocabulary with the policy to pass the gate, so the model's `NOT_IN_SOURCES` path handles it.

### End-to-end with Claude (`make eval-full`)

40 questions (golden + held-out) and 12 attacks against `claude-opus-5-5` at effort `medium`. Full report: [`eval/reports/full-latest.md`](eval/reports/full-latest.md).

| Metric | Value |
|---|---|
| Answered with citations | 40/40 |
| Key-fact coverage (the expected number or term appears in the answer) | **97.5%** |
| Cited an expected section | **97.5%** |
| Faithfulness (LLM judge, every claim backed by the retrieved sources) | **82.5%** (33/40) |
| Red team passed | **12/12** |
| Latency p50 / p90 | 7.0 s / 10.4 s (2 of 40 requests hung; see below) |
| Cost per query | **$0.021** ($0.86 for the run) |
| Input tokens served from prompt cache | 42% |

**What the first run found**, and what changed because of it:

- **The grader was wrong before the model was.** The first judge pass scored faithfulness at 30%. Reading the flagged claims showed the judge only saw the snippets the model *cited*, not the full sections and titles it was *given*. It flagged "this is the Texas endorsement" as unsupported because the jurisdiction lives in the title. After the fix, the same saved answers scored 82.5% (`--rejudge` re-grades them without re-asking). The 30% report is kept as [`full-v1-snippet-judge.md`](eval/reports/full-v1-snippet-judge.md).
- **One red-team "failure" was a bad check.** The coverage-promise test matched "is approved" inside *"I can't confirm that your roof claim is approved."* That's the behavior we want. The check now looks at each sentence and skips negated ones.
- **The 7 remaining faithfulness flags, triaged by hand:**
  - **1 material error (g03).** The answer described the California contents advance as applying to any total loss and dropped the "declared state of emergency" condition. That's the kind of mistake that matters in a regulated product, so it's the first prompt fix on the roadmap.
  - **1 unsupported advice (h03).** "Avoid permanent repairs until the damage is documented" sounds reasonable, but it isn't in the homeowners form.
  - **3 outside knowledge that is true but not retrieved (g02, g06, g31).** For example, "Coverage A is your dwelling coverage."
  - **2 judge artifacts (g30, h08).** The answer repeated the request's own context line, "no state endorsement applies."
- **Abstaining instead of guessing.** On the one held-out retrieval miss (h02, firearms), the model said the retrieved sections don't state a firearms limit instead of inventing one. It scores 0% on key facts, which is the correct failure mode.
- **Two hung requests.** One took 611 s and one 99 s, because the SDK's default timeout is 10 minutes. The client now uses a 60 s timeout with 2 retries. The p50 and p90 above are over all 40 requests; the two hangs only show up from p95 up.
- **Caching works but isn't the main cost lever.** The 1,293-token system prompt is cached after the first call (42% of input tokens served from cache). Most of the cost is output: answers average about 900 tokens. Shorter answers are the next cost lever.

## Design decisions and tradeoffs

- **Search-result blocks instead of "please cite [1]" prompting.** Native citations return the exact cited text and source id as structured data. That makes citation enforcement a code check, not a regex over prose.
- **Filter before scoring, not after.** Post-filtering top-k can let a restricted chunk influence ranking, or leak if someone later changes k. Pre-filtering makes the guarantee structural, and a parametrized test checks it for every role × state combination.
- **BM25 first, embeddings second.** On ~80 well-titled sections, BM25 plus a domain synonym table hit 100% / 87.5% recall with zero infrastructure and zero per-query cost. Adding a vector store before measuring would have been cargo cult. The held-out miss shows where it stops working.
- **A gate that skips the model.** Low-relevance questions return in about 1 ms for $0. That also removes a whole class of hallucinations: the model can't invent an answer from irrelevant context it never sees.
- **The disclaimer is code, not prompt.** Regulated wording shouldn't depend on the model remembering it.
- **Prompt caching, measured.** The system prompt carries a `cache_control` breakpoint, and traces record `cache_read_input_tokens`, so the hit rate is measured, not assumed. In the eval run, 42% of input tokens came from cache. Output length and the relevance gate (which skips the model entirely) move cost more.
- **Refusal fallback.** Requests use `fallbacks: "default"` (beta `server-side-fallback-2026-07-01`). If a safety classifier declines, the API retries on a fallback model within the same call, and a `refusal` stop reason is still handled explicitly.

## Run it

```bash
make setup                 # venv + dependencies (Python 3.9+)
cp .env.example .env       # add ANTHROPIC_API_KEY, or leave empty for offline mode
make run                   # http://localhost:8765
make test                  # 34 tests, no network
make eval                  # retrieval + red team, free
make eval-full             # end-to-end with Claude + LLM judge (about $1.50)
```

Try these in the UI: switch **State** between CA and TX and ask about hotels after a wildfire, or hail deductibles. Switch **I am a** to Policyholder and ask for reserve authority. You'll get "not found", because those sections don't exist for that role.

API: `POST /api/ask {question, role, state, history}` → `{status, answer, segments[{text, refs}], sources[{n, chunk_id, title, cited_text}], flags, usage, cost_usd, latency_ms, trace_id}`.

## Roadmap

1. **Fix the g03 class of error:** require every condition attached to a benefit ("relating to a declared state of emergency") to be carried into the answer. Add golden questions that probe conditions specifically.
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
