# Citizen Assistance Technology (CAT) — Project State

**This is the authoritative current-state document for CAT.**

> **CAT IS FROZEN** at commit `c24eda2`. M10, M11, M12 and M13 are
> complete. Part A below describes the final frozen system and is
> authoritative. Part B preserves the milestone-by-milestone history,
> including superseded numbers, clearly labelled as historical.
>
> Read Part A before touching anything. Where the two parts disagree,
> Part A wins.

## Source of truth

- **Implementation state:** this Git repository. Don't assume a feature exists because a spec says it should — inspect the code.
- **Requirements:** the user's latest decisions win over the original CAP overview document when they conflict.
- **Law:** official India Code text only (see `docs/LEGAL_SOURCES.md`). Never a bill draft, never an unofficial mirror.
- **Design:** current product requirements win over any old screenshot/template.
- **Final state:** commit `c24eda2` and the evaluation artifacts it produced. Where an older milestone summary conflicts with the frozen code, the index manifest or the final evaluation output, the artifact wins and the summary is historical.

---

# PART A — FINAL FROZEN STATE (authoritative)

> Everything in Part A describes the system as it exists at the frozen
> commit. Where an older milestone entry in Part B disagrees with Part A,
> **Part A wins** — Part B is preserved as the historical record of how
> the project got here, not as a statement of current fact.

## 0. ICCSDI 2026 revision update (post-freeze, authoritative deltas)

The ICCSDI 2026 minor revision made four bounded changes on top of the
frozen state plus the two post-freeze safety-routing commits
(`dce6304`, `951edaf`). Where a number below differs from the frozen
Part A sections, **this section wins**.

1. **Extraction defects fixed (corpus 1,827 → 1,832 chunks).** The five
   documented defects — BNS 217/255 and JJ Act 61/86 merged into the
   preceding chunk (wrong citation attribution), and RTI s.14 dropped
   entirely inside the excluded s.13 — are repaired by curated,
   asserted `SourceMeta.section_splits`
   (`app/ingestion/chunk.py::apply_section_splits`), the same idiom as
   `title_overrides`/`exclude_units`; the general header pattern is
   untouched. Regression tests: `tests/test_section_splits.py`. See
   `docs/LEGAL_SOURCES.md` "Curated section-split repairs".
2. **Case-law coverage guard.** A citation-audit probe ("supreme court
   judgment on privacy") was answered with statutes; the corpus holds
   no judgments, so `corpus_coverage.py` gained a narrow `case_law`
   category with its own message (`CASE_LAW_MESSAGE`), verified not to
   fire on any of the 362 labelled answer-expected queries.
3. **Full re-evaluation on the corrected corpus** (production path,
   `finetune/eval_seeds.py`; artifacts in
   `finetune/output/revision_eval/`). The corpus correction changed no
   headline metric on either model. The post-freeze safety refinement
   moved exactly one benchmark row (h017, "my neighbor broke into my
   house at night", now emergency-routed as an active crime), so false
   abstains are 46 base / 25 fine-tuned on citizen-281 (was 45/24) and
   11/8 on the held-out 41 (was 10/7); abstention accuracy 0.8530 →
   0.9201 (deployed citizen) and 0.7317 → 0.8049 (held-out). All other
   Part A section 5/6 numbers reproduce exactly on the corrected
   corpus: citizen recall@5 0.7448 → 0.9554, MRR 0.5656 → 0.8800,
   top-1 0.4448 → 0.8185, wrong-Act 43 → 19, hard-negative 28/29 →
   29/29, held-out recall@5 0.7634 → 0.8732 / MRR 0.5687 → 0.7122 /
   top-1 0.4634 → 0.6098; control set unchanged. Zero false accepts
   everywhere. Follow-up benchmark unchanged (19/21, 4/4, 4/4, 6/6,
   2/2, 2/3). Fresh scripted citation audit
   (`eval/audit_citations.py`): 26 probes, 95 excerpts, zero defects,
   including the five recovered sections.
4. **Repeated-seed stability experiment**
   (`finetune/run_seed_experiment.py`): seeds 42–46, identical
   corpus/splits/hyperparameters/protocol, only the seed varies;
   per-seed production-path results in
   `finetune/output/seed<N>_rev/seed_eval.json`. Held-out citizen 41:
   recall@5 0.8634 ± 0.0134 (range 0.8488–0.8732), MRR 0.7170 ± 0.0214,
   top-1 0.6244 ± 0.0408, abstention 0.7805 ± 0.0345; hard-negative
   29/29 on all five seeds; deployed wrong-Act 16–19 (base 43); the
   retrained seed-42 run reproduces the promoted model's numbers
   exactly. One seed (45) produced the sweep's only false accept —
   h293, "what is the minimum wage for a construction worker",
   answered from `bns:146` over the gate floor — which moved the
   minimum-wage subject into the coverage guard (`minimum_wages`
   category, metric-neutral for the promoted model, regression-tested).
   Full summary in `docs/RETRIEVAL_EVALUATION.md` "Repeated-seed
   results" and the revision report alongside the paper.

Python test count after the revision: **433 passed** (the frozen 369
grew with the post-freeze safety tests and the revision's regression
tests); API 318 and web 278 unchanged.

## 1. Final frozen state

| | |
| --- | --- |
| **Frozen commit** | `c24eda25cf44d66f41e6e9badbe9a58440e94bb2` ("deploy: promote m12_run2 to the production retrieval path (M13 freeze)") |
| **Remote** | `https://github.com/Solly2201/CAT` |
| **Milestones complete** | M10, M11, M12, M13 |
| **Status** | **FROZEN.** CAT is the experimental system of record. No feature, retrieval, model or corpus changes. |

M13 promoted the M12 fine-tuned embedding candidate onto the real
production retrieval path after a full one-variable evaluation against
the reproduced M12 baseline, fixed a real defect the deployment surfaced
(the test suite silently reverting the production index), and froze the
system.

**What the four final milestones delivered:**

- **M10 — product completion.** Deterministic civic duplicate handling, the Legal Assistant to Learn provision join, post-409 state resynchronisation, the authority petition-response panel, paginated/filtered authority queues, ADMIN signature recount, and role- and reality-aware navigation/denial/session copy.
- **M11 — session, mail, search, multi-turn context.** 7-day refresh token renewing a 15-minute access token (revocable via `tokenVersion`, stored role re-read on every refresh), verification email over any configured `SMTP_URL`, My Reports pagination, deterministic petition free-text search, acting-staff names in history, and the deterministic multi-turn context layer.
- **M12 — accuracy and evaluation.** The production-path measurement series, the 112-row failure taxonomy, a curated spelling layer plus probe-verified normalisation rules, the gate floor recalibration 0.42 to 0.41, the follow-up benchmark grown 18 to 40 rows, and the `m12_run2` fine-tune validated on held-out data.
- **M13 — promotion and freeze.** `m12_run2` deployed on the production path, promoted against all nine gate conditions, verified live against the running Docker stack, and frozen.

## 2. Final architecture

Three services behind one API boundary:

- `apps/web` — React 18 + TypeScript + Vite + Tailwind citizen UI.
- `services/api` — Node 20 + Express + Mongoose. Owns auth/RBAC and every business workflow (civic, petitions, media). Proxies legal calls to the AI service; the browser never reaches the AI service directly.
- `services/ai` — Python 3.11 + FastAPI. Ingestion, index build, retrieval, the deterministic safety layer, and answer assembly. Owns no user data.
- `packages/contracts` — shared Zod contracts.
- MongoDB for domain data; local disk for media; Redis provisioned in Compose but **not connected to by any code** (see section 9).

**The final legal-answer pipeline** (`handle_legal_query`):

```text
USER QUESTION
  -> Risk / UPL policy        harmful_request -> refuse
  |                           emergency       -> official helpline, no retrieval
  |                           serious         -> caution first, retrieval still runs
  -> Context resolution       fold in the previous turn deterministically,
  |                           or ask for a restatement; never guess
  -> Guard re-run             context is client-supplied and untrusted, so every
  |                           guard re-runs on the combined text; stricter wins
  -> Topic relevance          known out-of-domain subject -> abstain pre-retrieval
  -> Corpus coverage          names an Act this corpus lacks -> abstain pre-retrieval
  -> Query normalization      statutory vocabulary appended to the RETRIEVAL text only
  -> BM25 + dense retrieval   top-50 candidate pool each
  -> Weighted RRF             k=5, dense 3.0 / BM25 1.0 -> top-5
  -> Confidence / evidence    hybrid floor 0.41 on the top hit's dense score
  -> Citation verification    structural manifest metadata, never generated text
  -> DETERMINISTIC RESPONSE   verbatim excerpt(s) + citations + disclaimer
```

Insufficient evidence produces **ABSTAIN**, **CLARIFY** or **ROUTE** — never a filled gap.

**Standing decision, unchanged and final: 0% generative LLM in the
legal-answer pipeline.** Not as a generator, reranker, fallback or
classifier. The LLM-generation direction was built (provider
abstraction, a working Gemini integration, citation validation over
generated text) and deliberately discarded on hallucination-risk grounds.
`sentence-transformers` is used strictly as an encoder.

Normalisation placement is deliberate and load-bearing: every safety and
coverage guard inspects the **raw** question, so appended vocabulary can
never talk retrieval past a safety decision, and the answer is assembled
from the retrieved chunks themselves, so normalised text never reaches
the citizen, the citations, or the excerpt.

## 3. Final model and configuration

| | |
| --- | --- |
| **Production dense model** | `data/models/m12_run2` (service-root-relative) |
| **Base checkpoint** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Training** | MultipleNegativesRankingLoss, 4 epochs, batch 16, lr 2e-5, seed 42, 1682 train / 340 val triplets |
| **Dimension** | 384 |
| **Artifact hash** | `model.safetensors` SHA-256 `d61d077b4287c2cd1075045dccec0139981751fc1125e1bcd92dc29e0a0ce801`; aggregate over all 11 files `8a15eb039e298e44b25959903c79808f51c9194b75b92f410d567300981c95fa`; 91,861,927 bytes |
| **Distribution** | Gitignored build artifact, reproduced by the seeded `finetune/` pipeline. Never committed. |
| **Selection** | `DENSE_EMBEDDING_MODEL`; `embeddings.resolve_model_path()` resolves the relative path at load time only, so one manifest works on the host and in the container |
| **Retrieval mode** | `hybrid` |
| **Candidate pool** | 50 per method |
| **Fusion** | weighted RRF, k=5, dense weight 3.0, BM25 weight 1.0 |
| **top_k** | 5 |
| **Confidence floors** | hybrid **0.41** (on the top hit's `dense_score`), bm25 3.0, dense 0.45; overridable via `LEGAL_CHAT_MIN_SCORE` |

At query time the service always follows `index_manifest.json`'s
`dense_embedding_model`, so a running service can never encode queries
with a model different from the one that built its index. The container
mounts `./services/ai/data` read-only at `/app/data`, so a model or index
change needs **no image rebuild**.

## 4. Final corpus

**10 official Acts, 1,827 chunks**, verified from
`services/ai/data/index/chunk_manifest.jsonl`:

| Source id | Act | Chunks |
| --- | --- | ---: |
| `bnss` | Bharatiya Nagarik Suraksha Sanhita, 2023 | 531 |
| `constitution` | Constitution of India | 366 |
| `bns` | Bharatiya Nyaya Sanhita, 2023 | 356 |
| `bsa` | Bharatiya Sakshya Adhiniyam, 2023 | 170 |
| `jj2015` | Juvenile Justice (Care and Protection of Children) Act, 2015 | 110 |
| `cpa2019` | Consumer Protection Act, 2019 | 107 |
| `it_act` | Information Technology Act, 2000 | 92 |
| `pwdva` | Protection of Women from Domestic Violence Act, 2005 | 37 |
| `lsa` | Legal Services Authorities Act, 1987 | 32 |
| `rti` | Right to Information Act, 2005 | 26 |
| | **Total** | **1,827** |

Per-source coverage notes, exclusions and extraction limitations are in
`docs/LEGAL_SOURCES.md` and are surfaced live on `/corpus/sources` and on
every search result.

**Learn content, counted from `apps/web/src/content/learn/`:** 71
learning articles across 12 categories, 216 quiz questions, 35 FAQs.
Every article paragraph and every FAQ `legalBasis` paragraph carries a
structured `{ sourceId, unitNumber, label }` citation resolved against
the same source registry the corpus uses; the citation tests fail if any
of them stops resolving. Learn content is static and authored — the
frontend never calls the AI service to render it, so an article or FAQ
cannot change under a reader or say something its cited provision does
not.

## 5. Final evaluation

Three distinct benchmark families. **They measure different things and
must not be compared to each other or merged.**

### A. Final production benchmark (contains trained-on queries)

`run_eval.py --production-path --mode hybrid`. Same corpus, queries,
normalisation, guards, gate floor and scoring on both sides; the only
variable is the embedding model. Reproduced twice, byte-identically.

| Metric | Citizen 281 baseline -> m12_run2 | Control 46 baseline -> m12_run2 |
| --- | --- | --- |
| recall@5 | 0.7448 -> **0.9554** | 0.8623 -> **0.9674** |
| MRR | 0.5656 -> **0.8800** | 0.7341 -> **0.9246** |
| nDCG@5 | 0.6040 -> **0.8984** | 0.7476 -> **0.9261** |
| top-1 citation | 0.4448 -> **0.8185** | 0.6522 -> **0.8913** |
| abstention accuracy | 0.8562 -> **0.9233** | 0.9796 -> 0.9592 |
| false accepts | 0 -> **0** | 0 -> **0** |
| false abstains | 45 -> **24** | 1 -> 2 |
| wrong-Act top-1 | 43 -> **19** | 3 -> 3 (no new) |

Citizen 281 = the 281 non-abstain rows of the 313-row
`eval/queries_human.jsonl`. Control 46 = the 46 non-abstain rows of the
49-row `eval/queries.jsonl`.

**These are the deployed system's benchmark numbers. They are NOT a
generalisation result** — the fine-tune's training pool was drawn from
these labelled sets.

### B. Held-out generalisation evaluation

Restricted to ids in `finetune/data/test.jsonl`, never trained or
selected on.

| Metric | Citizen 41 | Control 9 |
| --- | --- | --- |
| recall@5 | 0.7634 -> **0.8732** | 0.8333 -> 0.8333 (equal) |
| MRR | 0.5687 -> **0.7122** | 0.7259 -> **0.8000** |
| top-1 citation | 0.4634 -> **0.6098** | 0.6667 -> **0.7778** |
| abstention accuracy | 0.7561 -> **0.8293** | — |
| false accepts | 0 -> **0** | — |
| false abstains | 10 -> **7** | — |

This — and only this — is the generalisation claim. Held-out wrong-Act
moved 4 to 8 and each case was inspected individually: two abstain
rather than answer (the wrong top-1 is never shown), one is a label gap
(`rti:21` is genuinely the RTI Act's identically-titled protection
section, on a row predating RTI ingestion), and one (h252) is a real mild
adjacent-domain ranking regression.

### C. Follow-up / context benchmark (40 rows)

`eval/queries_followup.jsonl`, all targets corpus-verified. See section 7.

### Split sizes

| Set | Rows |
| --- | ---: |
| `eval/queries.jsonl` (control) | 49 (46 non-abstain, 3 abstain-expected) |
| `eval/queries_human.jsonl` (citizen) | 313 (281 non-abstain, 32 abstain-expected) |
| `eval/queries_followup.jsonl` | 40 |
| `finetune/data/train.jsonl` | 1,682 triplets |
| `finetune/data/val.jsonl` | 340 triplets |
| `finetune/data/test.jsonl` | 368 triplets |

## 6. Final safety results

- **Zero false accepts** on both final evaluation sets and on the held-out set. Nothing that should abstain is answered.
- **Hard-negative recall 29/29** (up from 28/29), including the bidirectional BNS/BNSS decoy pair. This is the single most important number in the project: it measures not confidently citing a superficially similar but legally wrong provision.
- **Wrong-Act top-1 43 to 19** on citizen 281; no new wrong-Act answers on the control set.
- **Guards are byte-identical** across the model change. Every deterministic guard operates on raw text, so promoting the embedding model could not and did not move safety behaviour.
- **Live battery on the deployed index, 9/9:** supported query answered (`constitution:14` top-1), citizen-language stolen-phone complaint answered (`bnss:106`), misspelled "bale" answered (`bnss:482`/`480`), ambiguous answered, out-of-domain abstained, un-ingested Act (divorce) abstained via the coverage guard, emergency redirected, UPL personal-outcome abstained, harmful request refused.
- **Citation integrity:** every returned excerpt's `chunk_id` resolves in `chunk_manifest.jsonl`, with real source / act_no / unit / official-URL citations. A 33-probe audit across every pipeline route found zero defects over 100 excerpts, and the property is pinned permanently at `Chunk.citation()` by `tests/test_citation_integrity.py`.
- **Fabricated-action templates:** `app/safety/fabrication.py` is a regression check over the fixed hand-written strings. There is no per-request output to check, because nothing generates any.
- **Live-stack smoke: 23/23** end-to-end checks across legal, auth, civic and petitions against the running Docker stack.

## 7. Final context / follow-up results

Deterministic composition with the previous question. No model, no LLM.
The combined text is shown back verbatim, and every guard re-runs on it
with the stricter outcome winning, so context can never carry a query
past a safety or coverage decision the first turn already lost.

| Category | Rows | Result |
| --- | ---: | --- |
| condition follow-up | 21 | **19/21** with context (6/21 fragment-only baseline) |
| ambiguous follow-up | 4 | 4/4 |
| no-context follow-up | 4 | 4/4 |
| guarded follow-up | 6 | 6/6, reasons byte-identical |
| not-emergency | 2 | 2/2 |
| standalone override | 3 | 2/3 |

`f04` — the long-standing M8 FIR-copy recall miss — is **fixed** by the
final model. Residuals recorded, not papered over: `f22` newly misses on
ranking, `f24` (`rti:19`) unchanged, and `f35` now abstains instead of
answering (conservative direction).

## 8. Final engineering verification

Re-run and confirmed at the freeze:

| Check | Result |
| --- | --- |
| Python (AI service) — `python -m pytest tests/ -q` | **369 passed** |
| API unit — `npm test -w @cap/api` | **318 passed** |
| Web unit — `npm test -w @cap/web` | **278 passed** |
| Monorepo typecheck — `npm run typecheck` | clean |
| Production build — `npm run build` | clean |
| Database integration (real MongoDB) | CI job (`integration` in `ci.yml`); needs a live MongoDB, so not part of the local unit run |
| Compose stack build + smoke | `.github/workflows/integration.yml`, on demand and weekly |
| Live-stack end-to-end smoke | 23/23 at M13 |

CI (`.github/workflows/ci.yml`) runs on every push and pull request:
typecheck, `npm test`, production build, `git diff --check`, the MongoDB
integration job, and the Python suite. The retrieval evaluation is
deliberately excluded from CI — it is an offline research workflow, not a
per-commit check.

**A real defect M13 found and fixed:** `tests/test_retrieval.py` and
`tests/test_hybrid_retrieval.py` deliberately rebuild the real
`data/index`; with `DENSE_EMBEDDING_MODEL` unset, that rebuild used the
*default base model* and silently reverted the production index.
`tests/conftest.py` now pins the variable to whatever the on-disk
manifest records before any test runs (explicit env still wins; a
recorded-but-absent artifact falls through to the default). Verified by
running the whole suite env-unset and checking the manifest and vectors
afterwards. New unit tests: `tests/test_embeddings_config.py`.

## 9. Known limitations (final)

Carried forward as true at the freeze. The full historical gap register,
including everything since closed, is in "Known gaps / next steps" below.

**Legal coverage**

1. **Coverage is partial and deliberately so.** 10 Acts. Two different mechanisms keep un-ingested subjects from being answered, and conflating them would overstate the guard. **Named by `app/safety/corpus_coverage.py`, abstained on before retrieval:** POCSO, motor vehicles, matrimonial law, SC/ST atrocities, court fees/CPC, and the RTI service provisions excluded at ingestion. **Not ingested and deliberately left to the confidence gate:** labour/workplace, tenancy/rent control, data protection, stamp duty, arbitration, municipal services — a probe confirmed the gate abstains on all seven labour and civic-service probes correctly with no guard at all, so writing patterns for them would have been speculative rather than evidence-driven. **No case law of any kind is ingested;** CAT answers from statute only.
2. **RTI is the Central Information Commission's pre-2019 copy.** ss.13, 16 and 27 (replaced by the RTI (Amendment) Act 2019) are excluded rather than served as current law; s.25 is excluded for measured retrieval harm; s.14 is not chunked (a source formatting quirk); no RTI fee amount is stated anywhere, because the Act leaves the figures to rules that are not ingested.
3. **Four sections merge into the preceding chunk** (BNS 217/255, JJ Act 61/86) because of a source-PDF layout quirk. The text is present verbatim; the defect is citation attribution for those four sections, not content loss.
4. **Constitution section titles are not generally recovered** (two-column gazette layout); a hand-verified table covers Part III. Article numbers and body text are exact throughout.

**Retrieval**

5. **One residual top-1 preference:** "can an officer be penalized for not providing information" ranks `it_act:44` above `rti:20`. Both are genuine penalty-for-not-furnishing-information provisions and the query names no Act, so the preference is ambiguous by construction; the RTI section stays in the window the citizen sees, and the test asserts presence-in-window for that phrasing under the same convention as the BNSS s.43 window test. No normalisation rule was added for it — tuning the production path against a single probe after the numbers were finalised would invalidate the published comparison.
6. **`h286`** ("how do I file an application for information from a government office") remains the shape a deterministic phrase guard cannot catch: a subject the query never names.
7. **Genuinely ambiguous phrasings have no normalisation rule by design.** Where no discriminating signal exists, retrieval sees the raw query — guessing would move it confidently toward one wrong Act.

**Platform**

8. **Rate limiting is in-process** (`express-rate-limit`'s memory store), correct for the single API instance this project deploys. `REDIS_URL` is validated at boot and Redis runs in Compose, but no application code connects to it.
9. **Media is disk-backed and volume-persisted, not streamed.**
10. **Email verification needs a configured `SMTP_URL`;** production self-registration answers 503 rather than issuing a challenge nobody can receive.
11. **A Socket.IO server is mounted** and emits a readiness handshake; no product feature uses real-time updates.
12. **English only.**
13. **The API rate limiter bounds bulk end-to-end testing** (100 requests / 15 min / IP), so a full manual smoke run must be split across API restarts.

## 10. Reproduction instructions

```bash
# Corpus + index (from services/ai/)
export DENSE_EMBEDDING_MODEL=data/models/m12_run2
python scripts/ingest_corpus.py          # -> 1,827 chunks, mode=hybrid

# Final production-path evaluation
python eval/run_eval.py --production-path --mode hybrid           # control 46
python eval/run_eval.py --production-path --mode hybrid --human   # citizen 281
python eval/run_context_eval.py                                   # follow-up 40

# Historical raw-query series (unchanged, still reproduces every old number)
python eval/run_eval.py                   # bm25 vs dense vs hybrid, top_k=5

# Reproduce the model artifact itself (seeded, deterministic splits)
python finetune/build_dataset.py
python finetune/train.py --run-name m12_run2
python finetune/eval_heldout.py --run-name m12_run2

# Engineering verification
python -m pytest tests/ -q                # 369
npm run typecheck && npm test && npm run build
```

Re-ingestion is required after any corpus change and after any change to
`DENSE_EMBEDDING_MODEL`. Nothing downstream hardcodes the embedding
dimension — it is read from the model at build time and recorded in the
manifest.

---

# PART B — HISTORICAL MILESTONE RECORD

> **Everything below this line is historical.** It records what was true
> at each milestone, including numbers that later milestones superseded
> (corpus sizes of 554 / 1,783 / 1,801 chunks, the base
> `all-MiniLM-L6-v2` embedding model, earlier eval-set sizes, earlier
> recall/MRR/abstention figures, and earlier test counts). These are kept
> deliberately, because the reasoning behind a rejected or superseded
> decision is worth as much as the decision that replaced it.
>
> **Do not read any number below as a current or final value.** Part A
> above is the authoritative current state.


## Historical commit lineage

- `7971e01` — Increment 1 (foundation)
- `6c4ffe3` — Increment 2 / Module 1A (legal ingestion + learning library)
- `3dc2ced`, `343d22c` — Module 1B Batches 1–2, committed under an earlier generative design (see "Architecture pivot" below) — the confidence gate and abstention behavior from these commits survive into the current design; the LLM-provider code they also added does not.
- **Architecture pivot (75e2fff):** the legal-answer pipeline was rebuilt as pure retrieval + deterministic response. An LLM-generation direction (provider abstraction, a real Gemini integration verified against the live API, citation/index validation on generated text, prompt-injection defenses) was fully implemented and then deliberately discarded once weighed against hallucination risk in a legal-information context. **Standing decision: the legal-answer path never uses a generative LLM, full stop** — this is not a temporary state, and a future session should not reintroduce generation here without the user explicitly asking again.
- **Hybrid retrieval (8ac5123):** BM25-only retrieval was replaced with hybrid retrieval — BM25 + local dense embeddings (`sentence-transformers/all-MiniLM-L6-v2`), combined with weighted Reciprocal Rank Fusion — evaluated against a hand-curated 30-query set before and after, per `docs/RETRIEVAL_EVALUATION.md`. Hybrid beat the BM25 baseline on every measured metric (Recall@5 0.79→0.94, MRR 0.69→0.82, nDCG@5 0.69→0.84, top-1 citation correctness 0.61→0.74, abstention accuracy 0.77→0.83). Still pure retrieval — no generative LLM was added anywhere in this work; embeddings are retrieval infrastructure only.
- **Corpus expansion (this update, uncommitted):** All 10 India Code sources this project has PDFs for are now registered; 9 are fully ingested (1,783 chunks total). RTI Act 2005 remains the one unresolved source gap (font-encoding defect in the only PDF supplied so far). See "Corpus expansion" under Completed and "Retrieval/evaluation hardening" below for what this actually involved — a two-column gazette layout that an earlier attempt in this same uncommitted change got close on but not clean enough to ship was fully solved, section titles were recovered for roughly half of the affected sources, the evaluation set was rebuilt to actually cover the new corpus, and the hybrid confidence threshold was raised after that evaluation surfaced a real false-answer risk on out-of-domain queries.
- **Retrieval ranking optimization (Constitution titles + RRF retune):** a failure analysis over `eval/queries.jsonl`'s 45 non-abstain queries found missing Constitution Part III title metadata as the dominant remaining failure cluster; fixed with a small hand-verified title table (`app/ingestion/chunk.py`) plus a source-scoping bugfix (an early version leaked Constitution titles into other gazette Acts sharing the same chunker), then re-tuned the RRF dense weight (2.0→2.5) against the improved index. Hybrid recall@5 0.7407→0.8074, MRR 0.6341→0.6670, nDCG@5 0.6324→0.6734, top-1 citation correctness 0.5333→0.5556, abstention accuracy unchanged at 0.9796, no new wrong-Act false positives, 60/60 tests pass. Reranking was evaluated again against the new failure set and still not justified — see `docs/RETRIEVAL_EVALUATION.md`'s "Failure-analysis-driven fixes" section for the full breakdown, including what still doesn't rank correctly and why (an embedding-model/vocabulary gap on two queries, not a pipeline defect).
- **Topic-relevance guard:** closed gap #19 below — the hybrid confidence gate's single dense-score threshold could not separate genuinely out-of-domain queries ("What is the income tax slab?", "How do I get a driving licence?", both ~0.45-0.49) from a genuine low-confidence paraphrase (q20 at 0.4531), because both look identical to a bounded score once a query shares real vocabulary with unrelated corpus content. Added `app/safety/topic_relevance.py` — a small, curated, deterministic phrase-pattern guard (same style as `app/safety/risk.py`'s Risk/UPL rules and `app/retrieval/query_expand.py`'s abbreviation dict), run in `handle_legal_query()` after Risk/UPL and before retrieval. It matches phrase-level patterns (not bare keywords, to avoid colliding with genuine legal text sharing a single word) for five curated out-of-domain categories: company/business registration, income tax, driving licence/vehicle registration, identity documents (passport/Aadhaar/PAN/ration card/voter ID/birth certificate), and everyday non-civic topics (weather, food, entertainment, travel bookings, etc.). A match short-circuits before spending a retrieval call, exactly like Risk/UPL. Anything unrecognized still falls through unchanged to the existing per-mode confidence gate — this is not a general topic classifier and abstains (falls through, doesn't reject) on genuine legal-awareness questions and ambiguous near-matches by construction (verified against the full 49-query eval set and hand-picked near-match cases — see `docs/RETRIEVAL_EVALUATION.md`). 6 new tests (`tests/test_topic_relevance.py`); 66/66 Python tests pass. Since the guard only changes pre-retrieval gating (not ranking), hybrid's recall@5/MRR/nDCG@5/top-1-citation-correctness on the 45 non-abstain queries are unchanged (0.8074/0.6670/0.6734/0.5556); abstention accuracy stayed 0.9796 for hybrid (already correct on all OOD cases via the score gate) and rose 0.9184→0.9796 for bm25-only mode (which had no dense-score fallback and previously answered all 4 out-of-domain controls confidently from the wrong Act — the guard fixes that for every retrieval mode, not just hybrid, since it runs before mode-specific search).
- **New single-column source PDFs for BNS/BNSS/BSA/CPA2019/JJ Act, plus an RRF re-tune and one citizen-language expansion:** the user supplied replacement PDFs for these five sources -- plain single-column "bare Act" India Code text (consolidated "as on 6th October, 2025") instead of the old two-column gazette layout. Verified as genuine official India Code text (Act numbers, enactment clauses, section counts all check out), then integrated: switched all five from `extraction_mode="gazette_body"`/`chunk_style="constitution"` to the plain `chunk_sanhita` path already used by `it_act`/`pwdva`/`lsa` (same clean single-column format), which raised section-title recovery from 40-57% to 98-100% per source and fixed BNSS's old 337/338 duplicate-numbering artifact outright. Two small chunker regexes (`clean.py`'s `_SOFT_LINEBREAK`, `chunk.py`'s `_SANHITA_HEADER`) were widened to handle real layout variants in the new PDFs (indented section-opening lines; an em-dash directly after the section number with no space), verified to produce byte-identical output for the four untouched sources sharing the same chunker before/after. One narrower regex relaxation was tried and reverted after it introduced false-positive header matches elsewhere in the corpus -- see `docs/LEGAL_SOURCES.md`'s "New single-column PDFs" for the full extraction writeup, including the accepted 4-section residual gap (BNS 217/255, JJ Act 61/86) this left undone. Corpus grew 1,783 -> 1,801 chunks. Full index rebuilt once; RRF's dense weight was re-swept against the new embeddings (same method/grid as prior sessions) after a same-weights comparison showed the new corpus measurably shifted the embedding distribution -- dense weight 2.5 -> 3.0 (k unchanged at 5) recovered a clean improvement on every metric over both the pre-swap baseline and the un-retuned post-swap numbers (see `docs/RETRIEVAL_EVALUATION.md`). One evaluation-justified citizen-language expansion was added to `app/retrieval/query_expand.py` (`_CONCEPT_PHRASES`): "police question[ed] me" -> append "interrogation", after direct inspection confirmed BNSS s.38 (now correctly titled "Right of arrested person to meet an advocate ... during interrogation") wasn't reachable within the top-50 fusion candidate pool for the citizen phrasing "can my lawyer be present when police question me" -- the query and the section share almost no vocabulary despite describing the same right. Two other candidate gaps (q17, q46) were investigated and found NOT to be vocabulary-expansion problems -- their target chunks sit at dense rank 89 and 50 respectively, outside or at the edge of the 50-candidate fusion pool, an embedding-model/corpus-density limitation no small curated expansion can safely reach -- so, per the explicit instruction not to force expansion without evaluation justification, nothing was added for them. Final hybrid metrics (49-query set, 45 non-abstain): recall@5 0.8074 -> 0.8370, precision@5 0.1733 -> 0.1822, MRR 0.6670 -> 0.7096, nDCG@5 0.6734 -> 0.7227, top-1 citation correctness 0.5556 -> 0.6222, abstention accuracy unchanged at 0.9796, no new wrong-Act false positives. All 6 previously-fixed regression queries (FIR, bail, burden of proof, child-in-conflict-with-law, consumer complaint, RTI abstention) plus the out-of-domain topic guard re-verified end to end, all correct. 66/66 Python tests pass (one pre-existing standalone test, `test_search_finds_arrest_provision_for_sunset_query`, needed its window widened 5->10 with a documented reason: the new BNSS text genuinely moved an "inform a relative of the arrest" clause out of s.43 into its own dedicated s.48, a real content change from the PDF update, not an extraction defect, which shifted s.43's dense ranking for that one heavily-paraphrased non-tracked query). Node tests, typecheck, and production build all pass.

- **Citizen-language evaluation (this update, uncommitted):** built a second, larger evaluation set (`services/ai/eval/queries_human.jsonl`, 129 hand-verified queries across 10 categories -- direct terminology, ordinary citizen language, paraphrase, colloquial, misspelling, abbreviation, vague-but-answerable, multi-source, ambiguous, hard-negative, out-of-domain -- spanning all 9 ingested sources) specifically to test whether hybrid's strong numbers on the existing 49-query set (dominated by direct-lexical/paraphrase queries) hold up against how citizens actually type. They don't: recall@5 dropped to 0.5551 (from 0.8370) and abstention accuracy to 0.7674 (from 0.9796) before any fix, concentrated almost entirely in scenario-description categories (colloquial 0.267, vague_answerable 0.300, ordinary_citizen 0.450) while direct terminology and even deliberately close lexical decoys stayed strong (0.933 / 0.923). A real bug was found and fixed (`query_expand.py`'s FIR/NCR abbreviation matching was case-sensitive, so lowercase "fir" never expanded) and two more narrow, evaluation-justified `_CONCEPT_PHRASES` entries were added ("afford a lawyer" -> legal aid; "refund"/"money back" -> consumer complaint), recovering recall@5 to 0.5805 -- real but small relative to the gap, and confirmed not to regress the original 49-query set (still 0.8370, byte-identical). An RRF dense-weight sweep against the new set found no weight that improves both sets at once (unlike every previous re-tune), ruling out fusion-hyperparameter tuning as the fix. A generalizable dense-embedding artifact was found and confirmed across 4+ sources: every Act's own boilerplate "short title" chunk (`:1`) scores anomalously high in dense similarity for topical queries about that Act, because it literally contains the Act's full name. Conclusion: the remaining gap (~20-27 genuine failures) is a representation problem, not a vocabulary-list problem -- materially stronger evidence for embedding fine-tuning than this project's prior "2 isolated failures" baseline, meeting the documented trigger condition for revisiting that decision. **No training was started or approved** -- see `docs/RETRIEVAL_EVALUATION.md`'s "Citizen-language evaluation" section (and its "Embedding fine-tuning: now better justified, still not started" subsection) for the full root-cause breakdown and the recommended, not-yet-approved fine-tuning dataset design. New read-only diagnostic tool: `services/ai/eval/diagnose.py` (dumps a query's full uncapped BM25/dense/hybrid rank instead of guessing from a top-5-truncated view); `run_eval.py` gained a `--queries` flag (default unchanged) so either eval set can be run without duplicating the harness. 66/66 Python tests still pass.

- **Embedding fine-tuning experiment (this update, uncommitted): attempted, not promoted.** Built a reproducible fine-tuning pipeline (`services/ai/finetune/`) that mines training triplets from both eval sets using the live retrieval index for hard negatives (same-Act-nearby, BM25-strong-wrong, dense-strong-wrong, and the boilerplate-short-title pattern found last session), splits by query group to prevent leakage (train 801 / val 183 / test 171), and fine-tunes `all-MiniLM-L6-v2` with `MultipleNegativesRankingLoss`. The first full-eval-set comparison looked spectacular (hybrid recall@5 up to 0.99/0.89 on the two sets) but this was found to be **train/val contamination**: all six queries Phase 5 was asked to check (q17/q18/q23/q26/q40/q46) were in the training split, so their improvement was memorization, not generalization -- caught before being reported as a real result. The honest, corrected comparison (restricted to the 25 genuinely held-out `test`-split queries) shows recall@5 **exactly unchanged** (0.55 -> 0.55 on the 20 held-out citizen queries) with a per-query diff confirming an exact wash (1 improved, 1 regressed, 18 unchanged) and small regressions in MRR/top-1/abstention. A second hypothesis-driven experiment (larger batch size, for more in-batch negative diversity) was attempted twice and both runs were killed by environment resource instability before completing (not a hyperparameter finding); per instruction not to blindly retry against a failing environment, this was not pursued further. **Diagnosis: the training set (153 query groups) is too small to generalize** -- consistent with this project's own prior documented trigger condition (150-300+ eval queries) for revisiting fine-tuning. **Production embedding model and dense index were never modified** -- evaluation used a temporary index built in the OS temp directory. Full write-up, including the safety-gate checks (zero wrong-Act false positives, short-title artifact rank improved on every probed source) in `docs/RETRIEVAL_EVALUATION.md`'s "Embedding fine-tuning experiment (run1): not promoted". 66/66 Python tests still pass.

- **Citizen-language evaluation set expanded 129 -> 313 query groups (this update, uncommitted): measurement only, nothing in the retrieval path changed.** The previous session's fine-tuning experiment concluded the labelled set's *size* was the limiting factor, so this session grew `services/ai/eval/queries_human.jsonl` from 129 to **313 hand-verified query groups** (184 added) and re-measured, deliberately changing no retrieval code, index, embedding model, RRF weight, query-expansion entry, or confidence threshold. Every added positive was verified against real chunk text read out of `data/legal-corpus/<source>/chunks.jsonl` before being written — no section number guessed, no mapping inferred from general legal knowledge. Composition: `ordinary_citizen` 55, `colloquial` 44, `paraphrase` 34, `hard_negative` 29, `vague_answerable` 29, `direct_lexical` 24, `misspelling` 22, `out_of_domain` 22, `abbreviation` 18, `multi_source` 18, `insufficient_evidence` 10 (new), `ambiguous` 8; 281 positive / 32 abstain-expected groups; 219 distinct chunks referenced across all 9 Acts (`bns` 76, `bnss` 74, `constitution` 28, `bsa` 27, `jj2015` 27, `cpa2019` 26, `it_act` 22, `pwdva` 21, `lsa` 12). **Hybrid results (281 non-abstain, top_k=5): recall@5 0.6246, precision@5 0.1381, MRR 0.4874, nDCG@5 0.5160, top-1 citation correctness 0.3879, abstention accuracy 0.7572, wrong-Act top-1 rate 0.196** — beating dense (0.6115 / 0.4723 / 0.5027 / 0.3737) and BM25 (0.3855 / 0.2972 / 0.3137 / 0.2321) on every retrieval-quality metric, so the hybrid architecture conclusion holds at 6.4x the original evaluation size. **These percentages are not comparable to the earlier 0.5805 without accounting for composition**: scoring the original `h001`-`h129` rows in isolation out of the same run reproduces 0.5805 exactly, and re-running the unchanged 49-query set reproduces 0.8370 exactly — both are controls proving the pipeline is untouched and the aggregate movement is dataset composition. **The citizen-vs-statute gap is now confirmed at a meaningful sample size**: citizen-language categories (n=150) score recall@5 0.527 against legal-terminology categories (n=76) at 0.724, while `hard_negative` reaches 0.966 (up from 0.923 at 13 queries), including a deliberate inverse pair (`h108` Article 19 with Article 105 as decoy; `h306` Article 105 with Article 19 as decoy) that resolves correctly in *both* directions. **Two findings change standing decisions.** (1) A root-cause split of all 119 missed chunks buckets them as `bm25_vocabulary` 32.8% / `fusion_ranking` 30.3% / `representation_gap` 24.4% / `dense_embedding` 12.6% — and `fusion_ranking` (target inside *both* methods' top-50 pools, still ranked below 5) is precisely the "right answer buried in an otherwise-good candidate list" pattern this project twice cited as *absent* when deferring reranking. That blocking evidence no longer holds; reranking was still not implemented (measurement-only session), but the condition for revisiting it is now met by measurement. (2) The new `insufficient_evidence` category — legal questions about Acts the corpus genuinely does not contain (divorce, POCSO, Motor Vehicles, rent control, minimum wages, stamp duty, SC/ST Atrocities, arbitration, labour notice, RTI) — exposed a correctness risk nothing previously measured: hybrid abstains correctly on 20/22 `out_of_domain` (non-legal) queries but only **5/10** `insufficient_evidence` ones, answering e.g. "what is the penalty for drunk driving" from `bns:355` (misconduct by a drunken person) and "how do I get a divorce in india" from `bnss:219`. Hybrid's other 69 abstention errors are false *abstains*, 57 of them `ordinary_citizen`/`colloquial`, on queries whose correct chunk was retrieved — the confidence gate rejecting citizen phrasing, reproducing the 129-query finding at 5x the sample. q17/q46 re-measured and still failing as documented (`h040`: `constitution:20` at dense rank 63 / bm25 1180, outside the pool; `h098`: `pwdva:3` now hits at rank 4 but `constitution:15` still missed, with the `pwdva:1` short-title boilerplate chunk sitting at rank 1). The short-title artefact was re-probed across all 9 sources and refined: it fires hardest when a citizen *names the Act*, and it is **not dense-only** — `bnss:1` sits at BM25 rank 4 for a query naming the Sanhita, because the short-title chunk is the only place in 531 sections where the Act's full name literally appears. **Conclusion on fine-tuning: now adequately supported by data volume and by a confirmed failure class (37% of misses are unreachable by any reranker or fusion retune), but it should not be the next experiment** — three cheaper changes address larger buckets, and one of them addresses a correctness risk rather than a quality metric. Recommended order: extend the topic-relevance guard to name un-ingested Acts, re-tune the confidence gate against citizen phrasing, add the deferred cross-encoder reranker, *then* re-attempt fine-tuning against the ~362-group labelled pool. Full write-up in `docs/RETRIEVAL_EVALUATION.md`'s "Citizen-language evaluation set expanded to 313 query groups". No training started, no retrieval code touched, nothing committed. 66/66 Python tests pass.

- **Corpus-coverage safety guard, confidence-gate calibration, and a rejected reranker (this update, uncommitted):** the 313-query evaluation committed in `4f7fd54` ranked three interventions ahead of embedding fine-tuning. All three were attempted this session. **One shipped, one was investigated and deliberately not changed, one was implemented, measured and rejected.** BM25, dense retrieval, RRF weights, the confidence threshold, the embedding model, the corpus, and the query dataset are all unchanged. **(1) Corpus-coverage guard — shipped.** `app/safety/corpus_coverage.py` runs in `handle_legal_query()` after the topic-relevance guard and before retrieval, closing the failure class the new `insufficient_evidence` category exposed: a query that genuinely *is* a legal question in this service's subject area but names an Act the corpus does not contain. Such queries share real legal vocabulary with real legal content, clear the dense-score floor, and get answered confidently from the wrong Act — the same structural problem `topic_relevance.py` exists for, one level harder, and equally unreachable by moving a bounded threshold. Six categories, one per demonstrated failure and nothing else: drunk driving (was answered from `bns:355`), divorce (`bnss:219`), caste atrocities (`constitution:16`), POCSO (`bns:198`), court fees (`bnss:400`), RTI (`q35`). **Hybrid false accepts 7 → 1; abstention accuracy 0.7572 → 0.7764; bm25-mode abstention on the 49-query control 0.9796 → 1.0000.** Retrieval-quality metrics verified byte-identical before/after on both eval sets, since the guard only changes pre-retrieval gating and never ranking. Every pattern was checked against real indexed corpus text first, because the obvious discriminators are unsafe — bare "divorce" appears in `bnss:144`/`bnss:146` (maintenance for a divorced woman), bare "drunk" is the literal subject of `bns:355`, bare "scheduled caste" appears in `constitution:15`/`16`/`46` and `lsa:12`, and bare "court fee" appears in `lsa:21` (Lok Adalat refund) — so only the specific procedure phrasings match, and the SC/ST entry keys off "atrocities" (zero corpus occurrences). Over-blocking is asserted rather than spot-checked: a test scans all 362 labelled queries across both eval sets and fails on a single fire against an `expect_abstain=False` row — measured **zero false fires**, plus zero across twelve hand-built adversarial near-miss probes. 8 tests in `tests/test_corpus_coverage.py`. One `topic_relevance.py` addition from the same evaluation: "who won the last general election in india" (`h279`) was answered from `constitution:58` on shared election vocabulary; two narrow patterns added to the existing `everyday_nonlegal` category, with bare "election" deliberately not matched (BNS ss.169-177 and Constitution Part XV are genuinely ingested — all five genuine election-offence phrasings verified to still pass). **Residual:** `h286` ("how do I file an application for information from a government office") still answers from `it_act:6` — the RTI question deliberately phrased without naming RTI, unreachable by a phrase guard, and now the sole remaining hybrid false accept. Five other un-ingested subjects (rent control, minimum wages, stamp duty, arbitration, labour notice) are deliberately absent because the score gate already abstains on them; adding them would be speculative rather than evidence-driven. **(2) Confidence gate — investigated, no change.** The 69 false abstains (57 of them `ordinary_citizen`/`colloquial`, on queries whose correct chunk *was* retrieved) looked like a calibration problem and are not. The gate signal is genuinely miscalibrated for citizen language (should-answer median 0.456 vs 0.648 for legal terminology, so the 0.42 floor sits above the 25th percentile of citizen queries deserving an answer) — but the citizen-language true-positive distribution sits almost exactly on top of the wrong-Act distribution (median 0.456 vs 0.442), so **no threshold separates them**. Swept 0.30→0.46: the true-positive-per-wrong-Act ratio is **flat at ~2.0 across the entire range**, meaning threshold movement slides along a line of constant trade-off rather than finding a better operating point. A second hypothesis — that the problem is *what* the gate reads, not the number — was also tested: `max` and `mean` of `dense_score` over the returned top-5 both trace the same curve (at zero false accepts, top-1@0.44 gives 177/43/21, max-of-5@0.45 gives 176/44/21, mean-of-5@0.40 gives 171/49/22). One tempting candidate (0.43, which removes the last false accept and two wrong-Act answers for five genuine answers) was **not** applied: moving a global threshold to catch a single labelled query is overfitting, and `h286` is a guard-shaped problem, not a threshold-shaped one. `DEFAULT_MIN_SCORE_BY_MODE["hybrid"]` stays 0.42. This is a useful negative result — it rules out the cheapest remaining intervention on measurement, and says the citizen-language gap is a representation problem surfacing in the gate, not a gate problem. **(3) Cross-encoder reranking — implemented, measured, REJECTED.** The candidate-pool premise was verified first and proved correct: of 130 relevant chunks hybrid misses at top-5 across both sets, **100 (76.9%) are inside the existing pool-50 candidate set**, so a reranker genuinely had access to three quarters of the misses. Built with `sentence-transformers` `CrossEncoder` (`ms-marco-MiniLM-L-6-v2`, local, no external API, flag-gated, reorders only — never adds or drops a candidate). A targeted experiment on 30 known fusion-ranking failures looked strong (66.7% improved rank, 50% newly in top-5, mean rank 13.6 → 10.4, FIR queries rank ~18 → 2), so the full evaluation was authorised. **Full result: +1.7pp recall@5 (0.6246 → 0.6412) bought at an unacceptable safety cost.** `hard_negative` recall@5 **0.966 → 0.793** (zero-hit groups 1 → 6); abstention accuracy **0.7764 → 0.6677** (false abstains 69 → 103); top-1 citation correctness 0.3879 → 0.3772; MRR 0.4874 → 0.4846. On the **49-query control it was worse on every single metric** (recall@5 0.8370 → 0.8074, MRR 0.7096 → 0.6996, nDCG@5 0.7227 → 0.7070, top-1 0.6222 → 0.6000, abstention 0.9796 → 0.9388) — not a trade-off, just degradation. Two of the five hard-negative regressions are the exact failure this product must never make: "bharatiya nagarik **suraksha sanhita** rules about taking bail" returned `bns:200`/`bns:209`, and "bharatiya **nyaya sanhita** list of punishments" returned `bnss:220`/`bnss:33` — queries naming their Act in full, answered from the other Sanhita. The short-title artifact also worsened (3 of 10 probes moved the boilerplate `:1` chunk closer to rank 1, only 1 away; `h259` regressed from a correct `pwdva:3` top-1 to the contentless `pwdva:1`), explicably, since a title-like passage naming the Act is exactly what an MS MARCO cross-encoder rewards. Per-query diff: 29 fixed, 25 broken — near parity in count but asymmetric in composition, fixing recall-flavoured categories and breaking the safety-flavoured one. Cost was also material: ~34 min vs ~4 min for the same evaluation, an ~8x wall-clock increase from 594 cross-encoder invocations, i.e. real per-query latency for a citizen-facing endpoint. **All reranker code was removed after measurement**; `app/retrieval/search.py` was restored byte-identically to `4f7fd54` and both eval sets re-run to confirm the production path is back to its exact baseline. **Status change worth carrying forward: reranking is no longer an untested deferral, it is a tested and rejected approach** — the candidate-pool argument is now known to be both true and insufficient, and a future attempt would need to answer the actual failure (a general-purpose reranker has no notion that BNS and BNSS are different statutes). 74/74 Python tests pass.

The application milestones below were tracked in the "Completed" section before they were recorded here; their hashes are:

- `89c9ffe` — M1 platform usability (legal assistant UI + authentication/email-verification frontend)
- `37cb48f` — M2 civic reporting core (citizen reporting, EXIF stripping, local media storage)
- `354533c` — M3 civic authority workflow (transition table, status history, priority/SLA, authority queue)
- `c3075eb` — M4 petitions and public participation (petition lifecycle, database-enforced signature uniqueness, moderation queue)
- **M5 — Live stack integration, real-database validation and end-to-end hardening (this commit):** the first milestone verified against a *running* system rather than against mocks. Four integration defects were found and fixed (all outside the retrieval pipeline); the RAG/retrieval system itself was frozen and is byte-identical. See "M5" under Completed.

## Completed (historical milestone timeline)

**Increment 1 — Foundation**
Monorepo, React+TS frontend, Tailwind, React Router, Node+Express backend, FastAPI AI-service boundary, auth/RBAC (Citizen/Authority/Admin), landing + login pages, shared contracts, Docker config, GitHub Actions CI, local storage abstraction, seed accounts, architecture + legal-source docs, basic tests.

**Increment 2 — Module 1A (legal ingestion + learning library)**
- Ingestion pipeline: `services/ai/app/ingestion/` (extract → clean → chunk → version → persist). Chunking verified against known text (BNSS §43(5), Constitution Art. 21).
- Corrected a real corpus error: the supplied `BNSS.pdf` was a superseded bill draft; replaced with the enacted Act No. 46 of 2023 text from India Code.
- Hybrid retrieval: `services/ai/app/retrieval/search.py`. BM25 always built (with a process-lifetime cache added in Module 1B, since chat calls it far more often than corpus browsing); dense embeddings (`sentence-transformers`) used if installed, else graceful degrade to lexical-only — this is recorded in `index_manifest.json`, never silently assumed.
- Folder-upload workflow: drop `raw.txt` into `services/ai/data/legal-corpus/<source_id>/`, run `python services/ai/scripts/ingest_corpus.py`. Nothing else needs to change to pick up new/updated source text.
- FastAPI endpoints: `GET /corpus/sources`, `GET /corpus/search`, `GET /corpus/sections/{source}/{unit}` — retrieval only, no LLM generation.
- Node proxy: `GET /api/corpus/*` forwards to the AI service, keeping the browser off the Python service directly.
- Frontend: `LearnPage`, `ArticlePage`, `DocumentBrowserPage` replace the `/learn` placeholder.
- 63 fully-grounded learning articles (`apps/web/src/content/learn/`), grouped into eleven categories: Constitution & Fundamental Rights; Police, FIR & Complaints; Arrest & Bail; Courts, Trials & Evidence; Everyday Citizen Rights; Consumer Rights; Digital & Online Rights; Women's Safety & Domestic Violence; Children & Young People; Legal Aid & Access to Justice; and Civic Participation. 189 grounded quiz questions (three per article) sit alongside them in `content/learn/questions/`, each explaining its answer from the same provision the article cites. Every paragraph cites an exact Article or section, and each article lists the official India Code source it was written against. Content is curated and static -- nothing on these pages is generated at request time.
- Tests: `services/ai/tests/test_ingestion.py`, `test_retrieval.py` (11 passing). Whole JS monorepo typechecks, existing tests pass, production build succeeds. AI test suite is now also enforced in CI (`.github/workflows/ci.yml`).

**Module 1B — Deterministic legal answers (no generative LLM)**
- `services/ai/app/generation/pipeline.py`: `handle_legal_query()` (Risk/UPL → retrieval → `build_legal_answer()`), the confidence gate (`LEGAL_CHAT_MIN_SCORE`, provisional — see its docstring for why no defensible cutoff exists in the current corpus/tokenization), and `build_legal_answer()` itself, which returns the verbatim retrieved chunk text plus real citations directly — no LLM call, no free text to validate, since nothing generates one.
- `services/ai/app/generation/context.py`: `distinct_sources()` only, repurposed as a grouping/labeling helper. Multiple or differing sources are returned as separate excerpts by construction (never merged into one synthesized paragraph), which is why the old design's "don't let the LLM merge conflicting sources" prompt instruction has no replacement — the problem it solved doesn't exist once nothing generates a paragraph.
- `services/ai/app/safety/`: the deterministic query-safety policy (`risk.py`), which runs before retrieval. It is no longer a flat category list: `assess_query()` combines a **subject** signal (life-threatening vs. serious-legal), a **framing** signal (informational / instructional / personal) and an **immediacy** signal, and returns one of four severities — `harmful_request` (obstruction or fabrication instructions; refused, no retrieval), `emergency` (helpline immediately, no retrieval, no legal analysis in front of it), `serious` (caution plus a legal-aid route, and retrieval still runs so the general law can be cited under it), and `normal` (straight through). This replaced a keyword ruleset that both answered "How can I hide evidence from the police?" as an ordinary question and blocked "Explain what the law says about domestic violence" as an emergency. `fabrication.py`'s pattern matcher was repurposed from a per-request runtime check into a one-time regression test (`test_template_safety.py`) against the small set of fixed, hand-written response strings, since nothing generates free text to check anymore. Prompt-injection detection (`safety/injection.py`) was removed entirely — it defended an LLM system prompt, and no prompt exists anywhere in this pipeline now.
- Endpoints: `POST /legal/answer` (AI service, public, disclaimer attached to every response) and its proxy `POST /api/legal/answer` (Node, own rate limiter, sized for cheap BM25 lookups rather than LLM-call cost).
- Removed entirely: `LLMProvider`/`MockLLMProvider`/`GeminiProvider`/`get_provider` (`generation/provider.py`, `generation/gemini_provider.py`), `requirements-gemini.txt`. This was real, tested integration work (the Gemini path was verified this session against the live API, including its failure path with an invalid key) — it is recorded here as history, not silently erased, but none of it ships.
- Tests: 39 AI-service tests (Module 1A + 1B), all pure-function or monkeypatched-retrieval — no provider/LLM mocking exists anywhere in the suite because there is nothing left to mock. Live-verified against the real corpus, including a genuine multi-source query (BNSS + Constitution) confirmed to return two separate, unmerged excerpts.

**Hybrid retrieval (BM25 + dense, RRF-fused)**
- `services/ai/app/retrieval/embeddings.py`: local dense-embedding wrapper (`sentence-transformers/all-MiniLM-L6-v2`, 384-dim, configurable via `DENSE_EMBEDDING_MODEL`), L2-normalized at encode time. `services/ai/app/retrieval/fusion.py`: weighted Reciprocal Rank Fusion (`k=5`, dense weighted 2x — deliberately tuned away from the RRF paper's k=60 default, which measurably underperformed at this corpus's ~400-chunk scale; see `docs/RETRIEVAL_EVALUATION.md`). `services/ai/app/retrieval/tokenize.py`: the one BM25 tokenizer, shared by index-build and query time (fixes a real bug found during evaluation — whitespace-only splitting left punctuation glued to words, e.g. `"estoppel."` never matching query token `"estoppel"`).
- `services/ai/app/retrieval/search.py`: `search(query, top_k, source_id, mode)` now supports `bm25` | `dense` | `hybrid` (auto-selects hybrid when a dense index exists); every result carries `retrieval_mode`, `bm25_score`/`bm25_rank`, and `dense_score`/`dense_rank` alongside the primary fused `score`, so fusion is inspectable without re-querying. Callers (including `generation/pipeline.py`) never need to know which mode produced a result — same cited-chunk dict shape throughout.
- `services/ai/app/ingestion/index_build.py`: now indexes `"{title}. {text}"` for both BM25 and dense (titles like "Estoppel" were previously never indexed at all, only body text — a second real bug found and fixed this session), while `Excerpt.text` shown to a citizen stays exactly the verbatim `chunk.text`, unchanged.
- `services/ai/app/ingestion/extract.py`: deterministic PDF text-layer extraction (`pypdf`, no OCR); `services/ai/app/ingestion/pipeline.py`'s `_ensure_raw_text()` auto-extracts a dropped `data/legal-corpus/<source_id>/raw.pdf` to `raw.txt` on first ingest, so an approved PDF can be dropped in directly instead of requiring hand-copied text.
- `services/ai/app/generation/pipeline.py`: confidence-gate floors are now per-mode (`DEFAULT_MIN_SCORE_BY_MODE`: bm25 3.0, dense 0.45, hybrid 0.40 — all evaluation-tuned). Hybrid gates on the top hit's `dense_score`, not its fused RRF score, because the fused score was measured to compress into a narrow, relevance-independent band on this corpus (see `docs/RETRIEVAL_EVALUATION.md`) — it decides ranking, not confidence.
- `services/ai/eval/`: `queries.jsonl` (30 hand-curated, hand-verified queries: direct-lexical, paraphrase, a lexical-distractor case, multi-source, and abstain-expected including out-of-domain controls) + `run_eval.py` (Recall@K, Precision@K, MRR, nDCG@K, top-1 citation correctness, abstention accuracy, per mode). Hybrid beat the BM25 baseline on every metric measured; full numbers and methodology in `docs/RETRIEVAL_EVALUATION.md`.
- Reranking and query preprocessing were both evaluated as candidates and explicitly deferred with documented reasoning (not silently skipped) — see `docs/RETRIEVAL_EVALUATION.md`'s "Reranking: deferred" and "Query preprocessing: deferred" sections.
- Tests: 57 AI-service tests (was 39) — added `test_fusion.py`, `test_extract.py`, `test_hybrid_retrieval.py`, plus new gate-behavior cases in `test_pipeline.py`. One pre-existing test (`test_search_finds_arrest_provision_for_sunset_query`) was changed from asserting strict rank-0 to asserting presence in the top-5 window, with a docstring explaining why (the product shows every returned excerpt, never just a single "best" one — see the test itself).
- Still pure retrieval, still no generative LLM anywhere: embeddings are retrieval infrastructure (ranking/matching), never answer generation.

**Corpus expansion (8 sources now full-text; two-column gazette layout solved)**
- Registered and ingested `it_act` (92 sections), `pwdva` (37), `lsa` (30) — single-column official PDFs, no layout issues, using the existing `chunk_sanhita` chunker.
- Fixed a real bug in `chunk_sanhita` (`app/ingestion/chunk.py`): consolidated "as amended" Act PDFs print each amendment's history as a numbered footnote (e.g. `"1. Subs. by Act 10 of 2009, s. 2, for ..."`), reusing small numbers that collided with real section numbers and produced bogus duplicate-numbered chunks (5 in `it_act`, 1 in `lsa`). Fixed with a content-based filter (`_FOOTNOTE_TITLE`) rejecting matches whose "title" opens with a standard amendment-drafting verb — a real section title never does.
- **Solved the two-column India Code gazette layout** shared by BNS/BNSS/BSA/CPA2019/JJ Act (an earlier attempt in this same uncommitted change got close but left too many artifacts to ship). `app/ingestion/extract.py`'s `extract_gazette_body_text()` uses `pdfplumber`'s real per-character page coordinates to: locate the note-column/body-column gap and the body-column/ruler gap independently *per page* (both drift slightly across a 200+ page Act, and the note is printed on alternating left/right margins like a bound book's running heads); keep only body-column words with `x_tolerance=1` (BNS/BSA's font has no real space glyph, which merges words at pdfplumber's default tolerance); reassemble each row by real vertical position instead of a fixed grid (fixes word-order scrambling that a naive fixed-width row-bucketing approach produced); and drop repeating page-header/footer boilerplate by content. Feeds the existing `chunk_constitution` numeric-boundary chunker.
- Result: **BNS 357, BNSS 533 (incl. FIR ch. XIII and bail ch. XXXV), BSA 170, CPA2019 107, JJ Act 111 — all matching or within 1 of the known official section count**, verified with a 90-section random-sample audit (60 BNS/BSA/BNSS + 30 CPA2019/JJ Act) finding only 1 residual artifact (a stray ruler digit in one BNSS section). One known limitation: BNSS section 337 is mislabeled as a duplicate "338" due to a rare digit-extraction fault on that one page (its body text is intact and correctly ordered).
- **Section titles recovered** (a separate, independent pass — see `extract_gazette_titles()`'s docstring for why it's decoupled from body extraction and therefore carries none of the fabrication risk a wrong body excerpt would): present for 40-57% of sections across the five two-column sources (exact per-source percentages in each `coverage_note`); absent, never guessed, for the rest. This directly fixed a real regression the evaluation set caught: "estoppel" (BSA s.121) was false-abstaining because losing that section's title also lost the only place the word "estoppel" appears in the indexed text.
- The RTI Act 2005 replacement PDF the user supplied was checked byte-for-byte and text-for-text against the original — identical (same SHA-256, same "(1)"→"(/)" font corruption). The swap did not take effect; RTI remains uningested pending a genuinely different file — do not spend further effort trying to repair this specific PDF.
- Corpus total: 554 → 1,783 chunks. `pypdf` upgraded 5.1.0→6.16.1 (needed mid-investigation; harmless elsewhere); `pdfplumber==0.11.10` added to `requirements.txt` (base, not `-full`, since 5 of 10 registered sources now need it for core ingestion, not just optional hybrid search).

**Retrieval/evaluation hardening**
- `eval/queries.jsonl` rebuilt from 30 to 49 queries covering all 9 ingested sources (RTI excluded except as an abstain-expected control) across direct_lexical, paraphrase, multi_source, ambiguous, out_of_domain, source_specific, and abstain_expected categories, including the 6 explicitly requested regression queries (FIR, bail, burden of proof, child-in-conflict-with-law, consumer complaint, RTI) in their exact wording.
- Investigated the recall drop the stale 30-query set showed after corpus expansion (0.90→0.69 at the time): confirmed it was an artifact of the old eval set being unrepresentative (built for a 4-source, ~430-chunk corpus, evaluated against a 1,783-chunk one), not hybrid retrieval regressing — on the rebuilt 49-query set, hybrid still beats both BM25 and dense individually on every metric (see "Evaluate" run below). No RRF weights or BM25 tokenization changes were needed or made.
- Found and fixed two real, evaluation-demonstrated gaps, both narrow and documented rather than broad new components:
  - `app/retrieval/query_expand.py`: a tiny curated abbreviation-expansion (FIR → "First Information Report", NCR → "Non-Cognizable Report"), applied at query time only, appending rather than replacing the original query. This was the documented trigger condition for revisiting `docs/RETRIEVAL_EVALUATION.md`'s "Query preprocessing: deferred" decision — "FIR" is the term nearly every citizen actually uses, but it appears almost nowhere in BNSS's own statutory text. Not a general synonym model or reranker.
  - The hybrid confidence floor was raised 0.40→0.42 (`DEFAULT_MIN_SCORE_BY_MODE` in `generation/pipeline.py`) after stress-testing genuinely out-of-domain queries against the larger corpus found 3 of 8 scoring above the old floor (topically-adjacent-word false positives, e.g. "How do I register a company in India?" matching a BNSS summons-service section because both mention "company"). Checked against every genuine query in the rebuilt eval set before changing it — none were pushed below 0.42 (the previously-lowest genuine score, q19, already failed at 0.40 too). This is not a full fix (two of the three stress-test false positives, both ~0.45, still pass — see Known gaps) and was a raise, not a lowering, specifically to close a demonstrated safety gap.
- Regression tests added: `tests/test_pipeline.py::test_hybrid_abstains_on_out_of_domain_score_that_used_to_pass` pins the exact 0.4117 score that used to pass.
- Final metrics on the rebuilt 49-query set (`python eval/run_eval.py`): hybrid recall@5 0.7407, precision@5 0.16, MRR 0.6341, nDCG@5 0.6324, top1_citation_correctness 0.5333, abstention_accuracy 0.9796 — beats BM25 (recall@5 0.6296, MRR 0.5693, abstention_accuracy 0.9184) and dense-only (recall@5 0.6741, MRR 0.557) on every metric except tying dense on abstention_accuracy. Zero false-answers in bm25/dense/hybrid on this set except bm25's 4 out-of-domain controls (expected — bm25 has no dense-score gate to fall back on). One remaining false-abstain (`q19`, pre-existing, not new).
- All 6 requested regression queries manually re-verified end to end: FIR, bail, burden of proof, child-in-conflict-with-law, and consumer complaint all now answer with a rank-1 (or, for FIR, rank-4-but-present) citation from the correct Act; RTI still correctly abstains.
- Full re-verification after all of the above: `python scripts/ingest_corpus.py` (1,783 chunks, mode=hybrid), 58/58 Python tests, Node tests, typecheck, and production build all pass.
- Not committed — working-tree changes only, per instruction.

**Retrieval ranking optimization (Constitution titles + RRF retune)**
- Ran a per-query failure analysis over the 49-query eval set's 45 non-abstain queries: compared BM25/dense/hybrid full rankings (not just top-5) against expected source/section for every query hybrid missed, classifying each by cause (vocabulary mismatch, missing title metadata, chunking, embedding quality, RRF weighting, confidence gating).
- Dominant cluster (9 of the failing queries): the Constitution's `chunk_constitution()` always set `title=""` — unlike the gazette sources, it had no title-recovery path at all. Fixed with `app/ingestion/chunk.py`'s `_KNOWN_ARTICLE_TITLES`, a small table covering Part III (Fundamental Rights, Articles 12-22 — the only part any eval query needs), hand-transcribed directly from the raw two-column-reordered PDF text and verified against each article's real body content. A general parser to recover all 346 articles was attempted and abandoned as unsafe (footnote/title/page-number blocks interleave in page-dependent order with no reliable general boundary — a wrong article-to-title mapping is a correctness risk, not just a missed optimization).
- Caught and fixed a real bug in the same change: `chunk_constitution()` is shared by every two-column gazette source (BNS/BNSS/BSA/CPA2019/JJ Act), so the title table initially leaked into them (e.g. `jj2015:14` briefly inherited Article 14's title instead of its own). Fixed by scoping the lookup to `source_id == "constitution"`; regression test added (`test_constitution_titles_do_not_leak_into_other_gazette_sources`).
- Re-swept RRF's k/dense-weight grid against the title-fixed index (same method as the original tuning, see `docs/RETRIEVAL_EVALUATION.md`): dense weight 2.0→2.5 (k unchanged at 5) — a clean improvement, not a trade-off.
- Hybrid recall@5 0.7407→0.8074, precision@5 0.16→0.1733, MRR 0.6341→0.6670, nDCG@5 0.6324→0.6734, top-1 citation correctness 0.5333→0.5556, abstention accuracy unchanged 0.9796. No new wrong-Act false positives (hybrid's false-answer list stayed empty). 60/60 Python tests pass.
- Reranking was re-evaluated against the new failure set and still explicitly deferred, not silently skipped — the two worst remaining misses (q17, q46) aren't even in either method's top-50 candidate pool, so a reranker couldn't reach them; the rest are minor, scattered rank perturbations, not a systematic "right answer buried in a good candidate list" pattern. Full writeup: `docs/RETRIEVAL_EVALUATION.md`'s "Failure-analysis-driven fixes" section.

**M1 — Platform usability (frontend/auth integration milestone)**
This milestone changed no AI/retrieval behaviour at all. It closed the gap between working backend functionality and what a user could actually reach in the browser. Nothing under `services/ai/` was modified (verified by `git status` and by the Python suite staying green).
- **Legal Assistant page** (`apps/web/src/pages/LegalAssistantPage.tsx`, route `/legal-assistant`, linked from the header nav and from `/learn`): the first frontend consumer of `POST /api/legal/answer`. It renders exactly what the backend returns — verbatim excerpt text, source, act number, section/article, official-source link, verified-as-on date, coverage note, and the backend's own distinct-source list — and nothing else. It does not summarise, paraphrase, reorder, merge or explain the retrieved law, so the "no generative LLM in the legal-answer path" decision holds on the frontend as well as in the service. All five `policy_decision` branches are handled: `answered`, `abstained`, `redirect_emergency`, `redirect_adviser` and `refused`. The framing is chosen from the response's structured `severity`/`authority_guidance` fields rather than by parsing the message string, so an emergency, a refusal and an ordinary abstention each read as what they are instead of looking like a "no results" shrug. A `serious` response leads with the caution and then shows the retrieved law beneath it, labelled as general information. The disclaimer shown is the one carried on the response (`disclaimer_text` + `disclaimer_version`), not a hardcoded copy. The page is public, matching the endpoint's deliberate no-login design.
- **Email-verification deadlock — fixed.** Registration created accounts with `emailVerified: false`, login rejected unverified accounts, and nothing ever issued a verification challenge, so *every* self-registered account was permanently locked out; only `seed.ts` accounts could sign in. `services/api/src/lib/email-verification.ts` now issues a 32-byte random token at registration, persists only its SHA-256 hash (`emailVerification.tokenHash`, `select: false`) with a 24-hour expiry, and `POST /api/auth/verify-email` consumes it. **Chosen development behaviour, deliberately documented:** this project has no mail transport (nodemailer is a dependency that nothing imports), so outside production the raw token is returned in the register/resend response (`verification.deliveredVia: "api-response"`) and the frontend carries it straight to `/verify-email`. `devVerification()` returns `undefined` when `NODE_ENV === "production"`, so a deployed instance never leaks a token over the API. Wiring a real provider later means mailing `token` from those two handlers — no other part of the flow changes. No external infrastructure was invented. `POST /api/auth/resend-verification` covers a lost or expired token and answers identically whether or not the address exists, so it cannot be used to enumerate accounts.
- **Frontend auth state**: `apps/web/src/auth/AuthContext.tsx` plus `lib/auth-storage.ts`. The JWT is persisted in `localStorage` (same key the old LoginPage already used) and attached to every request by an axios interceptor in `lib/api.ts`; a 401 on a request that actually presented a token clears the session. The user object is never cached alongside the token — it is always re-fetched from `GET /auth/me`, so a revoked token cannot leave a stale signed-in shell on screen. `RegisterPage`, `VerifyEmailPage` and `AccountPage` are new; `LoginPage` now drives the context and routes the user onward instead of printing a placeholder message; `SiteShell` shows the signed-in user and a working log-out.
- **Protected routes**: `components/ProtectedRoute.tsx` guards `/account` (the only route that genuinely needs an account today). It waits for the session check to resolve before deciding, so refreshing a protected page does not bounce an authenticated user to `/login`, and it deliberately does **not** guard the legal-answer page.
- **Design decisions taken here** (smallest option consistent with existing architecture, per the milestone brief): token in `localStorage` rather than an httpOnly cookie, because switching would mean changing backend auth (cookie issuance + CSRF) — the exposure is bounded by the 15-minute token lifetime; verification does not auto-login (it proves address control, not identity); API auth tests mock the Mongoose model rather than adding `mongodb-memory-server`, and web tests use `fireEvent` rather than adding `@testing-library/user-event` — no new dependencies were added in this milestone.
- **Tests added**: `services/api/src/routes/auth.test.ts` (14 tests — registration success/invalid/duplicate, verify-email success/expired/unknown, resend + non-enumeration, login success/unverified/wrong-password, `/auth/me` unauthenticated/malformed-token/valid) and, on the web side, `auth/AuthContext.test.tsx` (6), `components/ProtectedRoute.test.tsx` (3), `pages/LoginPage.test.tsx` (4), `pages/RegisterPage.test.tsx` (5) and `pages/LegalAssistantPage.test.tsx` (9 — render, validation, submit, answer + citations, loading, abstention, emergency redirect, 503, 429). Node API 5 → 19 tests, web 1 → 28 tests.
- **Also fixed**: `apps/web` ran vitest without `globals`, so Testing Library could never register its automatic cleanup and renders leaked between tests. `apps/web/src/test/setup.ts` now calls `cleanup()` in an `afterEach` (wired via `vite.config.ts`). This was latent — the suite had only one test before, so nothing had exposed it.

**M2 — Civic reporting core (Module 2, first end-to-end slice)**
A citizen can now authenticate, file a civic report with an optional photo and a location, and track it. The legal/RAG pipeline is untouched by this milestone -- nothing under `services/ai/` is modified and the Python suite stays green. Civic CRUD deliberately does **not** pass through the Python service: there is no AI in this path yet, so the browser talks to Node, and Node talks to MongoDB and local disk.
- **Contracts** (`packages/contracts/src/civic.ts`, re-exported from the package index): closed enums for 8 categories, 5 statuses and 3 priorities, `createCivicReportSchema` (the single validator both the form and the API use), shared media limits (JPEG/PNG, 5 MB), and the `CivicReport`/`CivicMedia` response types. Coordinates use `z.coerce.number()` because the create endpoint accepts multipart/form-data, where every field arrives as a string. `reporterId` is deliberately absent from the input schema.
- **Model** (`services/api/src/models/civic-report.ts`): location is stored as GeoJSON `{ type: "Point", coordinates: [lng, lat] }` with a `2dsphere` index, so "reports near me" and duplicate clustering are possible later without a migration -- but no GIS infrastructure was added. Indexes: `reporterId`, `status`, `createdAt`, the compound `{ reporterId, createdAt: -1 }` that the only list query uses, and the geospatial index. Media is an embedded subdocument array holding storage references only; the bytes live on disk.
- **API** (`services/api/src/routes/civic.ts`): `POST /api/civic/reports` (CITIZEN only), `GET /api/civic/reports/mine`, `GET /api/civic/reports/:id`, and `GET /api/civic/reports/:id/media/:mediaId`. `reporterId` always comes from the verified JWT; a client-supplied one is not in the schema and is dropped. Status and priority are server-set (`SUBMITTED`/`MEDIUM`) and cannot be chosen by the client. A citizen requesting someone else's report gets **404, not 403**, so report ids cannot be enumerated. Report creation has its own rate limit (20 per 15 min) on top of the app-wide one.
- **Media and privacy** (`services/api/src/lib/image-sanitize.ts`): a phone photo's EXIF block routinely carries GPS coordinates and device identity. The citizen chose what location to put on the report; they did not choose to publish where they were standing. So metadata is stripped **before** the file is persisted -- the original bytes never reach disk. JPEG APPn/COM segments and PNG `tEXt`/`zTXt`/`iTXt`/`eXIf`/`tIME` chunks are dropped by a hand-written container walk; image data is copied through untouched and never re-encoded. **No image-processing dependency was added** (no sharp, no exiftool) -- the audit found none present, and a native image stack is a large dependency for a well-specified container edit. Consequence: only JPEG and PNG are supported, which is exactly the allow-list. Content type is verified from magic bytes and must agree with the declared type. `LocalFileStorage` was extended narrowly (a `read()` method with a resolved-path containment check) rather than replaced.
- **Frontend**: `/report` (the old placeholder is gone), `/reports/mine` and `/reports/:id`, all behind `ProtectedRoute` -- a report has an owner, so these need an account. Browser geolocation fills the latitude/longitude fields via a "Use my location" button; **no map library and no reverse geocoding** were added. Report media is not public, so `components/AuthedImage.tsx` fetches image bytes through the authenticated axios instance and renders them from an object URL rather than using a bare `<img src>` that could not send a token.
- **Tests added**: 24 civic API tests, 7 image-sanitiser tests (including a fixture carrying a known GPS string that must not survive to storage), 7 storage-safety tests against a real temp directory (traversal, absolute paths, cross-scope reads, no-overwrite), 12 `ReportPage` tests and 5 `MyReportsPage` tests. Node API 19 -> 57, web 28 -> 45.
- **Deliberately not built** (deferred, per the milestone brief): authority dashboard, status transitions, SLA, duplicate detection, image similarity, face/number-plate masking, automatic classification or priority prediction, analytics, notifications, Redis, cloud storage, maps.

**M3 — Civic authority workflow (Module 2, second slice)**
A report now has a life beyond SUBMITTED: an authority reviews it, moves it through a deterministic state machine, and the citizen can see what happened and why. The legal/RAG pipeline is untouched again -- nothing under `services/ai/` is modified and 74/74 Python tests still pass. No new dependency was added.
- **State machine** (`packages/contracts/src/civic.ts`): eight declared transitions are the single source of truth, shared by the API (which enforces them) and the UI (which renders actions from them). The existing five-status vocabulary was kept rather than adding `ACCEPTED`, so no contract churn. `SUBMITTED -> UNDER_REVIEW | REJECTED`; `UNDER_REVIEW -> IN_PROGRESS | REJECTED`; `IN_PROGRESS -> RESOLVED | UNDER_REVIEW`; and, **ADMIN only**, `RESOLVED | REJECTED -> UNDER_REVIEW` (reopen). Rejection, resolution, send-back and reopen each require a written reason. **CITIZEN appears in no rule at all**, so a citizen cannot move a report as a property of the table itself rather than of a middleware check somebody could forget on a future route. ADMIN has more reach than AUTHORITY but travels the same table -- there is no arbitrary "set status" endpoint anywhere.
- **Status history** (embedded in `CivicReport`): every status and priority change appends `{ type, from, to, actorId, actorRole, note?, at }`. Entries are built server-side from the authenticated actor and the server clock; nothing from a request body reaches them except the note. **Embedded rather than a separate collection**, deliberately: history is only read with its report, is written only by the workflow service, and is bounded by the state machine's shape -- and keeping it in one document is what makes the conditional update below safe without a transaction. Promoting it to its own collection later is contained (one writer, one reader). `actorId` is returned only to AUTHORITY/ADMIN viewers; a citizen sees the acting role and the reason, not which member of staff acted.
- **Priority and SLA**: priority stays **staff-assigned, not inferred**. Automatic assignment was considered and rejected — the only signals at submission are category, free text and coordinates, and this project has no evidence base for mapping any of them onto real urgency; a category table that silently called every "water" report HIGH would look objective while encoding a guess, and in a queue that ordering decides what gets attention first. SLA mechanics are implemented regardless: HIGH 48h, MEDIUM 120h, LOW 240h, with `dueAt` always re-derived from `createdAt` (re-prioritising a week-old report does not hand it a fresh window). Overdue = past the deadline **and still open**, so closed reports do not accumulate a growing breach count. The helpers are pure and take `now` as a parameter, so the tests use fixed instants and nothing depends on the machine's timezone.
- **API added**: `GET /api/civic/authority/reports` (queue: status/category/priority/overdue filters, three sorts, capped pagination), `POST /api/civic/reports/:id/transitions`, `PATCH /api/civic/reports/:id/priority`. History travels on the existing report responses rather than a separate endpoint. Authority scope is documented as **one authority seeing all categories** -- the project models a single civic body, and inventing wards/departments/escalation chains would be inventing a government structure the project never specified.
- **Concurrency**: transitions use a conditional `findOneAndUpdate` filtered on the status the decision was made against, so if another authority moves the report in between, the write matches nothing and the API answers **409** instead of silently overwriting their transition.
- **Frontend**: `/authority` (queue with server-side filtering) and `/authority/reports/:id` (detail with only the transitions valid from the current state, note enforcement, priority control, full history), both behind a role-gated `ProtectedRoute`. Citizen pages now show the deadline badge and the full status history, so a report explains itself. `ProtectedRoute` gained an optional `roles` prop -- it hides the UI, it is not the security boundary; the API re-authorises everything.
- **Two security issues found and fixed during the Phase 7 review** (both with regression tests): route params typed `string | string[]` were passed straight to `isValidObjectId`, so all id handling now goes through one `objectIdParam` narrowing helper; and priority could be changed on a closed report, moving a finished report's deadline and appending history to it, which is now refused.
- **Tests**: Node API 57 -> 115, web 45 -> 64. Includes every declared transition exercised for every role it declares, an exhaustive sweep asserting every undeclared status pair is rejected, a sweep proving a citizen can move nothing from any state to any state, history-forgery attempts, the 409 conflict path, actor-identity visibility per viewer role, SLA arithmetic against fixed instants, and the two regressions above.

**M4 — Petitions and public participation (Module 3)**
Citizens publish petitions, sign each one at most once, and follow what the authority does with them; the authority moderates through a deterministic state machine and can see the support each petition has gathered. The legal/RAG pipeline is untouched again -- nothing under `services/ai/`, `data/index/` or `data/legal-corpus/` is modified and 74/74 Python tests still pass. **No new dependency was added**, and no AI is involved anywhere in this module: there is no petition recommendation, no clustering, no classification and no generated petition text, so the browser talks only to Node and nothing is routed through the Python service.
- **State machine** (`packages/contracts/src/petitions.ts`): five statuses (`OPEN`, `UNDER_REVIEW`, `ANSWERED`, `CLOSED`, `REJECTED`) and eight declared transitions that are the single source of truth, shared by the API (which enforces them) and the UI (which renders its action list from them). `OPEN` is the only signable state; `ANSWERED` is the only terminal one; `REJECTED` is the only non-public one. The declared moves are `OPEN -> CLOSED | UNDER_REVIEW | REJECTED`, `UNDER_REVIEW -> ANSWERED | CLOSED | REJECTED`, `CLOSED -> OPEN` and `REJECTED -> OPEN` (the last two ADMIN-only). Every transition except `OPEN -> UNDER_REVIEW` requires a written reason, which is published on the petition.
- **Keyed by capability, not role** -- the one structural difference from the civic transition table, and the reason for it is that a petition has a relationship a report does not: a creator. `petitionCapabilityFor(role, isCreator)` derives `CREATOR | AUTHORITY | ADMIN | null` server-side, from the authenticated user id compared against the *stored* `creatorId`; a citizen who is not the creator maps to no capability, appears in no rule, and can therefore move nothing -- a property of the table itself rather than of a middleware check a future route could forget. **Creatorship is checked first on purpose, so nobody adjudicates their own petition**: a staff account that published a petition before being promoted keeps the creator's single power (closing it) and loses its staff powers over that one petition only, while colleagues can still moderate it.
- **Two collections, deliberately** (`services/api/src/models/petition.ts`, `signature.ts`): signatures are **not** embedded in the petition. MongoDB cannot enforce uniqueness *within* an array, so "one signature per citizen per petition" would have rested on application logic; a separate collection gets a real unique compound index on `{ petitionId, citizenId }` enforced by the database. Embedding would also make a successful petition's signer list unbounded against the 16 MB document ceiling, and would drag the whole list into every listing read that only wants a count. Lifecycle `history` *is* embedded, for the same reasons `CivicReport.history` is. Petition indexes: `creatorId`, `status`, `{ creatorId, createdAt: -1 }`, `{ status, createdAt: -1 }`, `{ status, signatureCount: -1 }`, `{ status, category, createdAt: -1 }`. Signature indexes: the unique `{ petitionId, citizenId }` and `{ citizenId, createdAt: -1 }`.
- **Signature integrity** (`services/api/src/services/petition-signatures.ts`) is the security-critical part of the module, because a signature count is the only thing a petition asserts about the world. The signer is always the JWT subject -- **no code path anywhere reads a signer identity from a request**. "Have you signed already?" is never asked as a precondition and then acted on: that is check-then-act and it loses under concurrency, so the insert is simply attempted and the database rejects the loser with a duplicate-key error (E11000), which means exactly one of N racing requests can win whatever N is. The count is adjusted with `$inc` (atomic), so concurrent signers cannot lose each other's updates.
- **Ordering and compensation, in place of a transaction**: the deployment target (`docker-compose.yml`) runs a standalone `mongod`, and MongoDB multi-document transactions require a replica set, so a transaction was *not available* rather than passed over. Signing inserts the signature first and increments second, so the overwhelmingly common failure (the same citizen signing twice, i.e. a double-clicked button or a replayed request) fails atomically at the index and needs no compensation; the rarer race -- the petition closing mid-request -- is caught by making the increment conditional on the petition still being `OPEN`, and the just-inserted row is deleted if it matches nothing. Withdrawal is the mirror image (decrement first, then delete, compensating the decrement back if the delete removes nothing). **The residual risk is bounded and one-directional**: a process death between insert and increment leaves the count *lower* than the number of signature rows, never higher, and the `Signature` collection remains the source of truth, so a recount is a single aggregation. An inflated count would be a correctness failure; a conservative one is a recoverable inaccuracy.
- **API** (`services/api/src/routes/petitions.ts`): `POST /api/petitions` (CITIZEN only), `GET /api/petitions` (public), `GET /api/petitions/mine` (`created` | `signed`), `GET /api/petitions/authority` (AUTHORITY/ADMIN queue, with category/status/`goalMet` filters), `GET /api/petitions/:id` (public), `POST /api/petitions/:id/signatures` (CITIZEN), `DELETE /api/petitions/:id/signatures/me` (CITIZEN), `POST /api/petitions/:id/transitions` (authenticated; the workflow decides). **Reading is public, acting is not** -- browsing needs no account because the point of a petition is to be seen. Lifecycle change is modelled as *creating a transition* rather than PATCHing a status field, and there is deliberately no endpoint anywhere that assigns an arbitrary status. Staff are refused both creation and signing by role, because the authority is the body being petitioned and its own petitions or signatures would corrupt exactly the signal it is meant to read.
- **New middleware** (`optionalAuth` in `services/api/src/middleware/auth.ts`): populates `request.auth` when a valid token is present and continues either way, for the two genuinely public endpoints that still render differently for a signed-in citizen (the list and the detail both report `hasSigned`). An invalid or expired token is treated as anonymous rather than as an error, so a stale session degrades a public page to its public view instead of breaking it. It grants no access on its own and every privileged branch behind it re-checks the identity it finds.
- **Server-controlled fields**: `creatorId` comes from the JWT and `creatorName` is read from that account's own record; `status`, `signatureCount`, `history` and both timestamps are server-set. None of them appear in any input schema, and both input schemas are `.strict()`, so a client-supplied `creatorId`/`status`/`signatureCount`/`history`/`actorId`/`at` is a **400, not a silently discarded field**. History entries are built from the derived capability and the server clock; nothing from a request body reaches them except the note. The only client-chosen number is `signatureGoal`, which is the creator's own target, grants no privilege and is bounded (10..100,000).
- **Removed petitions** (`REJECTED`) stay visible to their creator (so they can read why) and to staff (so the decision stays auditable), but not to anyone else -- republishing removed material would defeat the point of removing it. A viewer who may not see one is answered **404, not 403**, so the endpoint cannot confirm that a particular removed petition was ever published. The public list excludes them structurally (the status filter is intersected with the public statuses rather than trusted from the query), and the "signed by me" list applies the same rule, so signing something is not a second route to content moderation took down.
- **Concurrency on transitions**: the same conditional `findOneAndUpdate` the civic workflow uses, filtered on the status the decision was made against, so a petition moved by somebody else in between produces a **409** rather than a silently overwritten action.
- **Rate limiting**, keyed by authenticated user id rather than IP (an IP key both punishes citizens behind a NAT and is trivially sidestepped): publishing 10/hour, signing and withdrawal 60/15 min, workflow actions 120/15 min.
- **Frontend**: `/petitions` (public browse with server-side category/status/sort filters and pagination), `/petitions/:id` (public detail, signing, withdrawal, capability-derived action panel, full history), `/petitions/new` (CITIZEN-gated), `/petitions/mine` (created/signed tabs, paginated) and `/authority/petitions` (AUTHORITY/ADMIN-gated queue with the `goalMet` triage filter). The old `/petitions` placeholder is gone. There is **one** petition detail page rather than a public one plus a near-identical staff one, because the difference between them is entirely "which actions are available" and that answer already exists in the shared table -- so `petitionTransitionsFor(status, capability)` renders exactly the moves the API will accept, and a reader with no capability sees no action panel. None of that is a security boundary: the API independently re-derives the same capability and re-authorises every action. The nav's "Authority queue" link was renamed "Report queue" now that there are two queues.
- **No edit and no delete endpoint**, deliberately: people sign a specific text, so letting it be rewritten afterwards would misrepresent what they supported, and removal is moderation (`REJECTED`, with a published reason and a reversible ADMIN reinstate) rather than destruction. The create form says so on screen.
- **Two issues found and fixed while recovering this milestone** (both with regression tests): the "signed by me" list paginated over raw signature rows while filtering removed petitions out of the result, so `total` counted petitions the page could never show and a page could come back short -- it now paginates over the petitions actually visible to the viewer; and `MyPetitionsPage` printed a total it had no controls to reach, silently truncating a citizen with more than 20 petitions -- it now paginates like the other two lists. `*.tsbuildinfo` was also added to `.gitignore`, since `tsc -b` had left an untracked build artefact in `services/api/`.
- **Tests**: Node API 115 -> 233, web 64 -> 129. Includes every declared transition exercised for every capability it declares, an exhaustive sweep asserting every undeclared from/to pair is rejected, a sweep proving a non-creator citizen can move nothing from any state to any state, a staff-creator conflict-of-interest case, forged actor/timestamp/history/status/count attempts, the 409 conflict path, 2-way and 5-way concurrent duplicate signing by one citizen, 2-way and 10-way concurrent signing by different citizens, racing withdrawals, a sign/withdraw/sign cycle asserting the count still matches the rows, the mid-request close compensation, IDOR attempts on both `mine` filters, malformed-ObjectId handling on every id route, pagination and filter boundary validation, public-vs-staff visibility of removed petitions and of actor identity, and frontend happy paths plus loading/error/empty states for all five pages.
- **Deliberately not built** (no instruction to): petition comments or discussion, petition categories beyond the closed enum, signature verification beyond an authenticated account (no address, constituency or identity check), petition-to-report linking, DBSCAN clustering or any petition recommendation agent, notifications, analytics, sharing/embedding, and petition search (the list filters by category and status but has no free-text search).

**M5 — Live stack integration, real-database validation and end-to-end hardening**
- **What makes this milestone different:** M1-M4 were verified by unit/integration tests that mocked Mongoose. M5 is the first milestone verified against a **running system** — five containers, a real `mongod`, the real AI service, and a real browser session. Its purpose was not to add features but to prove the application already built actually works as one integrated system. **No product features were added.**
- **The live stack runs.** `docker compose up -d` brings up all five services healthy: `mongo` (7.0, healthcheck passing), `redis` (7.4, healthcheck passing), `api`, `ai` and `web`. Service-to-service connectivity was verified *from inside* the API container: `api -> ai` over Compose DNS, `api -> mongo` (`ping {ok:1}`), and `api -> redis` (`+PONG`). Uploads persist to the `uploads_data` volume, CORS admits only `WEB_ORIGIN`, helmet's CSP/HSTS/`nosniff` headers are present, and the nginx SPA fallback serves deep links.
- **Real MongoDB validation — 22/22, closing the single highest-value missing test (gap #50).** Against the live database: every declared index actually exists (`civicreports` including the `location_2dsphere` geo index and the `status+dueAt` queue index; `petitions` including all four compound browse indexes; `signatures` including the **unique `{petitionId, citizenId}` compound index**; `users.email` unique). Schema enforcement was exercised for real rather than asserted in code: required fields, every enum (category/status/priority/role/media MIME), the custom GeoJSON coordinate-range validator, `maxlength`, and `min` on `signatureGoal` all reject. `isDuplicateKeyError()` recognises the genuine driver E11000.
- **Signature integrity proved under real concurrency.** 12 simultaneous sign attempts by one citizen on one petition produced 1 success and 11 `ALREADY_SIGNED`, and **direct database inspection afterwards** confirmed exactly one signature row with `signatureCount = 1`. A 10-distinct-citizen race produced exactly 10 rows and a count of 10. This is the claim M4 could only make against a fake that emulated the index.
- **`Model.init()` startup fix — a real, demonstrated reliability defect.** `server.ts` connected and began serving before indexes were built. Mongoose's `autoIndex` builds them in the background and surfaces a failure only through an event nothing was listening for. Reproduced end to end: with the unique index dropped and conflicting rows present, the API started **clean, silent and healthy** — and one citizen then signed the same petition **five times, inflating the count to five**, because the index *is* the entire control and the application has no fallback. `start()` now awaits `Model.init()` for `User`, `CivicReport`, `Petition` and `Signature` before `listen()`. Verified both ways: normal startup is unaffected, and the broken-index case now logs the full duplicate-key error and refuses to serve traffic. (Note: `npm run dev` uses `tsx watch`, so the container stays up while the server never listens; a production start would exit.)
- **API Docker image fix.** `services/api/Dockerfile` copied `/workspace/services/api/node_modules`, a directory npm never creates under this workspace layout because dependencies are hoisted to the root — so the API image had **never built successfully**. The line was removed.
- **`AI_SERVICE_URL` fix.** `docker-compose.yml` never set it, so inside the API container `env.ts` fell back to `http://localhost:8000` — the API itself, not the AI service. Added `AI_SERVICE_URL: http://ai:8000`. The AI service's gitignored build artefacts (`data/index/`, `data/legal-corpus/`) are now bind-mounted read-only rather than baked into the image.
- **`sentence-transformers` dependency fix (narrowly approved change inside the otherwise-frozen AI area).** `services/ai/Dockerfile` installed `requirements.txt`, which omits the optional dense dependency, while the built index declares `mode: "hybrid"` — so `/legal/answer` failed in the container with `ModuleNotFoundError: sentence_transformers`. This was **stale packaging, not a deliberate production choice**: the base/full split predates hybrid retrieval, and the Dockerfile was never updated when hybrid became the evaluated production configuration. Fixed by installing `requirements-full.txt`, which is exactly `requirements.txt` plus that one package (dev extras live in `requirements-dev.txt`, fine-tuning extras in `requirements-finetune.txt`, and the production app imports none of them).
- **`RETRIEVAL_MODE=bm25` was tested as a workaround and REJECTED on safety grounds.** It is the obvious way to avoid the missing dependency and it silently destroys the out-of-domain guarantee: the hybrid confidence gate is load-bearing on `dense_score`, which lexical-only mode cannot produce. Measured directly — "What is the best pizza topping in New York?" abstains (`insufficient_evidence`) under hybrid but returns **five confident excerpts from four different Acts** under bm25-only. **Do not reintroduce a lexical-only fallback as a way around a packaging problem.**
- **Retrieval behaviour is unchanged and was never touched.** The existing index loads exactly as built (1,801 chunks, `all-MiniLM-L6-v2`, 384-dim, `mode=hybrid`); `RETRIEVAL_MODE` remains **unset** so the service auto-selects hybrid on its own; a live query runs in `retrieval_mode=hybrid` with `dense_score` present for the gate. **Zero changes** to BM25, dense retrieval, RRF, thresholds, safety guards, the corpus, the index, embeddings, evaluation datasets or fine-tuning — verified by diff, not by assertion.
- **API smoke test against the live stack:** 58 requests, 67/69 checks passing; both flagged items were test-side, not defects (`act_no` is legitimately empty for the Constitution, which has no Act number, and a hand-minted token was correctly rejected for lacking the required `iss`/`aud`). Covered auth (register -> development verification -> login -> `/me`, plus expired, malformed, wrong-secret and `alg=none` rejection), legal (answered, abstained, citations, disclaimer), civic (creation with image, media persistence, IDOR, path traversal, MIME spoofing, priority, valid and invalid transitions, concurrent transitions where exactly one wins) and petitions (creation, browse, signing, duplicate rejection with no count inflation, withdrawal, moderation, lifecycle, authorisation boundaries).
- **Browser smoke test:** 18/18 checkpoints through a real Chrome session with zero console errors — landing, registration, verification, login, Legal Assistant (real AI response with citations, official-source links and disclaimer), civic report creation with image upload (blob confirmed loaded), My Reports, authority queue, the full authority workflow (priority change moving the SLA deadline, a transition recorded in history with actor and note, next valid actions updating), petition browse/create/sign, My Petitions, authority petition queue, and logout clearing the token with protected routes redirecting.
- **Security review against the running system.** Verified: forged `reporterId`/`status`/`priority` on report creation are ignored (server-derived); forged `creatorId`/`signatureCount`/`status`/`creatorName` on petition creation are rejected outright by the strict schema; cross-citizen IDOR on reports and media returns 404; media requires auth and rejects path traversal; SVG-declared-as-PNG is rejected 415; role boundaries hold on every authority route. **Documented at M5, fixed in M6:** the JWT `role` claim was trusted without a database re-check, so a validly-signed token claiming `AUTHORITY`/`ADMIN` was accepted for a CITIZEN account, and a role change or account deletion was not reflected until the 15-minute token expiry. M6 added `User.tokenVersion` + a `ver` token claim and re-reads the stored role on privileged routes (see "M6 — engineering hardening" below); `docker-compose.yml` no longer hardcodes the secret, and production refuses to boot with the development placeholder.
- **Tests unchanged at M5:** API 233, web 129, Python/RAG 74 — all still passing, with typecheck and production build clean. M5 added no test files; its evidence is the live-system verification recorded above. (The Learn expansion and M6 later raised these to API 265, web 155, Python/RAG 74.)

### M6 — engineering hardening (verified against the live stack)

Production-readiness work. **No product behaviour changed, and the frozen
RAG system was not touched** — `git status` on `services/ai/` shows only
`Dockerfile` and a new `.dockerignore`, both packaging, with retrieval,
corpus, embeddings, thresholds, safety gates, evaluation sets and
fine-tuning all byte-identical.

- **Token freshness and revocation.** `User.tokenVersion` (default 0) is
  embedded in the access token as `ver`. `requireFreshRole(...)` re-reads
  `{ role, tokenVersion }` from the database on privileged routes,
  rejects a superseded token version, and replaces `request.auth.role`
  with the stored value so authorisation uses stored fact, not the
  token's claim. Bumping a user's `tokenVersion` revokes their live
  tokens. Ordinary citizen requests keep the stateless path. This closes
  the M5 finding above. 10 tests in `src/middleware/auth-freshness.test.ts`.
- **Environment guards.** Production refuses to start with the
  development `JWT_SECRET` or a wildcard `WEB_ORIGIN`; `parseEnv()` is
  exported so this is testable. `docker-compose.yml` now reads secrets
  and addresses from the environment with local defaults, documented in
  a new root `.env.example`. 6 tests in `src/config/env.test.ts`.
- **Observability.** One pino instance with redaction at the logger
  (`authorization`, `cookie`, `password`, `passwordHash`, `token`,
  `tokenHash`), `pino-http` request logging with a request id and
  outcome-graded levels, path-only logging so legal query strings are
  never recorded, and AI-proxy failure logging that omits the question.
  5 tests in `src/lib/logger.test.ts`.
- **Health and lifecycle.** `/health` is dependency-free liveness;
  `/health/ready` reports MongoDB connectivity and answers 503 when
  degraded. SIGTERM/SIGINT drain the server, close Socket.IO and
  disconnect Mongoose with a 10s backstop. MongoDB connection events are
  logged.
- **MongoDB transactions deliberately not adopted.** Signing is protected
  by a unique index plus atomic `$inc` with compensating writes;
  status changes are single-document conditional updates. Neither needs a
  transaction, so no replica set was configured. Reasoning recorded in
  `docs/ARCHITECTURE.md`.
- **Image and context hygiene.** The AI image installs CPU-only PyTorch
  (the CUDA wheel was ~2 GB the service never loads; there is no GPU in
  the stack and `embeddings.py` never selects a device). `.dockerignore`
  files cut the root build context 330.0 MB → 0.9 MB and the AI context
  111.6 MB → 0.1 MB, verified statically against every `COPY` source. The
  embedding model is cached in a named volume rather than baked in.
- **CI.** pip caching, a concurrency group, and a `git diff --check`
  step; a separate weekly/on-demand `integration.yml` builds the stack
  and smoke-tests health, readiness, an in-domain answer and an
  out-of-domain abstention. Retrieval evaluation stays out of CI.

- **Database integration tests.** The petition signature guarantee is
  enforced by a unique index in MongoDB, so a mock cannot verify it: the
  unit suite's signature fake throws a real E11000 and would behave
  identically against a schema carrying no index at all. A 13-test suite
  (`src/services/petition-signatures.integration.test.ts`) now runs
  against a real `mongod` and asserts the index exists and is unique,
  that a duplicate insert is refused, that 12 concurrent `signPetition`
  calls by one citizen produce exactly one row with `signatureCount` 1,
  that 12 distinct citizens produce 12, that a non-`OPEN` petition
  records nothing, and that the enum validators and the unique
  `users.email` index hold. Confirmed non-vacuous by mutation: removing
  `unique: true` from the schema fails exactly the four tests that assert
  the guarantee, including the count-inflation one.

  `mongodb-memory-server` was evaluated first and rejected on cost, not
  capability — it does start a genuine `mongod`, but it pulled 37 packages
  and a 781 MB MongoDB 8.2.6 archive, and validated against a different
  server version than the `mongo:7.0` this project deploys. The suite
  instead connects to a server that already exists (`MONGODB_TEST_URI`,
  defaulting to localhost), which the README's setup step and the CI
  service container both provide. It uses its own database name and drops
  it afterwards, so it never touches development data. Kept out of
  `npm test` behind `npm run test:integration` so the unit suite stays
  infrastructure-free.

**Verification performed (Docker daemon available this session):**

| Check | Result |
| --- | --- |
| `docker compose build` | succeeded, all three images |
| AI image size | **8.61 GB — 2.07 GB**, the CPU-only PyTorch change measured against the previous image |
| API / web image size | 324 MB / 74.7 MB |
| All five services start and report healthy | mongo, redis, api, ai healthy; web serving HTTP 200 |
| `/health`, `/health/ready` | `ok`; `ready` with `mongodb: up` |
| API — MongoDB / Redis | readiness reports `up`; `redis-cli ping` returns `PONG` |
| API — AI over Compose DNS | `http://ai:8000/health` reachable from the api container |
| Normal legal question | `answered`, severity `normal`, 5 cited excerpts, disclaimer attached |
| Serious query | `redirect_adviser`, severity `serious`, caution plus 5 cited excerpts |
| Emergency query | `redirect_emergency`, severity `emergency`, no excerpts, no retrieval |
| Obstruction request | `refused`, severity `harmful_request`, no excerpts, no retrieval |
| Out-of-domain question | `abstained`, `insufficient_evidence`, severity `normal` |
| Educational domestic-violence question | `answered`, severity `normal` (the false-positive check) |
| Hybrid retrieval live in the container | `retrieval_mode: hybrid` with real `dense_score` values |
| `.dockerignore` completeness | ai image carries `app/` and the mounted `data/`; api carries `packages/contracts`; web carries the built assets |
| Environment guards in the container | production rejects the placeholder `JWT_SECRET` and a wildcard `WEB_ORIGIN`, accepts a real pair; development still accepts the placeholder |
| CORS for the browser leg | preflight from `http://localhost:5173` returns the matching allow-origin; another origin never receives its own |

**Model cache across container recreation.** The 88 MB
`all-MiniLM-L6-v2` download lands in the `ai_model_cache` named volume.
The container was **recreated** (`docker compose rm -sf ai` then `up`,
confirmed by a changed container id — not a restart) and the cache was
still present before any query. Conclusively: the model then loaded with
`HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` set, which is only
possible from cache.

**Retrieval baseline re-measured, unchanged.** `eval/run_eval.py` was
re-run because the harness calls `handle_legal_query()`, so the new
safety layer could in principle have shifted abstention. It did not —
hybrid reproduces the documented control-set baseline exactly: recall@5
0.8370, precision@5 0.1822, MRR 0.7096, nDCG@5 0.7227, top-1 0.6222,
abstention accuracy 0.9796, with `q19` the only false abstain as before.

**Still not verified:** the browser leg. The Chrome extension was not
connected this session, so no click-through of the Learn or Legal
Assistant pages was performed. The HTTP path those pages use was
verified instead, including the CORS preflight that is the part most
likely to break.

### M7 — citizen-language query normalisation (uncommitted)

Closes part of the measured gap between how citizens describe legal
problems and how statutes express them. **The frozen RAG system was not
touched**: retrieval, ingestion, the corpus, the index, the thresholds,
the confidence gate, the evaluation datasets and fine-tuning are all
byte-identical, and the new layer lives in its own package outside
`app/retrieval/`.

- **`app/query/normalize.py`** — 25 deterministic rules appending
  statutory vocabulary to the *retrieval text only*. Every rule was probed
  against real retrieval and kept only if it moved the target chunk into
  the top-5; none was added for completeness. Each carries a confidence
  tier (`HIGH` = corpus section title **and** Legal Glossary headword with
  the same citation; `MEDIUM` = corpus only; `CONTEXT-GATED` = fires only
  on a discriminating signal) and names the evaluation query that
  justified it.
- **Ambiguity is preserved, not resolved.** No rule exists for "took my
  phone" (theft vs police seizure), "complaint", "court" or "case". Where
  the discriminating signal is absent, retrieval sees the raw query.
- **Safety is unaffected.** Normalisation runs after the safety policy and
  both guards, all of which still inspect the raw question, so nothing it
  appends can move a query past a safety decision or an abstention. The
  answer is assembled from retrieved chunks, so the normalised text never
  reaches the user, the citations or the response.

**Measured result** (frozen harness, mode=hybrid, both arms on the same
metric definitions):

| Set | recall@5 | recall@1 | abstention accuracy |
| --- | --- | --- | --- |
| control (49) | 0.8370 → **0.8593** | 0.6222 → **0.6444** | 0.9796 → 0.9796 |
| citizen-language (313) | 0.6246 → **0.7171** | 0.3879 → **0.4342** | 0.7827 → **0.8243** |

Also measured: `hard_negative` recall unchanged at 0.966, wrong-Act rate
0.1957 → 0.1886, `direct_lexical` and `ambiguous` unchanged, retrieval
latency unchanged (~17ms median). Gains are concentrated exactly where the
gap was: colloquial +0.159, vague_answerable +0.138, misspelling +0.136,
ordinary_citizen +0.127, abbreviation +0.111, paraphrase +0.088.

**A separate citizen-language retrieval index was measured and rejected.**
Retrieving concepts from a NALSA/DAKSH-derived index and feeding them into
authoritative retrieval scored -0.082 / -0.157 / -0.246 at top-1/2/3
concepts and collapsed `hard_negative` recall 0.966 → 0.724. Broad concept
vocabulary dilutes section-level discrimination; an oracle injecting only
the Act name cost 0.24 recall on its own. The value is in the mapping, not
in retrieving it. Do not re-propose without addressing that cause.

- **Startup warm-up** (`app/main.py`). ~12.1s of a ~15.4s cold first query
  was the sentence-transformer load. FastAPI's lifespan now issues one
  throwaway query at startup: **first query 15.36s → 0.028s**, warm queries
  unchanged. Failure is logged and surfaced on `/health`
  (`retrieval_warm`, `warmup_error`) rather than raised, so a missing index
  degrades the service instead of blocking boot. `AI_SKIP_WARMUP` opts out.
- **Legal Glossary 2026** (Ministry of Law and Justice, Legislative
  Department, Official Languages Wing) is used as a **terminology
  validation** resource only, never as answer evidence. The 20.6 MB PDF is
  **not committed and not ingested**. It maps English legal term → Hindi
  with the statutory citation attached, which corroborated 21 of 34
  candidate targets (e.g. `robbery : [s. 309, B.N.S.]` matches `bns:309`).
  Two cautions: it carries some legacy IPC numbering
  (`cheating by personation : [s. 416, B.N.S.]` is the IPC number, not the
  BNS one), and its two-column bilingual text extracts interleaved, so it
  corroborates rather than decides.

**Known limitation found while doing this:** `app/retrieval/query_expand.py`
expands `FIR` to "First Information Report", a phrase appearing in only 4
of 1,801 chunks; the statute says "information relating to the commission
of a cognizable offence". Reported, not changed — that file is frozen.

### M7b — Learn FAQs, "What should I do?" (uncommitted)

30 practical FAQs alongside the 63 explanatory articles. The split is
deliberate: an article answers *what is this law*, an FAQ answers *what do
I need to know if this happens to me*. An FAQ never duplicates an article
— it answers briefly and links to the article for the detail.

**Chosen from demand, not from a target count.** The questions come from
the 313-query citizen-language evaluation set: the provisions citizens
actually ask about most, in their own words. `bnss:47`, `bnss:173`,
`lsa:13`, `jj2015:10`, `bnss:478` and `pwdva:18` were each asked about
four times; those became FAQs. Nothing was written to reach a number.

**Grounding.** All 92 citations resolve to real corpus sections (checked
against `chunks.jsonl`, and enforced by
`apps/web/src/content/learn/faq-content.test.ts`). Every FAQ carries a
mandatory `scopeNote` naming what it does not decide, and all 36
`relatedArticles` links resolve to existing article slugs. Secondary
sources (NALSA, DAKSH) helped identify *which questions citizens ask* and
supplied citizen-language search tags; they are **not** cited as legal
authority anywhere.

**Safety.** FAQs touching danger or live legal jeopardy carry an
`urgency`, and the panel then leads with contacting help rather than with
the law. Only the four official national helplines the Legal Assistant's
safety layer may name appear anywhere — 112, 181, 1098, 1930 — enforced by
a test that strips statutory references first so a section number is not
mistaken for a phone number. A second test rejects outcome-promising
wording ("you will get", "guaranteed") in any answer or step.

**Static, not retrieved.** FAQs are ordinary Learn content. The frontend
does not call the AI service to render one, so an FAQ cannot change under
a reader or assert something its cited provision does not say. They reuse
the existing Learn search and category filter rather than adding a second
search surface, and their citizen-language `tags` are what let a search
for "cops won't file" reach the FAQ titled "The police won't register my
FIR" — the same gap the retrieval normalisation layer closes, solved here
by indexing the words people actually use.

**Coverage, by category:** police-fir 7, arrest-bail 7, everyday-rights 4,
women-and-safety 3, consumer-rights 3, legal-aid 2, digital-rights 2,
children-and-young-people 2.

**Deliberately omitted.** A "government department is ignoring my
complaint" FAQ was planned and dropped: the corpus contains no
grievance-redressal statute, the RTI Act is not ingested, and the
Legislative Department's grievance page returned HTTP 403. Writing it
would have meant inventing procedure from general knowledge. The civic
complaint route on this platform is described in the Civic Participation
article instead, which is honest about being platform behaviour rather
than law.

### M8 — RTI ingestion, coverage rework, emergency safety

**The false-answer hole, closed first.** A 24-question probe of
out-of-corpus subjects found **14 answered confidently from unrelated
Acts**. The worst was "how do I get information from a government
department", answered from BSA's section on *unpublished official
records* — the exact opposite of the entitlement asked about.
`corpus_coverage.py` gained `_COMPOSED_RULES`: a rule fires only when
every required concept group matches and a stand-down group does not,
the same SUBJECT × FRAME composition `risk.py` uses, applied to
coverage. Result **14 → 0 false answers**, with a control set of
genuinely answerable queries proving it was not bought by abstaining
more broadly. Every pattern was checked against real indexed text
first, which changed the design twice: "bribe" is in the corpus four
times answerably (electoral bribery, screening an offender, bribing a
witness), and "copy of"/"information" are heavily covered (free FIR
copy, police-report copies, certified judgments, grounds of arrest,
consumer right to be informed).

**Safety triage.** The serious tier carried one pattern unlike the rest
of its group — a bare possessive, "my (fir|case|complaint|...)".
Because a possessive is inherently personal, `_is_purely_educational`
could never be true for it, so it fired unconditionally: a pothole
complaint graded `serious`, and "must the police tell me the grounds of
my arrest" got a lawyer redirect. Split into `_OWN_LEGAL_MATTER`,
counted only when no entitlement frame and no bribe solicitation is
present. "complaint" left the list entirely; the complaint-*against*-me
pattern was widened so "an FIR has been filed against me" now grades
serious (it graded normal before). Bribery solicitation now grades
consistently regardless of possessive.

**RTI ingested — 26 sections.** From the Central Information
Commission's own published copy (no new download). Ingestion gained
three general opt-in mechanisms, all defaulting to previous behaviour:
`chunk_end_marker` (the Second Schedule's numbered organisations were
being read as sections, colliding with the real ss.9 and 22),
`exclude_units` with a mandatory reason recorded in the manifest, and
`title_overrides`. Ingestion now refuses to run on duplicate chunk_ids
or on a stale exclusion/override.

Four sections excluded. **ss.13, 16, 27** — replaced by the RTI
(Amendment) Act 2019, and this pre-2019 copy still states the
superseded five-year term and CEC salary parity. **s.25** — excluded
for measured retrieval harm, not currency: its "prepare a report /
collect and provide such information" text sits close in embedding
space to "file an FIR" (First *Information* Report) and took the top
hit from bnss:173/177 on four FIR queries, accounting alone for 5 of 11
RTI intrusions into the dense top-5 of non-RTI queries. Stated
trade-off: a question about a Commission's annual reporting duty is now
unanswerable.

One OCR defect was deliberately **not** repaired. 48 markers render as
"(/)", and they are not all the same character — most are "(1)", but
in s.2 the same glyph is the definitions clause "(l)". A blanket
rewrite would relabel definition clauses as sub-sections. Two *titles*
were restored ("Ftight to information", "Powers and 'Unctions"),
because titles are indexed and those are the exact words citizens
search for.

Nine deterministic RTI normalisation rules were added, because citizens
describe this Act in words it never uses — "RTI" appears nowhere in
the statute, so "how do I file an RTI application" retrieved it_act
chunks at dense 0.25 and abstained. **20 RTI probes through the
production pipeline: answered 19/20 → 20/20, top hit from RTI 13/20
→ 20/20, right section 8/20 → 18/20, wrong-Act top hits 5 → 0.**

**Emergency tier.** Two gaps found by probing what a frightened person
actually types. Child cases ("someone took my child", "my child went
missing", "my son did not come back from school and a stranger took
him") all graded normal while only the word "kidnapped" worked; they
now route to `child_safety` so the reply names Childline 1098. Stalking
had no representation at all and is deliberately a *composition*:
being followed AND a second signal (fear, repetition, or the person's
home), standing down entirely on social-media context, because
"following me" is also what an Instagram account does. Matrix: clear
emergencies 10/10 unchanged, educational 12/12 unchanged, ambiguous
0/9 → 8/9, plus a 20-case false-positive probe at 20/20.

**Learn.** 8 RTI articles, 27 questions, 5 FAQs — 71 articles, 216
questions, 35 FAQs across 12 categories. All 713 Learn citations
resolve to real ingested sections. No fee amount appears anywhere (the
Act leaves figures to un-ingested rules) and nothing describes
Commissioner tenure (the excluded sections); both are asserted by
tests, and both are declared as `deferredTopics` on the category.

**362-query evaluation, across all of M8:** recall@1 unchanged on both
sets (0.6222 control / 0.3879 citizen); recall@5 0.8370 unchanged
control, 0.6246 → 0.6238 citizen; wrong-Act rate unchanged on both
(0.0667 / 0.1957); hard-negative recall unchanged at 0.9655. The
single citizen recall change is `h258` ("protection of action taken in
good faith"), whose gold set names the five Acts that had that section
when it was written — RTI s.21 carries it too, so a correct sixth
match displaced one. Citizen abstention 0.8275 → 0.8243, one query:
`h029` ("a stranger grabbed my daughter off the street"), which now
routes to the child-safety emergency instead of citing bns:137.

**Three eval labels are now stale and were left untouched**, since
`eval/` is outside the approved scope and editing them to make changes
pass would be weakening the criteria: `q35` and `h286` both assert "the
RTI Act is not ingested" (both now answer from rti:6, the correct
section), and `h029` encodes retrieval as the desired response to a
live child abduction.

**Known limitations carried forward.** RTI s.14 is not chunked (the
source omits the full stop before the em-dash the header pattern
needs). "how do I get a free copy of my FIR" still abstains at the
confidence gate although BNSS s.173 answers it — a retrieval-recall
miss, untouched because retrieval and the gate are frozen. The bare
"someone is following me" is a stated non-fire.

### M9 — evaluation reconciliation, safety hardening, three audits

**Three stale evaluation labels reconciled.** Each was checked
individually and only what was genuinely obsolete changed; every edited
row keeps its original expectation in a new `superseded_expectation`
field so the change is auditable from the file rather than from git
history. `q35` and `h286` both asserted "the RTI Act is not ingested",
which stopped being true; both now expect `rti:6`, the provision that
governs making a request, chosen from the Act rather than from what the
system returns. `h029` ("a stranger grabbed my daughter off the
street") expected `bns:137`; it now routes to the child-safety
emergency. Marking it `expect_abstain=true` alone would have said
withholding an answer is correct without saying why, so the harness
gained two optional keys, `expect_severity` and `expect_reason`, letting
a row require the *route* and not merely the silence — a
child-abduction query that abstains because the corpus lacks the law
has still failed. Verified non-vacuous with stubs.

Result: control false_answer `['q35']` → `[]`, abstention 0.9592 →
0.9796; citizen false_answer `['h286']` → `[]`, abstention 0.8243 →
0.8307, recall@5 0.6238 → 0.6274, MRR 0.4876 → 0.4912, nDCG 0.5154 →
0.5190. No other query changed.

**A measurement defect worth knowing about.** Control recall@5 moved
0.8370 → 0.8188, and it is not a regression: `q35` is now scored, and
it scores 0 because `evaluate_retrieval` calls `search()` directly and
skips `app.query.normalize`, the layer production uses. Raw search
returns it_act chunks for that query; normalised search returns `rti:6`
at rank 1, which is what a citizen actually receives. **The harness
measures a path the product does not use.** Left alone because changing
it would shift every historical retrieval number in the project at
once.

**Emergency tier hardened.** A 40-case probe matrix (stalking, threats,
child safety, domestic violence) found four defects, two in each
direction; the matrix now scores 40/40 with zero false emergencies and
zero missed. Missed: "a man follows me to the bus stop every evening"
(only the literal "every day" counted as repetition) and "my child was
taken" (every pattern required a grammatical subject, so passive voice
was missed). Escalated wrongly: the tier had **no notion of tense at
all**, so "my husband used to beat me years ago, what are my options"
got a helpline instead of the law on protection orders. Immediacy
always defeats the new historical stand-down — reading a live
emergency as history costs far more than the reverse.

The matrix also exposed an asymmetry nobody had listed: "my husband
beats me" was an emergency and "he beats me" was normal, the same
situation graded by the pronoun the person happened to use.
`_UNNAMED_ABUSER_SUBJECTS` closes it, routed to `threat_to_life` since
no relationship is stated. One false positive was introduced and caught
by the full evaluation before commit — `h059`, "my kid got picked up by
the cops", is a lawful apprehension under the JJ Act, not an abduction.

**A self-inflicted coverage gap closed.** Excluding ss.13/16/27 as
pre-2019 text meant no correct answer to a tenure question existed —
and retrieval answered anyway: 7 of 8 tenure/salary questions came back
from Definitions, Designation of PIOs, Constitution of the Commissions
and Removal. Real sections, correctly cited, none containing the
answer. A new `rti_amended_service_provisions` category catches an
Information Commissioner concept AND a service-terms concept, with its
own message, because `NOT_IN_CORPUS_MESSAGE` would be false here: the
Act *is* held. 9 abstain, 9 still answer.

**Learn search fixed.** `matchesQuery`/`faqMatchesQuery` were a
whole-phrase substring test, so "cops won't file my complaint" found
nothing against an FAQ tagged "cops won't file". Matching is now exact
phrase first, then an AND over meaningful words; the article haystack
gained the body text, since searching only title and summary meant
"what is the punishment for theft" matched no article at all.

**Two API reliability defects fixed.** Health checks sat behind the
global rate limiter — verified 429 from the 101st request, with the
container healthcheck alone consuming 60 of 100 per window, so Docker
would restart a working container. And the AI service call had no
timeout: node's fetch imposes none, the existing catch saw refused
connections but not silent ones, so a hung AI service held requests
open indefinitely. Now bounded at 15s, answering 504 rather than 503.

**Audited, correct, unchanged:** citation integrity (33 probes, 100
excerpts, nine properties, zero findings — mutation-tested so zero
means something); Learn content integrity (no duplicate ids or slugs,
no broken references, no citation to an excluded section, every FAQ
carrying a legal basis, citation, scope note and tags, none promising
an outcome); authentication, validation, ownership, file-storage path
handling and security middleware.

**Deployment decisions documented rather than taken:** no `trust proxy`
setting (behind a proxy the rate limiter would bucket every user
together, but setting it wrongly lets clients spoof X-Forwarded-For),
and auth endpoints sharing the global limit rather than a stricter
login-specific one.

Retrieval parameters, embedding model, RRF weights, candidate pool and
confidence thresholds were not touched anywhere in this increment.

### M10 — product completion: civic duplicates, Legal Assistant ↔ Learn, state-sync and navigation

The product-completion milestone the M9 handover authorised. **The frozen
RAG system was not touched**: nothing under `services/ai/` changed —
retrieval, thresholds, safety guards, corpus, index, embeddings and
evaluation sets are byte-identical, and the 349-test Python suite is
unchanged and green.

- **Civic duplicate handling — built, deterministically.** Two mechanisms,
  deliberately kept apart (`services/api/src/services/civic-duplicates.ts`):
  - *Exact resubmission*: SHA-256 fingerprint over reporter id, category,
    normalised title+description (lowercase, punctuation/whitespace
    collapsed, NFKC), coordinates quantised to 4 decimal places (~11 m
    cells) and an hourly time bucket. Stored on the report and enforced by
    a **unique sparse index** (`models/civic-report.ts`), so the database —
    not application logic — wins the race between two in-flight identical
    submissions; `CivicReport` was already in `server.ts`'s `indexedModels`,
    so the API refuses to serve if the index cannot build. The fingerprint
    embeds the reporter id, so two citizens reporting the same pothole can
    never collide — only the same citizen re-submitting the same content in
    the same hour. The API answers 409 `DUPLICATE_REPORT` with the citizen's
    own earlier report id, and the form links to it.
  - *Potential same real-world incident*: before anything is persisted,
    a `$nearSphere` query over the existing 2dsphere index finds
    non-rejected same-category reports within 200 m from the last 30 days.
    A match is a **warning, never a refusal**: the API answers 409
    `POTENTIAL_DUPLICATE` with deliberately redacted summaries (id, title,
    category, status, rounded distance, date — no body, no landmark, no
    reporter, no coordinates, preserving the 404-not-yours boundary), and
    the form shows them with "Submit my report anyway", which re-submits
    with `acknowledgeDuplicates` (a strict `"true"` literal check — not
    boolean coercion, which would read `"false"` as true). Independent
    reports of a real problem are legitimate evidence and are never
    suppressed. Verified against real MongoDB in
    `civic-duplicates.integration.test.ts` (index existence/uniqueness/
    sparseness, E11000 on identical resubmit, different citizens allowed,
    legacy no-fingerprint documents coexist, real geo query with distance
    ordering and radius/category/recency/status exclusions).
- **Legal Assistant ↔ Learn — connected by exact metadata.** The AI
  service's `chunk_id` is `"{source_id}:{unit_number}"` and every Learn
  citation is the structured `{ sourceId, unitNumber }` in the same
  vocabulary, so `relatedLearnContent()` (`content/learn/index.ts`) is an
  exact-key join over a map built once from the static content — no
  similarity model, no invented relationship, and a provision without
  Learn coverage honestly renders nothing (the page keeps its generic
  Learn links). Round-trip tests assert every authored article and FAQ
  citation reaches its own content back. FAQ deep links exist now:
  `FaqPanel` carries `id="faq-<id>"`, and `/learn#faq-<id>` opens that FAQ
  expanded and scrolled into view.
- **Stale-state deadlocks fixed.** A 409 on sign/withdraw/transition
  (petitions) or transition/priority (reports) now refetches, so the page
  shows the state that actually exists instead of a button that can only
  fail again beside a message saying to reload. The authority's formal
  `ANSWERED` note gets its own "The authority's response" panel rather than
  being one grey history row. The citizen report page gained a "Check for
  updates" refresh; every list/detail error state gained a retry button.
- **Authority queues completed.** The report queue paginates (it printed
  "Showing n of total" while being unable to reach past 25), distinguishes
  an empty database from an unmatched filter, and keeps the
  overdue/terminal-status filters mutually exclusive (a closed report is
  never overdue, so the combination could only match nothing). The petition
  queue's goal filter became a three-way select — the API always supported
  `goalMet=false` but the checkbox could not express it.
- **Signature recount — the documented recovery, implemented.**
  `POST /api/petitions/:id/signatures/recount` (ADMIN, fresh-role checked)
  sets `signatureCount` from a real `Signature` row count. Count drift was
  by design one-directional and recoverable "by one aggregation" — that
  aggregation now exists, tested against real MongoDB.
- **Navigation and copy made role- and reality-aware.** `/report` is
  citizen-only in the route guard to match the API (staff could previously
  fill the whole form, upload a photo and only then meet a 403); the nav
  hides Civic report / My reports / My petitions from staff, whose work
  lives in the queues; `ProtectedRoute` derives its denial copy from the
  declared roles (a citizen-only page no longer tells an authority officer
  it is "for civic authority staff"); the home page finally links the
  Legal Assistant (four pathways, not three); a typo'd URL gets a real
  404 page instead of "planned module" (`PlaceholderPage` deleted); an
  expired session says so on the login screen instead of presenting as a
  fresh visit (`sessionExpired` in `AuthContext`); the account page links
  each role to its actual spaces and drops its stale "later increments"
  copy; the document browser reports a too-short query instead of silently
  ignoring the submit, and its loading/error states carry `role=` for
  screen readers.

Counts after M10: API unit tests 272 → 298, web 247 → 266, integration
15 → 22 (all against real `mongod`), Python 349 unchanged. Typecheck and
production build clean.

### M11 — session refresh, remaining product gaps, and the deterministic multi-turn context layer

Two halves. M11-A closed the highest-impact product gaps left after M10;
M11-C/D built the first deterministic NLP/context capability beyond
single-turn normalisation. **No generative LLM anywhere, unchanged**;
retrieval parameters, embeddings, RRF weights, thresholds and the corpus
are untouched, and both single-turn eval baselines reproduce exactly
(control recall@5 0.8188 / abstention 0.9796 with q19 the sole false
abstain; citizen 0.6274 / 0.8307).

**M11-A — product gaps.**
- *Token refresh.* Login now issues a 7-day refresh token alongside the
  15-minute access token (distinct JWT audience, so the two can never be
  substituted for one another; the refresh token carries no role).
  `POST /auth/refresh` re-reads the account on every use — tokenVersion
  revocation still kills the whole session, and the new access token
  carries the *stored* role, so promotions/demotions take effect at the
  next refresh. The web app renews transparently: a 401 with a presented
  token triggers one single-flight refresh and a replay of the failed
  request; only a failed refresh ends the session. Login-401s never
  touch the stored session.
- *Verification email.* `SMTP_URL` (optional env) activates a nodemailer
  transport; register/resend then mail the same single-use hashed token
  the development flow uses. No provider is assumed — a deployment brings
  its own SMTP endpoint. In production with no transport configured,
  registration answers 503 instead of creating accounts nobody can ever
  activate; development keeps the token-in-response flow either way.
- *My Reports pagination* (limit/offset + total; the old fixed 100 cap
  silently truncated), *petition free-text search* (`q` over
  title/description, regex-escaped, case-insensitive, public status floor
  intact — search on submit, not per keystroke), and *staff history actor
  names*: actorIds on civic/petition history resolve to display names in
  one batched read, staff viewers only, id kept as fallback for deleted
  accounts.
- *Withdraw drift* — deliberately unchanged, now correctly documented:
  the decrement-then-delete order is the inverse of signing on purpose
  (flipping it would let a crash inflate the count, violating the one
  safety invariant), the rare crash-retry double-decrement stays
  conservative-only, and the M10 ADMIN recount is the recovery.
- *Notifications* — deferred again, deliberately: no clean minimal
  implementation exists inside the current architecture (it needs
  storage, read-state and a delivery surface), and the report page's
  refresh affordance covers the acute need.

**M11-C/D — deterministic multi-turn context (`app/query/context.py`).**
The Legal Assistant now understands safe follow-ups with zero model
calls. The client sends back its previous question; the service decides,
by rules alone: a *standalone* question passes through untouched (context
never overrides new intent); a *follow-up* ("what if I'm a minor?", "and
at night?", "what if he breaks it?") is resolved by **pure text
composition** — previous question + fragment concatenated, nothing
inferred or generated — and the combined text is shown back to the user
("Read together with your previous question: …") so no interpretation is
invisible; a follow-up that *cannot* be resolved ("what about this?", or
no previous question) gets a clarification request (`needs_context`),
never a guess. Detection is deliberately conservative: a dependent opener
alone is not enough ("what happens when you're arrested?" stays
standalone), and a scan test pins that none of the 362 single-turn eval
queries is misread as a follow-up.

**Safety: client context is untrusted input.** Every deterministic guard
(risk, topic, coverage) re-runs over the combined text, stricter outcome
wins — a divorce question the coverage guard refused in turn one cannot
become answerable through an innocuous follow-up, and a harmful request
split across turns is still refused before retrieval. Both are pinned by
tests and eval rows.

**Measured** (`eval/queries_followup.jsonl`, 18 rows, every expected
chunk verified against real corpus text; `eval/run_context_eval.py` runs
the production pipeline for both arms): condition follow-ups hit@5
**0/10 fragment-only baseline → 8/10 with context**; ambiguous and
no-context follow-ups 4/4 clarified; standalone-override 2/2 (context
correctly not applied); guarded follow-ups 2/2 blocked. Two narrow
CONTEXT-GATED normalisation rules were added for turn-spanning signals
(breach of protection order → pwdva:31; consumer limitation →
cpa2019:69), each probe-verified to rank 1–2, keyed on phrases that occur
in exactly one Act, and proven inert on all 362 single-turn queries by a
scan test. The two residual misses are known representation limits: f01
(arrest + "minor" cannot reach the JJ Act — the child normalize rule is
sentence-bounded and its signals sit in different turns in the wrong
order) and f04 (FIR copy — the same recall miss M8 documented).

Counts after M11: Python 349 → 363, API unit 298 → 318, web 266 → 278,
integration 22 unchanged. Typecheck and production build clean.

### M12 — accuracy & evaluation: production-path measurement, taxonomy-driven fixes, validated fine-tune

Feature work paused; this milestone measured why CAT misses queries and
fixed only what the evidence named. Full method and numbers in
`docs/RETRIEVAL_EVALUATION.md`'s M12 section; the short version:

- **Production-path evaluation series** (`run_eval.py --production-path`)
  closes M9's known measurement gap — retrieval measured on the
  normalised text production actually searches. Historical raw-query
  numbers untouched and still reproduce exactly.
- **Failure taxonomy** over every production-path failure: gate 35 /
  ranking 23 / BM25-vocabulary 40 / representation 14 at baseline.
- **Promoted (one variable at a time, control set byte-identical
  throughout, zero false accepts throughout):** a curated spelling layer
  (generic edit-distance corrector built and rejected — statutory
  vocabulary ≠ English), seven probe-verified normalisation rules plus
  two child-rule extensions, gate floor 0.42→0.41 (the abstain-side
  production-path ceiling is 0.399; tune/validation split, no leakage),
  follow-up detection refinements, and an emergency-tense fix ("he hit
  me last year" is no longer a helpline redirect; "last week"
  deliberately still is). One M7 ambiguity pin narrowed with the eval
  label as ground truth: "someone took my phone" now expands to theft;
  police-subject phrasings still never do (both directions pinned).
- **Rejected on measurement, documented:** the generic spelling
  corrector; an agreement-branch confidence gate (+5 good, +2 wrong-Act
  — both retrieval methods can agree on the same wrong chunk).
- **Citizen production-path: recall@5 0.7199 → 0.7448, abstention
  0.8307 → 0.8562**, false abstains 53 → 45. Follow-up benchmark grown
  18 → 40 corpus-verified rows: condition follow-ups 19/21 (fragment
  baseline 3/21), every safety/behaviour category green.
- **Fine-tune m12_run2: the first candidate to generalise.** Against
  run1's honest wash, the 402-group pool trains a model that improves
  every quality metric on strictly held-out queries (citizen recall@5
  0.6171 → 0.7024) and passes every mandatory safety gate
  (hard-negative 29/29, wrong-Act top-1 46 → 22, zero false accepts,
  emergency untouched by construction). **Not flipped into production**:
  that requires distributing a ~90 MB model artifact — a deployment
  decision recorded, with exact reproduction and deployment steps, in
  the evaluation doc.

Counts after M12: Python 363 → 364 (net: taxonomy-driven test updates),
follow-up eval 40 rows. Node suites, typecheck, build untouched by this
milestone's changes (AI service only).

### M13 — m12_run2 promoted to production; final engineering freeze

The M12 candidate was deployed on the real production path, evaluated
against the reproduced M12 baseline with only the embedding model
varying, and **promoted** — full method, tables, per-case severity
analysis and artifact hashes in `docs/RETRIEVAL_EVALUATION.md`'s M13
section. The short version:

- **Deployment = existing mechanism, no new infrastructure**: artifact at
  `services/ai/data/models/m12_run2` (gitignored, reproduced by the
  seeded `finetune/` pipeline; `model.safetensors` SHA-256
  `d61d077b…0ce801`), `DENSE_EMBEDDING_MODEL=data/models/m12_run2`,
  re-ingest. The manifest records the service-root-relative path and
  `embeddings.resolve_model_path()` resolves it at load time, so the
  same index works on the host and inside the Docker container (which
  already mounts `data/` and needs no image rebuild).
  `docker-compose.yml` and `.env.example` now record the setting.
- **Production-path results** (citizen 281 / control 46): recall@5
  0.7448 → **0.9554** / 0.8623 → **0.9674**, MRR 0.5656 → 0.88, top-1
  citation 0.4448 → 0.8185, abstention 0.8562 → 0.9233, false accepts
  **0 → 0**, wrong-Act top-1 43 → 19, hard-negative recall **29/29**.
  Held-out-only (never trained/selected on): recall@5 0.7634 → 0.8732,
  every quality metric up, zero false accepts — the generalisation
  claim survives the production path. Follow-up 40-row benchmark: f04
  (the M8 FIR-copy miss) fixed; f35 now abstains (conservative
  residual); guards byte-identical. Every candidate number reproduced
  twice, byte-identically.
- **A real defect found and fixed**: running the Python test suite with
  `DENSE_EMBEDDING_MODEL` unset silently rebuilt `data/index` with the
  *default* base model (test_retrieval/test_hybrid_retrieval rebuild the
  real index by design). `tests/conftest.py` now pins the env var to
  whatever the on-disk manifest records before any test runs; verified
  by running the suite env-unset and checking manifest + vectors after.
  New: `tests/test_embeddings_config.py`.
- **Deferred with reasons** (not blockers for the single-instance
  capstone deployment): distributed rate limiting (in-process store,
  one API instance; `REDIS_URL` is validated but nothing connects to
  Redis), media-serving streaming (media storage itself is disk-backed
  and volume-persisted), email transport (gap #32, unchanged).

**CAT is now FROZEN as the experimental system for the research paper.**
The paper must use these M13 production-path numbers, not the
intermediate M12 ones.

## Do NOT do yet

- Module 2 (civic reporting): the **citizen reporting core, the authority workflow and deterministic duplicate handling are built** (see M2, M3 and M10 above). Do not build DBSCAN clustering, civic vision/ML, automatic categorisation or automatic priority prediction, civic analytics, or a notification system without a new instruction.
- Module 3 (petitions): the **citizen petition core, signatures and the authority moderation workflow are built** (see M4 above). Do not build a petition recommendation agent, DBSCAN clustering over petitions, petition-to-report linking, petition comments/discussion, identity or constituency verification of signers, or petition analytics without a new instruction.
- The Learn module is **expanded and complete for the current corpus**: 63 grounded articles and 189 quiz questions across eleven categories in `apps/web/src/content/learn/`. Remaining Learn gaps are content the corpus cannot support: RTI (un-ingested), workplace/labour rights (no labour legislation ingested), sexual offences against children (POCSO un-ingested), and IT Act sections 43/43A/66 (absent from the ingested PDF). Do not write content for those without ingesting a source first.
- Do not redesign the architecture without a concrete reason.
- Do not re-ask questions already answered in prior chat history — check the conversation/spec first.

## Known gaps / next steps (historical register)

> **Historical, and append-only.** This register grew by appending: a
> later item that resolves an earlier one usually cites it by number
> ("gap #23", "gap #59") rather than editing the original, and items
> struck through were closed in place. **A numbered item here being
> un-struck does not mean it is still open at the freeze** — several
> were closed by a later milestone whose entry appears further down, or
> in the "Completed" timeline above.
>
> **For the list of limitations that are actually still true at the
> freeze, read Part A, section 9.** That list is authoritative; this one
> is the record of how the project reasoned about each gap at the time.

**Module 1A corpus**
1. ~~**BNSS**: ingest Chapter XIII (investigation/FIR) and Chapter XXXV (bail and bonds)~~ — resolved this session: BNSS is now fully ingested (533/533 sections), see "Corpus expansion" above.
2. ~~**BNS**: ingest punishments, abetment, offences against the body, offences against property~~ — resolved this session: BNS is now fully ingested (357 sections).
3. ~~**BSA**: currently only a small excerpt~~ — resolved this session: BSA is now fully ingested (170 sections).
4. ~~FIR vs NCR and Bail Procedure learning articles can now be written (corpus supports them)~~ — resolved: both are written (`fir-vs-ncr`, `bail-procedure-basics`), grounded in BNSS ss.173-176 and ss.478-484 respectively.
5. ~~Compoundable vs Non-compoundable Offences topic — needs BNSS section 359~~ — resolved this session: section 359 is ingested. Article not yet written.
6. Consider adding a lightweight admin UI (or at minimum a documented CLI step) for approving a new source before `ingest_corpus.py` will pick it up, per the "admin validates official origin before indexing" requirement — not built yet, currently enforced only by the `APPROVED_SOURCES` allow-list in code.
7. ~~Dense embeddings are optional and untested~~ — resolved this session: `requirements-full.txt` (`sentence-transformers`) installs and runs cleanly; hybrid mode is live and evaluated (`docs/RETRIEVAL_EVALUATION.md`). Note for future environments: this environment's global TensorFlow/Keras install initially broke `transformers`' TF integration path on import — worked around with `USE_TF=0` in `app/retrieval/embeddings.py`, harmless where TF isn't installed at all.

**Module 1B legal answers**
8. ~~Same corpus gaps as above directly limit what can be answered~~ — resolved this session for bail, burden of proof, and child-in-conflict-with-law (all now answer correctly with real, specific citations — see "Corpus expansion" above). FIR/NCR and offences-against-the-body/property can now also be answered, corpus-wise, though not re-verified query-by-query this session.
9. ~~`LEGAL_CHAT_MIN_SCORE` provisional floor~~ — resolved this session: floors are now per-retrieval-mode (`DEFAULT_MIN_SCORE_BY_MODE` in `generation/pipeline.py`), each tuned against the new evaluation harness rather than guessed. Still not perfect (a 30-query eval set isn't statistically robust) — re-sweep after significant corpus growth.
10. ~~No retrieval evaluation harness~~ — resolved this session: `services/ai/eval/` (Recall@K, Precision@K, MRR, nDCG, abstention accuracy, top-1 citation correctness). It was used to justify moving from BM25-only to hybrid (BM25+dense, RRF-fused) with real before/after numbers, and to decide reranking is not yet justified (see `docs/RETRIEVAL_EVALUATION.md`).
11. No persisted audit log of policy decisions — deliberately deferred to the evaluation/hardening increment; current logging is application-level only.
12. The query-safety policy is a deterministic signal-combining ruleset, not an exhaustive classifier — false negatives on unusually phrased risky queries remain possible; this is the accepted trade-off for staying rules-only (no ML/LLM classifier, per standing decision). It is materially harder to evade than the flat keyword list it replaced, because a harmful request is matched on act plus instructional framing rather than on an exact phrase, but it is still curated and should be extended when a specific miss is demonstrated.
13. ~~No query preprocessing (synonym expansion, misspelling correction) yet~~ — partially resolved: `app/retrieval/query_expand.py` now expands 2 known Indian-legal abbreviations (FIR, NCR) after evaluation demonstrated a concrete need (see "Retrieval/evaluation hardening" above). Still no general synonym expansion or misspelling correction — this remains a narrow, curated exception, not a new preprocessing stage, and should stay that way unless evaluation demonstrates another specific, named gap.
14. Reranking (the architecture diagram's optional stage) was evaluated as a candidate and deferred with documented reasoning — hybrid already beat the BM25 baseline on every metric, and the remaining misses look like embedding-model/vocabulary gaps rather than reranking-shaped ranking-order problems. Re-evaluated again after the Constitution-title/RRF-retune fix and still not justified — see `docs/RETRIEVAL_EVALUATION.md`'s "Reranking: deferred" and "Failure-analysis-driven fixes" for what would justify revisiting this.
15. No FAISS/ANN index — a deliberate choice, not an oversight: brute-force NumPy cosine similarity over ~400 chunks runs in sub-millisecond time, so an approximate-nearest-neighbor index has no measured benefit yet. `app/retrieval/embeddings.py` was kept swap-compatible with one for when/if the corpus grows by orders of magnitude.
16. ~~Two-column gazette PDFs not ingested~~ — resolved: BNS, BNSS, BSA, Consumer Protection Act 2019, and Juvenile Justice Act 2015 are all now fully ingested via `extract_gazette_body_text()`, with section titles best-effort recovered for 40-57% of their sections via the independent `extract_gazette_titles()` pass; see `docs/LEGAL_SOURCES.md`'s "Two-column gazette PDFs". One residual limitation remained at the time: one BNSS section (337) mislabeled as a duplicate 338 — **since fixed outright** by replacing all five sources with single-column "bare Act" PDFs (the new BNSS source has no such duplicate; its 531 sections match the official count with no gaps or collisions). Section-title recovery rose from 40-57% to 98-100% in the same change. A different, narrower residual took its place: four sections across two sources (BNS 217/255, JJ Act 61/86) merge into the preceding chunk — see `docs/LEGAL_SOURCES.md` and Part A section 9.
17. ~~RTI Act 2005 still not ingested. The supplied PDF has a font-encoding defect (digit "1" renders as "/" in most subsection markers); a user-supplied "replacement" PDF turned out to be byte-identical to the original (same defect, same SHA-256) — the swap didn't actually happen. Needs a genuinely different PDF, not a code fix — do not spend further effort on the same file.~~ — **resolved in M8, exactly as predicted: by a genuinely different source file, not a code fix.** The Central Information Commission's own published copy is now ingested as **26 sections** in the final corpus. The OCR defect described above survives in that copy too and was handled by leaving the bracketed markers exactly as extracted (rewriting them all to "(1)" would relabel s.2's definition clauses as sub-sections); only two garbled *titles* were repaired. Four sections are deliberately excluded and one is not chunked — see `docs/LEGAL_SOURCES.md`'s RTI section, and Part A section 9 for what that still costs a citizen.
18. ~~`eval/queries.jsonl` (30 queries) doesn't cover the 5 new/expanded two-column sources~~ — resolved: rebuilt to 49 queries covering all 9 ingested sources (see "Retrieval/evaluation hardening" above).
19. ~~The hybrid confidence-gate raise (0.40→0.42) closed one demonstrated out-of-domain false-answer ("register a company") but not all of them~~ — resolved this session: `app/safety/topic_relevance.py` adds a curated deterministic topic-relevance guard (see "Topic-relevance guard" above) that catches "income tax slab", "driving licence", and other well-known out-of-domain subjects before retrieval, independent of the score threshold. Not exhaustive by design (a curated set, extend only when evaluation names a new specific gap) — genuinely novel out-of-domain phrasings not matching any curated pattern still fall through to the confidence gate unchanged.
20. `eval/queries.jsonl`'s "estoppel" (q07) title-dependent query and the multi-source/ambiguous categories are new this round and only lightly stress-tested (a handful of hand-picked cases, not systematic) — worth another pass once the corpus grows again.
21. ~~Constitution articles have no title metadata at all~~ — resolved for Part III (Fundamental Rights, Articles 12-22) this session; see "Retrieval ranking optimization" above. The other ~335 Constitution articles still have `title=""` — deliberately not attempted generally (the two-column reordering makes a safe general parser intractable without real misattribution risk); extend `_KNOWN_ARTICLE_TITLES` only if a future evaluation query names another specific missing title, same rule as `query_expand.py`'s abbreviation dict.
22. ~~`bnss:38` (q15) has a title-recovery gap in the gazette extraction path~~ — resolved this session by the BNSS source-PDF replacement (100% title recovery, no gazette extraction involved anymore) plus one evaluation-justified citizen-language expansion (`query_expand.py`'s `_CONCEPT_PHRASES`, "police question[ed] me" → "interrogation") — see "New single-column source PDFs" above. **Remaining known limitation:** two queries (q17, q46) still don't reliably retrieve their target chunk — confirmed again this session against the new corpus (dense rank 89 and 50 respectively for `constitution:20` / `constitution:15`, both outside or at the very edge of the 50-candidate fusion pool) and confirmed NOT to be a citizen-language/vocabulary-expansion problem this time either (a small curated expansion can't reach a chunk that far outside the candidate pool without risking false positives elsewhere). This is a genuine embedding-model/corpus-density limitation, not fixable by title metadata, query expansion, RRF weighting, or reranking. With only 2 residual failures out of 45 non-abstain queries (95.6% otherwise correct), embedding fine-tuning is not yet justified by this evaluation set's size — see `docs/RETRIEVAL_EVALUATION.md`'s "Embedding fine-tuning: not yet justified" for the recommended trigger condition and rough training-data shape if this changes.

23. **Confident wrong-Act answers on legal questions about un-ingested Acts** — found by the new `insufficient_evidence` category in the 313-query citizen-language evaluation. Hybrid abstains correctly on 20/22 non-legal `out_of_domain` queries but only 5/10 of these: "what is the penalty for drunk driving" answers from `bns:355`, "how do I get a divorce in india" from `bnss:219`, "what does the law against caste-based atrocities cover" from `constitution:16`, "what is the punishment under the POCSO act" from `bns:198`, "how do I file an application for information from a government office" from `it_act:6`. `app/safety/topic_relevance.py` recognises *non-legal* subjects; it has no patterns for legal subjects the corpus does not contain. This is a correctness risk in a legal-information product, not a quality metric, and is the highest-priority item from that evaluation. The in-keeping fix is to extend the same curated deterministic phrase-pattern list with the un-ingested Acts (matrimonial/family law, Motor Vehicles, POCSO, rent control/tenancy, labour and minimum wages, stamp duty/registration, SC/ST Atrocities, arbitration, RTI) — not a classifier. Not done: that session was scoped to measurement only.
24. **The confidence gate is tuned against a query population it no longer represents.** Hybrid produced 69 false abstains across the 313-query set, 57 of them `ordinary_citizen`/`colloquial`, on queries whose correct chunk *was* retrieved into the top-5 — the `DEFAULT_MIN_SCORE_BY_MODE` hybrid floor (0.42) was swept against the 49-query set, whose phrasing sits much closer to statutory register. Re-sweeping the floor against the citizen-language set is now possible with a statistically usable sample, but it is a genuine trade-off (lowering it also admits more of gap #23's wrong-Act answers), so the two should be re-tuned together, not separately.
25. ~~Reranking is deferred because the remaining misses are not reranking-shaped~~ — **that justification no longer holds** (gap #14 above records the original reasoning). The 313-query root-cause split found 36 of 119 missed target chunks (30.3%) sitting inside *both* BM25's and dense's top-50 candidate pools while fusion still ranked them below 5 — the exact pattern a cross-encoder reranker exists to fix — clustered in `multi_source`, `ambiguous` and `paraphrase`. Adding a lightweight local cross-encoder after fusion, gated available-if-installed like dense retrieval, is now supported by measurement rather than assumption. Still not implemented.
26. **Embedding fine-tuning: supported by the data now, but not the next experiment.** The 313-query evaluation confirms a real, sample-size-robust citizen-vs-statute gap (recall@5 0.527 over 150 citizen-language queries vs 0.724 over 76 legal-terminology ones) and shows 44 of 119 missed chunks (37.0%) are `representation_gap`/`dense_embedding` failures no reranker or fusion retune can reach. The labelled pool is now ~362 query groups (313 + 49), materially above the 153 that run1 concluded was too small. But gaps #23, #24 and #25 each address a larger bucket or a correctness risk at lower cost, and fine-tuning would not fix #23 and might worsen it. Recommended order: #23, then #24, then #25, then re-attempt fine-tuning with the existing reusable `services/ai/finetune/` infrastructure, evaluated held-out-only.

27. ~~Confident wrong-Act answers on legal questions about un-ingested Acts (gap #23)~~ — **resolved this session** by `app/safety/corpus_coverage.py` (see the corpus-coverage guard entry above). Hybrid false accepts 7 → 1, abstention accuracy 0.7572 → 0.7764, zero false fires across all 362 labelled queries. **One residual remains:** `h286` ("how do I file an application for information from a government office") — the RTI question deliberately phrased without naming RTI. A deterministic phrase guard cannot recognise a subject the query never names, and closing it would require a semantic classifier, which is out of scope by standing decision. It is the sole remaining hybrid false accept. If a future evaluation surfaces more un-named-subject false accepts of this shape, that — not another curated pattern — is the signal that the guard's approach has reached its limit.
28. ~~The confidence gate is tuned against a query population it no longer represents (gap #24)~~ — **investigated this session and deliberately left unchanged.** The gate signal is genuinely miscalibrated for citizen language, but the citizen-language true-positive and wrong-Act score distributions overlap almost completely (medians 0.456 vs 0.442), so the true-positive-per-wrong-Act ratio is flat at ~2.0 across the whole 0.30–0.46 sweep and no operating point is better than another. Alternative signals (max/mean of `dense_score` over the returned top-5) trace the same curve. `DEFAULT_MIN_SCORE_BY_MODE["hybrid"]` stays 0.42. Re-open this only if the underlying dense representation changes — a better-separated signal is a prerequisite for a better threshold, not the other way round.
29. ~~Reranking is now supported by measurement (gap #25)~~ — **superseded: implemented, measured, and REJECTED on legal-safety grounds this session.** The candidate-pool premise was verified correct (76.9% of missed chunks reachable in the existing pool-50 set) and the intervention still failed: `hard_negative` recall 0.966 → 0.793, abstention accuracy 0.7764 → 0.6677, top-1 correctness 0.3879 → 0.3772, worse short-title artifact, and worse-on-every-metric on the 49-query control, for +1.7pp citizen-set recall@5 and an ~8x latency increase. **Do not re-propose a cross-encoder reranker on the strength of the candidate-pool argument** — that argument is already known to be true and already known to be insufficient. A future attempt must answer the actual failure mode: a general-purpose reranker has no notion that the BNS and the BNSS are different statutes (it answered two queries naming their Act in full from the other Sanhita), and it rewards short-title boilerplate that names the Act. A legal-domain-tuned cross-encoder might clear that bar; `ms-marco-MiniLM` demonstrably does not.
30. ~~Embedding fine-tuning is now the next intervention worth evaluating — but it is not authorised and no training has been started~~ — **resolved across M12/M13**: run1 failed held-out (too little data), the pool grew to 402 groups, m12_run2 generalised on held-out data with every mandatory safety gate passing (hard-negative 29/29, wrong-Act top-1 down, zero false accepts), and M13 deployed it on the real production path and **promoted** it — see the M13 entries above and in `docs/RETRIEVAL_EVALUATION.md`. The original conditions are preserved below for the record. **Embedding fine-tuning is now the next intervention worth evaluating — but it is not authorised and no training has been started.** Three of the four candidate interventions are resolved (guard shipped, gate investigated with no available operating point, reranking rejected), so the remaining failures are concentrated where the evidence always pointed: `representation_gap` (29 of 119 misses) plus `dense_embedding` (15 of 119) — 37.0% combined, unreachable by any reranker or gate change. The labelled pool is now ~362 query groups (313 + 49) against the 153 that run1 concluded was too small, and the `services/ai/finetune/` infrastructure is reusable as-is. Conditions for any future attempt, unchanged from standing discipline: held-out-only measurement, real before/after numbers on **both** eval sets, and **no promotion at all if `hard_negative` recall or the wrong-Act top-1 rate degrades** — the reranker's failure mode is exactly what a fine-tune could also cause, and it must be caught the same way.

**M1 platform usability**
31. **No token refresh.** The API issues a 15-minute access token and exposes no refresh endpoint, so a session simply ends 15 minutes after sign-in and the user is returned to `/login`. Adding refresh tokens would change the backend auth architecture and was out of scope for an integration milestone. This is the most likely first complaint from anyone actually using the app for a while.
32. **Email verification is development-mode only.** The flow is complete and correct, but the token is delivered in the API response rather than by email (see the M1 entry above). A production deployment must wire a real transport into the `/register` and `/resend-verification` handlers before self-registration is usable by real users — `devVerification()` already returns `undefined` there, so production currently issues a challenge nobody can receive.
33. **API auth tests mock the Mongoose model.** They cover route logic, status codes, hashing and the token lifecycle, but not schema/index behaviour. M5 confirmed against a real MongoDB that the `users.email` unique index genuinely exists and that the role enum rejects, but the committed *test suite* still mocks the model — `mongodb-memory-server` or a test container would keep this covered in CI rather than in a one-off script.
34. `/account` is intentionally minimal (identity, role, verification status, log out). Role-specific dashboards belong to the civic/petition increments, not here.

**M2 civic reporting**
35. **No authority workflow.** A report is created `SUBMITTED` and stays there -- nothing can transition it. Status/priority exist in the model and UI so the transition workflow can be added without a migration, but no endpoint writes them today.
36. **Priority is always MEDIUM.** Automatic priority prediction is deliberately not implemented; the field is a placeholder for the triage milestone.
37. **EXIF stripping covers JPEG and PNG containers only, and is not a substitute for image redaction.** It removes metadata, not content: faces, number plates and identifying detail in the *pixels* are untouched (deferred by instruction). A malformed file stops the container walk early and is rejected rather than partially cleaned.
38. ~~**API auth/civic tests mock Mongoose.**~~ — **resolved in M5** for the schema layer: the enum validators, the coordinate validator and the `location_2dsphere` index were all verified against a real MongoDB (22/22). The *test suites* still mock Mongoose; the live verification is a separate scripted check rather than a committed integration suite, so adding `mongodb-memory-server` or a test container remains worthwhile to keep this covered in CI.
39. **Media is served through the API process** by reading the whole file into memory. Fine at this size and file count; a streaming response or a signed-URL/CDN path is the scaling answer, not more instances.
40. ~~**Not smoke-tested against a live stack**~~ — **resolved in M5.** The full Compose stack runs and the civic flow was exercised end to end against real MongoDB, both through the API and through a real browser session (report creation with image upload, media persistence, IDOR, My Reports).

**M3 authority workflow**
41. **No assignment or ownership among staff.** Any AUTHORITY user can act on any report; there is no "assigned to me", no team, no jurisdiction. That is the documented simulation scope, not an oversight -- modelling wards or departments would mean inventing a government structure the project has not specified.
42. **Priority is not predicted.** It is staff-assigned by design (see M3 above). If a future milestone wants automatic priority, it needs an evidence base first; the SLA mechanics will not need to change when it arrives.
43. **No SLA escalation or reminders.** Overdue is computed and displayed, but nothing acts on it -- no notification, no auto-escalation, no scheduled job.
44. **Reopening restarts nothing.** An ADMIN reopen moves the report back to UNDER_REVIEW but leaves `dueAt` derived from the original submission, so a reopened report is usually immediately overdue. That is arguably correct (the citizen has been waiting since they reported it) but it is a decision worth revisiting with a real workflow in mind.
45. **History has no pagination or retention policy.** Bounded in practice by the state machine, but nothing enforces a ceiling.
46. ~~**Still not smoke-tested against a live stack**~~ — **resolved in M5.** The authority workflow was driven through a real browser against the live stack: a priority change moved the SLA deadline, a `SUBMITTED -> UNDER_REVIEW` transition was recorded in history with actor and note, and the available-actions list advanced to the next valid set.

**M4 petitions**
47. **One signature per *account*, not per person.** The unique index guarantees a citizen account signs a petition at most once, and that is exactly as strong as account identity is -- which is an email address plus a password. Anyone able to register several accounts can add several signatures, and nothing checks address, constituency, age or real identity. Email verification is the only barrier and is still development-mode only (gap #32), so **a petition's signature count should be read as "distinct verified accounts", not "distinct people"**. Closing this needs real identity assurance, which is a product and policy decision, not a code change.
48. **The signature count can drift low, and nothing reconciles it.** By design the drift is one-directional (see M4 above) and the `Signature` collection stays authoritative, but there is no scheduled reconciliation job, no admin recount endpoint and no alert if a count and its row count disagree. A recount is a single aggregation whenever someone decides to run one.
49. **No multi-document transaction**, because `docker-compose.yml` runs a standalone `mongod` and MongoDB requires a replica set for them. The compensating-write scheme above is the substitute. If the deployment ever moves to a replica set, signing and withdrawal become a natural place to use a real transaction and the compensation logic can be deleted.
50. ~~**The petition tests mock Mongoose**~~ — **resolved in M5, and this was the single highest-value test that was missing.** Against the live database the unique `{ petitionId, citizenId }` index was confirmed to exist, and 12 concurrent sign attempts by one citizen produced exactly one signature row with `signatureCount = 1` (verified by inspecting the database, not the route's answer). The original wording is kept below for context. Route logic, RBAC, the transition table, the concurrency ordering and the compensating writes are all covered, and the signature fake deliberately *emulates* the unique index by throwing a real E11000, so the racing-signature tests prove the route handles the constraint correctly. What is **not** exercised is that the constraint actually exists in a live database: the unique `{ petitionId, citizenId }` index, the schema enum validators and the compound read indexes are asserted in code, not against a running `mongod`. Since that index is the module's central security control, an integration test against a real database is the single highest-value test still missing.
51. **The authority queue's `goalMet` filter cannot use an index.** It is a `$expr` comparison of two stored fields (`signatureCount` vs `signatureGoal`), which MongoDB evaluates with a collection scan. Correct and fine at this scale; a denormalised boolean maintained on write would be the fix if the collection ever grows.
52. **The "signed by me" list reads all of a citizen's signature ids** (projected to ids only) in order to paginate over what is actually visible after the removed-petition rule is applied. Bounded per account and cheap in practice, but there is no hard ceiling; a `$lookup` aggregation would push the whole thing into the database if a single citizen ever signed enough petitions for it to matter.
53. **Signatures cannot be withdrawn once a petition leaves `OPEN`.** That is deliberate -- after review, closure or a formal answer the tally is the historical record the authority acted on -- but it means a citizen who changes their mind after the authority picks the petition up has no route to remove their name.
54. **Taking a petition up for review stops signature collection**, because `OPEN` is the only signable state. This is a defensible reading (the authority is now acting on a fixed tally) but it is a product decision worth revisiting: a petition can lose momentum the moment it succeeds in being noticed.
55. **No search and no free-text filtering.** The public list filters by category and status and sorts three ways; there is no text index and no way to find a petition by a word in its title or body.
56. **Petitions cannot be edited, and the trade-off is real.** It protects signers from a text changing underneath them, but a creator who publishes a typo or a wrong date can only close the petition and start again, losing every signature gathered so far. No "correction note" mechanism exists.
57. **Nothing notifies anybody.** A signer is not told when a petition they signed is answered, closed or removed; a creator is not told when the authority acts; staff are not told when a petition reaches its goal. The `goalMet` queue filter is the only "this needs attention" signal, and someone has to go and look at it.
58. **Reinstating a removed petition restores its old signatures.** `REJECTED -> OPEN` is ADMIN-only and appends a reason to the history, but the signature rows and the count survive the removal untouched, so a reinstated petition returns with the support it had. That is intentional (the signatures were genuine) and worth stating, because the alternative -- discarding them -- would make removal destructive in a way the design otherwise avoids.
59. **Rate-limit state is in-process.** `express-rate-limit`'s default memory store means the petition limiters (like the civic ones) reset on restart and are counted per API instance, so they bound abuse from a single process rather than across a horizontally scaled deployment. A shared store is the fix whenever a second instance exists.
60. ~~**Still not smoke-tested against a live stack.**~~ — **resolved in M5.** The Docker daemon is now running and the full five-service Compose stack was brought up, exercised through the API and a real browser, and validated against real MongoDB. See the M5 entry under Completed.

**M5 live stack**
61. ~~**The AI image carries roughly 2 GB of CUDA packages it never executes.**~~ **Resolved and measured in M6:** the Dockerfile installs the CPU-only PyTorch wheel before `requirements-full.txt`, taking the image from **8.61 GB to 2.07 GB**. Original text follows.  Installing `requirements-full.txt` pulls the default `torch` wheel, which brings `cuda-toolkit`, `nvidia-cublas`, `nvidia-cudnn`, `nvidia-nccl`, `triton` and friends; the container reports `cuda_available=False`. The image went 441 MB -> 2.99 GB. A CPU-only wheel (`--extra-index-url https://download.pytorch.org/whl/cpu`) would be a dependency-only change and should recover most of that. **Deliberately not done in M5** — image optimisation was explicitly out of scope for an integration milestone.
62. ~~**The embedding model downloads at runtime, not at build time.**~~ **Resolved in M6:** `HF_HOME` points at the `ai_model_cache` named volume. Verified by recreating the container (changed container id, not a restart) and then loading the model with `HF_HUB_OFFLINE=1`, which only succeeds from cache. A network-isolated first run would still fail on a cold volume. Original text follows.  `all-MiniLM-L6-v2` (88 MB) is fetched from HuggingFace into `/root/.cache/huggingface` on the first `/legal/answer` call. It survives container restarts but **not** container recreation, and a network-isolated deployment would fail on its first request. Pre-baking the model into the image or mounting a cache volume is the fix.
63. ~~**The JWT `role` claim is trusted without a database re-check**~~ **Resolved in M6** by `requireFreshRole`/`withFreshRole` plus `tokenVersion` revocation; privileged routes authorise on stored state, not the token's claim. Original text follows.  (see the M5 security review). A validly-signed token with the correct `iss`/`aud` claiming `AUTHORITY` or `ADMIN` is accepted for a CITIZEN account. This needs the signing secret, so it is standard stateless-JWT design rather than an authentication bypass — but `docker-compose.yml` ships a hardcoded development secret that must never reach production, and a demotion or account deletion is not reflected until the 15-minute expiry. Re-checking the role per request, or shortening the token lifetime, are the available answers.
64. ~~**No `.dockerignore` exists**~~ **Resolved in M6:** a root and an AI `.dockerignore`, both verified against the built images (the AI image still carries `app/` and its mounted `data/`, the API image still carries `packages/contracts`, the web image still carries its built assets). Original text follows.  so build contexts are larger than necessary (the AI context includes `data/`, `.venv/`, `__pycache__/` and fine-tuning checkpoints). Not a correctness defect — the images build correctly — but it slows builds and inflates context transfer.
65. ~~**The live-stack verification is scripted, not committed.**~~ **Partly resolved in M6:** the highest-value part is now a committed 13-test integration suite run against a real `mongod` in CI (`npm run test:integration`), covering index existence, concurrent signing and schema validation. The Compose wiring and the AI image's dependencies are covered by the on-demand `integration.yml` workflow rather than by per-commit CI. Original text follows.  M5's evidence came from throwaway scripts run against the running system, not from tests in the repository. Nothing in CI would catch a regression in index creation, the Compose wiring or the AI image's dependencies. Turning the highest-value parts (index existence, the concurrent-signature proof, the container's ability to import `sentence-transformers` and answer/abstain) into a committed integration suite is the natural follow-up.
66. **The API rate limiter bounds bulk end-to-end testing.** The app-wide limit is 100 requests per 15 minutes per IP with an in-process store (gap #59), so a full smoke run has to be split across API restarts. Harmless in production terms, but worth knowing before anyone writes a larger automated end-to-end suite.

## Development philosophy (unchanged from Increment 1)

Work one increment at a time. Inspect the repo before changing anything. Preserve existing working functionality. Keep services modular and loosely coupled. After each increment, run typechecks/tests/builds and report exactly what was verified — never claim something works without having run it. Don't add technology (Kafka, Neo4j, Qdrant, PostGIS, voice, multilingual, etc.) unless the current increment actually needs it.
