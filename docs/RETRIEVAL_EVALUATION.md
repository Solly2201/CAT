# Retrieval evaluation: from BM25 to a fine-tuned hybrid production path

> **Read this first.** This document is a **chronological research
> record**, not a summary of the current system. It runs from the
> original BM25-vs-hybrid decision through RRF tuning, citizen-language
> evaluation, several **failed and rejected** experiments, embedding
> fine-tuning, and finally to the deployed model. Numbers appear in the
> order they were measured, against the corpus and eval sets that existed
> at the time.
>
> **The final, authoritative numbers are in the "FINAL PRODUCTION
> EVALUATION" section immediately below, and in the M12/M13 sections at
> the end.** Every number between them is historical. Do not quote a
> mid-document figure as a current result.

This records how CAT decided to move from BM25-only retrieval to hybrid
(BM25 + dense + Reciprocal Rank Fusion) retrieval and then to a
fine-tuned dense model, with real measurements against this project's
actual ingested corpus -- not a synthetic benchmark, and not added
because "hybrid sounds better." See `docs/PROJECT_STATE.md` for where
this sits in the project timeline and `docs/ARCHITECTURE.md` for how it
fits the overall pipeline.

**No generative LLM is involved anywhere in this evaluation or in what it
evaluates.** `services/ai/eval/run_eval.py` calls only
`app.retrieval.search` and `app.generation.pipeline.handle_legal_query`
-- both pure-retrieval/deterministic.

---

## FINAL PRODUCTION EVALUATION (authoritative)

The frozen system: corpus **1,827 chunks across 10 Acts**, dense model
**`data/models/m12_run2`** (384-dim, fine-tuned from
`sentence-transformers/all-MiniLM-L6-v2`), hybrid retrieval with a top-50
candidate pool per method, weighted RRF (k=5, dense 3.0 / BM25 1.0),
top_k 5, and a hybrid confidence floor of **0.41** applied to the top
hit's `dense_score`.

### The four measurement series, and what each one actually measures

This document contains four series that are **not comparable to each
other**. Mixing them produces false claims.

| # | Series | What it measures | Where |
| --- | --- | --- | --- |
| 1 | **Historical raw-query series** | Retrieval quality on the *raw* query text, before `app.query.normalize` runs. It measures the retrieval layer in isolation, **not the path the product runs.** Reproduced by the default `run_eval.py`. Every historical number in the body of this document belongs to this series. | body of this doc |
| 2 | **M12 production-path baseline** | The same pipeline the product runs (`--production-path` retrieves on the normalised text), with the **base** `all-MiniLM-L6-v2` model. This is the *before* column of the final comparison. | M12 section |
| 3 | **Final deployed `m12_run2`** | The same production path with the promoted fine-tuned model. **These sets contain queries the fine-tune was trained on** -- they are the deployed system's benchmark, not generalisation evidence. | M13 section |
| 4 | **Held-out production-path evaluation** | Series 2 vs 3 restricted to ids in `finetune/data/test.jsonl`, never trained or selected on. **This, and only this, is the generalisation claim.** | M13 section |

Series 1 and series 2/3/4 differ in the text being retrieved on, so their
absolute numbers are not comparable even for the same model. Series 3 and
series 4 differ in which queries are scored. A jump between series is not
a result.

### Series 3 — final deployed benchmark (contains trained-on queries)

Same corpus, queries, normalisation, guards, gate floor, fusion weights
and scoring code on both sides; **the only variable is the embedding
model behind the dense index.** Every candidate number was reproduced
twice, byte-identically.

| Metric | Citizen 281: baseline -> m12_run2 | Control 46: baseline -> m12_run2 |
| --- | --- | --- |
| recall@5 | 0.7448 -> **0.9554** | 0.8623 -> **0.9674** |
| MRR | 0.5656 -> **0.8800** | 0.7341 -> **0.9246** |
| nDCG@5 | 0.6040 -> **0.8984** | 0.7476 -> **0.9261** |
| top-1 citation correctness | 0.4448 -> **0.8185** | 0.6522 -> **0.8913** |
| abstention accuracy | 0.8562 -> **0.9233** | 0.9796 -> 0.9592 |
| false accepts | 0 -> **0** | 0 -> **0** |
| false abstains | 45 -> **24** | 1 (q19) -> 2 (q19, q17) |
| wrong-Act top-1 | 43 -> **19** | 3 -> 3 (no new) |
| hard-negative recall | 28/29 -> **29/29** | -- |

Citizen 281 = the 281 non-abstain rows of the 313-row
`eval/queries_human.jsonl`. Control 46 = the 46 non-abstain rows of the
49-row `eval/queries.jsonl`.

> **NEVER present the 281-query benchmark as a held-out generalisation
> result.** The fine-tune's training pool was drawn from these labelled
> sets. It is the correct number for "how well does the deployed system
> do on our benchmark" and the wrong number for "how well does it
> generalise".

### Series 4 — held-out generalisation (never trained or selected on)

| Metric | Citizen 41 | Control 9 |
| --- | --- | --- |
| recall@5 | 0.7634 -> **0.8732** | 0.8333 -> 0.8333 (equal) |
| MRR | 0.5687 -> **0.7122** | 0.7259 -> **0.8000** |
| top-1 citation correctness | 0.4634 -> **0.6098** | 0.6667 -> **0.7778** |
| abstention accuracy | 0.7561 -> **0.8293** | -- |
| false accepts | 0 -> **0** | -- |
| false abstains | 10 -> **7** | -- |

The held-out improvement reproduces on the path production actually runs.
Held-out wrong-Act moved 4 to 8 and every case was inspected
individually -- see the M13 section for the per-case severity analysis
(two abstain rather than answer, one is a label gap, one is a genuine
mild adjacent-domain regression).

### Series C — follow-up / context benchmark (40 rows)

Condition follow-ups 19/21 with context (fragment-only baseline 6/21),
ambiguous 4/4, no-context 4/4, guarded 6/6 with byte-identical reasons,
not-emergency 2/2, standalone override 2/3. `f04` -- the long-standing M8
FIR-copy recall miss -- is fixed. Residuals: `f22` (ranking), `f24`
(`rti:19`), `f35` (now abstains; conservative direction).

### Reproduction

```bash
cd services/ai
export DENSE_EMBEDDING_MODEL=data/models/m12_run2
python scripts/ingest_corpus.py                                   # 1,827 chunks, mode=hybrid

# Series 2/3 -- the final production-path numbers above
python eval/run_eval.py --production-path --mode hybrid           # control 46
python eval/run_eval.py --production-path --mode hybrid --human   # citizen 281
python eval/run_context_eval.py                                   # follow-up 40

# Series 1 -- the historical raw-query series in the body of this document
python eval/run_eval.py                                           # bm25 vs dense vs hybrid, top_k=5
python eval/run_eval.py --mode hybrid --top-k 10
python eval/run_eval.py --json eval/last_run.json                 # full per-query dump

# Reproduce the model artifact itself (seeded, deterministic splits)
python finetune/build_dataset.py
python finetune/train.py --run-name m12_run2
python finetune/eval_heldout.py --run-name m12_run2
```

Swapping the model back to the base checkpoint to reproduce the baseline
column is `DENSE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`
plus a re-ingest -- and note that the Python test suite rebuilds the real
index, so `tests/conftest.py` pins the variable to whatever the on-disk
manifest records (see the M13 section's incident write-up).

### What was measured and REJECTED

Kept because a rejected result is evidence too, and because each of these
gets re-proposed on intuition:

| Rejected | Why |
| --- | --- |
| Cross-encoder reranking (`ms-marco-MiniLM`) | `hard_negative` recall 0.966 -> 0.793, abstention accuracy 0.7764 -> 0.6677, worse on every metric on the control set, ~8x latency. A general-purpose reranker has no notion that the BNS and the BNSS are different statutes. |
| A separate citizen-language concept index | -0.082 / -0.157 / -0.246 at top-1/2/3 concept, and `hard_negative` recall 0.966 -> 0.724. |
| Generic edit-distance spelling correction | Statutes do not contain ordinary English, so "unknown token" is not "misspelled token" ("texting" -> "testing", "goons" -> "goods"). |
| Agreement-branch confidence gate | +5 good answers for +2 wrong-Act answers: both retrieval methods can agree on the same wrong chunk. |
| RRF weight retuning at M9 | Not a clean win; not applied. |
| FAISS | Brute-force NumPy cosine is sub-millisecond at this corpus size. |
| Raising the global confidence threshold again | The true-positive and wrong-Act score distributions overlap almost completely (medians 0.456 vs 0.442); no operating point dominates. Solved instead by the non-score-based topic-relevance and corpus-coverage guards. |

---

# PART B: HISTORICAL RESEARCH RECORD

## Evaluation set

> **Since updated. The counts in this section are the ORIGINAL ones and
> are historical.** `eval/queries.jsonl` finally has **49 queries (46
> non-abstain, 3 abstain-expected)**, spanning all ten ingested sources
> -- the `ambiguous` and `source_specific` categories were added later,
> and RTI, which was not yet ingested when this set was rebuilt, appears
> in it only as a single labelled target plus abstain-expected controls.
> The corpus those 49 queries now run against is **1,827 chunks across 10
> Acts**, not the 395 described below. The section that follows describes
> the original evaluation this document records, at the point BM25 vs
> hybrid was decided -- see the FINAL PRODUCTION EVALUATION section at
> the top of this file for the current sets and their results.

`services/ai/eval/queries.jsonl` -- 30 hand-curated queries against the
actually-ingested corpus (395 chunks across Constitution, BNS, BNSS,
BSA as of this evaluation), each with a hand-verified ground-truth
`relevant_chunk_ids` set (checked against the real chunk text, not
guessed) or `expect_abstain: true`. Categories:

| Category | Count | Tests |
| --- | --- | --- |
| `direct_lexical` | 11 | Exact section-title / term matches -- the case BM25 should win outright |
| `paraphrase` | 8 | Synonym-heavy rephrasing with low direct term overlap -- the case dense embeddings exist for |
| `distractor` | 1 | A query with a strong lexical false-friend elsewhere in the corpus (see "Article 19 vs 105" below) |
| `multi_source` | 2 | Evidence genuinely spans more than one source |
| `abstain_expected` | 7 | Topics documented as NOT yet ingested (FIR, bail, compounding, theft/robbery, burden of proof) plus two fully out-of-domain control queries ("best restaurants in mumbai", "how to bake a chocolate cake") |

Retrieval-quality metrics (Recall@5, Precision@5, MRR, nDCG@5,
top-1 citation correctness) are computed only over the 23 non-abstain
queries, since precision/recall against an empty ground-truth set is
undefined. Abstention accuracy is computed over all 30 queries by
running the full `handle_legal_query()` pipeline (Risk/UPL -> retrieval
-> confidence gate), separately per mode via `RETRIEVAL_MODE`.

## Baseline: BM25-only

First measurement, before any dense/hybrid code existed:

| Metric | Value |
| --- | --- |
| Recall@5 | 0.51 |
| MRR | 0.46 |
| nDCG@5 | 0.45 |
| Top-1 citation correctness | 0.39 |
| Abstention accuracy | 0.77 (but see below) |

The abstention number is misleading in isolation: BM25's raw score has
no absolute meaning (it's an unbounded, corpus-relative sum of
per-term weights), so `DEFAULT_MIN_SCORE_BY_MODE["bm25"] = 3.0` cannot
distinguish "genuinely uncovered legal topic" from "completely
off-topic query." Every one of the 7 `abstain_expected` queries --
including the two fully out-of-domain control queries -- scored above
the floor and got a confident-looking answer with a real (but
irrelevant) citation attached. This is the exact failure this project
already flagged before hybrid work started (see the `DEFAULT_MIN_SCORE`
docstring history in `app/generation/pipeline.py`): a wrong-topic
citation shown as if authoritative is a worse failure than abstaining,
in a legal-information context.

## A real bug found along the way: titles weren't indexed

The first hybrid pass revealed that `app/ingestion/index_build.py` only
ever tokenized `chunk.text` (the section body), never `chunk.title`
("Estoppel", "Right of private defence of body and of property") --
even though titles are exactly the vocabulary a citizen is likely to
search with, and the chunker (`app/ingestion/chunk.py`) deliberately
keeps titles out of the body it stores. A single-word query like
"estoppel" could miss BSA s.121 entirely, because the word "estoppel"
never recurs inside the section's own body text.

Fix: `app/ingestion/index_build._index_text()` now indexes
`"{title}. {text}"` (title included only for matching -- the excerpt
shown to a citizen is still exactly `chunk.text`, unchanged, preserving
the no-fabrication/verbatim-text guarantee). This alone raised the BM25
baseline from Recall@5 0.51 -> 0.62.

A second bug compounded the first: BM25 tokenization split on
whitespace only (`text.lower().split()`), so `"Estoppel."` (title,
period glued on by the `"{title}. {text}"` join) never matched a query
token `"estoppel"`. Fixed by extracting `\w+` word runs in a single
shared tokenizer (`app/retrieval/tokenize.py`) used identically at
index-build time and query time, so the two can never drift out of
sync again. This raised the BM25 baseline further, to Recall@5 0.79.

Both fixes apply to every mode (BM25, dense, hybrid) since they're
upstream of all three -- the numbers throughout this document are
post-fix.

## Dense retrieval

`sentence-transformers/all-MiniLM-L6-v2` (384-dim, local, no paid API),
L2-normalized at encode time so cosine similarity is a plain dot
product at query time (`app/retrieval/embeddings.py`). Persisted as
`data/index/dense_vectors.npy`, row-aligned with
`data/index/chunk_manifest.jsonl`. At ~400 chunks, brute-force
`vectors @ query_vector` is sub-millisecond -- no FAISS/ANN index is
used or needed at this corpus size (see "Why no FAISS" below).

| Metric | Value |
| --- | --- |
| Recall@5 | 0.86 |
| MRR | 0.83 |
| nDCG@5 | 0.83 |
| Top-1 citation correctness | 0.83 |
| Abstention accuracy | 0.80 (threshold 0.45, tuned -- see below) |

Dense alone beats BM25 alone on every quality metric here, expected
given 8 of 23 queries are deliberately synonym-heavy paraphrases. It
also abstains far more sensibly than raw BM25 once its threshold is
tuned, because cosine similarity is bounded and comparable across
queries in a way an unbounded BM25 score is not.

## Hybrid: Reciprocal Rank Fusion

`app/retrieval/fusion.py` implements (weighted) RRF: each ranked list
contributes `weight / (k + rank)` per item; an item missing from a list
contributes nothing from it (no invented score). Both candidate lists
are capped to the top 50 per method before fusion (`app/retrieval/
search.py`'s `_FUSION_CANDIDATE_POOL`) -- items past ~50th barely move
a `1/(k+rank)` term at the k values used here, so this bounds fusion
cost without changing which chunks can plausibly reach the final
top-`k`.

**k=60 (the RRF paper's standard default, tuned for thousand-document
web-search candidate pools) measurably underperformed plain dense
retrieval here.** A parameter sweep across `k in {5,8,10,15,30,60}` and
a dense weight in `{1, 1.3, 1.5, 1.8, 2, 2.5, 3}` (BM25 weight fixed at
1.0) against this project's 23 scored queries found:

- k=60, unweighted: Recall@5 0.75, MRR 0.61 -- **worse than dense alone
  on every metric**, because at that scale a document's exact rank
  barely moves its fusion contribution, so fusion collapses toward
  noise rather than combining genuine signal from both methods.
- **k=5, BM25 weight 1.0, dense weight 2.0** (the values now in
  `app/retrieval/fusion.py`'s `DEFAULT_RRF_K` / `DEFAULT_DENSE_WEIGHT`):
  clearly and consistently the best fit at this corpus size.

Final hybrid numbers, k=5 / dense-weighted 2x:

| Metric | BM25 | Dense | Hybrid |
| --- | --- | --- | --- |
| Recall@5 | 0.79 | 0.86 | **0.94** |
| Precision@5 | 0.22 | 0.19 | 0.21 |
| MRR | 0.69 | 0.83 | 0.82 |
| nDCG@5 | 0.69 | 0.83 | **0.84** |
| Top-1 citation correctness | 0.61 | 0.83 | 0.74 |
| Abstention accuracy | 0.77 | 0.80 | **0.83** |

**Hybrid beats the BM25 baseline on every single metric**, and beats
plain dense on recall, nDCG, and abstention accuracy while trading
away a little top-1 precision. That trade-off is acceptable for this
product specifically because the legal-answer pipeline shows every
retrieved excerpt in the response window, never just the top-1 result
merged into a single answer (`app/generation/pipeline.py`'s
`build_legal_answer` returns one `Excerpt` per retrieved chunk) -- so
"is the right law somewhere in the returned set" (recall) matters more
to what a citizen actually sees than "is it ranked first" (top-1
precision). This is why `tests/test_retrieval.py::
test_search_finds_arrest_provision_for_sunset_query` asserts the
correct section appears in the top-5 window rather than strictly at
rank 0 -- see that test's docstring.

### Why the fused RRF score can't gate confidence

An early version gated the confidence threshold on the fused RRF score
itself, using a placeholder cutoff. Measurement showed this was
unusable: on this corpus, a query's single top-ranked hybrid result
scores in a narrow ~0.027-0.033 band **regardless of whether the query
is genuinely covered by the corpus** -- RRF's score reflects a
candidate's rank position within a small pool, not its absolute
semantic relevance, so "ranked first among 50 candidates" stays true
even for a nonsense query. Every one of BM25's original 7 false
positives still passed at any reasonable RRF threshold.

Fix: `app/generation/pipeline._passes_confidence_gate()` gates hybrid
results on the top hit's `dense_score` (bounded, and the best-separated
signal measured) instead of its fused score, while still using the
fused ranking to decide *which* chunks are top hits. Threshold sweeps
against the labeled eval set (`DEFAULT_MIN_SCORE_BY_MODE`):

- `dense`: 0.45 (false_answer: bail/compounding/burden-of-proof
  near-misses; false_abstain: 2-3 borderline paraphrases)
- `hybrid`: 0.40 (false_answer: same 3 near-miss legal topics;
  false_abstain: 2 borderline paraphrases)

Both remaining false-answer categories (q24 "bail procedure", q25
"compounding of offences", q27 "burden of proof") are queries where the
corpus has genuinely adjacent-but-not-actually-relevant content (e.g.
BNSS s.39's non-cognizable-arrest discretion is topically near "bail"
without being bail procedure) -- a harder problem than threshold
tuning can fully solve, and a known, documented limitation rather than
a silent gap (see "Remaining limitations" below).

### The Article 19 vs 105 distractor case

Query "freedom of speech and expression" (q20) is designed to expose a
real corpus quirk: Constitution Article 105 ("freedom of speech in
**Parliament**") and Article 194 (same, for state legislatures) are
strong *lexical* false friends for the actual fundamental-rights
provision, Article 19(1)(a). Under BM25 alone and dense alone, Article
19 loses to these distractors. Hybrid fusion corrected this case --
neither signal alone was enough, but combining BM25's confidence that
19 contains the phrase with dense's semantic read pulled it back to a
correct top rank. This is the one concrete example in this evaluation
of hybrid fusion fixing an error neither individual method resolved.

## Why no FAISS

`docs/ARCHITECTURE.md`'s original service diagram named FAISS
alongside BM25. At ~400 chunks, brute-force NumPy cosine similarity
(`vectors @ query_vector`, all 395 rows) runs in well under a
millisecond -- an approximate-nearest-neighbor index exists to avoid
scanning millions of vectors, which does not describe this corpus.
Adding FAISS now would mean a second native binary dependency
(`faiss-cpu`) for zero measured benefit. If the corpus grows by
orders of magnitude (full BNS/BNSS/BSA ingestion, additional Acts),
revisit this -- `app/retrieval/embeddings.py` and the persisted
`dense_vectors.npy` format were kept swap-compatible with an ANN index
specifically so that migration wouldn't require touching the
generation/pipeline layer above it.

## Reranking: deferred, not added

The target architecture diagram includes an optional reranker stage.
It was deliberately **not** added this iteration. Reasoning:

1. Hybrid already beats the BM25 baseline on every metric measured,
   which was this evaluation's actual mandate -- a reranker's job would
   be to improve on hybrid specifically, and that's a separate,
   unproven claim.
2. Inspecting the remaining misses (`eval/last_run.json`, e.g. q06, q07,
   q16 at full-corpus rank 8-25) showed most are not "the right answer
   is a few ranks too low in an otherwise-good candidate list" --
   exactly the shape of problem a reranker fixes -- but genuine
   embedding-model/vocabulary gaps (a general-purpose 384-dim model
   with no legal-domain fine-tuning under-weighting formal statute
   phrasing against a conversational paraphrase). A cross-encoder
   reranker over the existing candidates would not obviously fix that;
   better legal-domain embeddings or corpus growth would.
3. A reranker adds real cost (a second model, extra inference latency
   per query) for a v1 capstone system at ~400 chunks, where that cost
   is harder to justify than it would be at production scale.

If corpus growth or future evaluation shows the remaining top-5 misses
are actually reranking-shaped (correct chunk present but consistently
mis-ordered within a decent candidate pool), add a lightweight local
cross-encoder (e.g. `cross-encoder/ms-marco-MiniLM-L-6-v2`) as an
optional stage after fusion, gated the same way dense retrieval is
(available-if-installed, degrade gracefully if not) -- not before that
evidence exists.

**Re-confirmed, not revisited, after the failure-analysis pass below:**
of the queries still missing their target chunk in the top-5 after the
Constitution-title and RRF-weight fixes, the two worst (q17, q46) don't
even enter either method's top-50 fusion candidate pool -- there is
nothing for a reranker to reorder. The rest are minor rank
perturbations (9-53) scattered across unrelated sources, not a
systematic "right answer buried in an otherwise-good list" pattern.
Deferral stands.

**Superseded by the 313-query evaluation (see "Citizen-language
evaluation set expanded to 313 query groups" below).** The deferral above
rests entirely on the claim that the remaining misses are not
reranking-shaped. That claim was true and independently re-verified at 49
and at 129 queries. At 313 queries it no longer holds: 36 of 119 missed
target chunks (30.3%) sit inside *both* methods top-50 candidate pools
and are still ranked below 5 by fusion -- the exact "right answer buried
in an otherwise-good candidate list" pattern a cross-encoder reranker
exists to fix -- clustered in the multi_source, ambiguous and paraphrase
categories. Reranking was implemented and measured in the session
that followed, and **rejected on legal-safety grounds** -- the
candidate-pool premise proved correct (76.9% of missed chunks were
reachable) and the intervention still failed, degrading `hard_negative`
recall 0.966 -> 0.793, abstention accuracy 0.7764 -> 0.6677, and the
short-title artifact, for +1.7pp recall@5. See "Safety guard,
confidence-gate calibration, and the rejected reranker" below for the
full numbers. This deferral is therefore no longer an untested
assumption: it is a tested and rejected approach.

## Failure-analysis-driven fixes: Constitution titles + RRF retune

A full per-query failure analysis was run over `eval/queries.jsonl`'s
45 non-abstain queries: for every query where hybrid missed its target
chunk's top-5 rank or top-1 slot, BM25/dense/hybrid full rankings (not
just the top-5 window) were compared against the expected source and
section to classify the cause (vocabulary mismatch, missing title
metadata, chunking, embedding quality, RRF weighting, or confidence
gating).

**Dominant cluster: missing Constitution title metadata.** 9 of the
failing queries (q16, q17, q18, q19, q20, q21, q22, q45, q46) all
needed a Constitution article whose marginal-note title
(`chunk.title`) was empty -- `app/ingestion/chunk.py`'s
`chunk_constitution()` always set `title=""`, unlike the gazette-style
sources (BNS/BNSS/BSA/CPA2019/JJ Act), which get best-effort title
recovery via `extract_gazette_titles()`. Direct inspection of
`data/legal-corpus/constitution/raw.txt` confirmed the titles *do*
exist in the extracted text but are reordered by the source PDF's
two-column layout into per-page trailer blocks, often splitting a
single sentence across the reordered block. A general parser to
recover all 346 articles' titles was attempted and abandoned after
several iterations -- footnote, title, and page-number content
interleave in page-dependent order with no reliable general boundary,
and a wrong article-to-title mapping is a correctness risk this
project's anti-fabrication stance won't accept. Instead,
`chunk.py`'s `_KNOWN_ARTICLE_TITLES` is a small, hand-verified table
covering exactly Part III (Fundamental Rights, Articles 12-22, the
only part any eval query needs a title from), each title transcribed
directly from the raw two-column-reordered text and checked against
that article's own body content -- the same narrow,
evaluation-justified-only pattern as `query_expand.py`'s abbreviation
dict. Guarded by
`tests/test_ingestion.py::test_constitution_fundamental_rights_titles_are_recovered`.

A real bug was caught while building this: `chunk_constitution()` is
shared by every two-column gazette source, so the first version of the
table leaked Constitution titles into unrelated Acts sharing the same
article/section numbers (e.g. `jj2015:14` was overwritten with
"Equality before law." instead of its own correct title, "Inquiry by
Board regarding child in conflict with law"). Fixed by scoping the
table lookup to `source_id == "constitution"`, with a regression test
(`test_constitution_titles_do_not_leak_into_other_gazette_sources`)
guarding against the same leak recurring.

**Second cluster: RRF dense weight no longer optimal.** With BM25
meaningfully stronger on the paraphrase queries the title fix
targets, re-running the same k / dense-weight grid this document's
original tuning used (k in `{3,5,8,10,15}`, dense weight in
`{1,1.3,1.5,1.8,2,2.5,3}`, BM25 weight fixed at 1.0) against the
title-fixed index found dense weight 2.5 (k unchanged at 5) a clean
improvement over the previous 2.0 -- not a trade-off, since MRR,
nDCG@5, top-1 correctness, and abstention accuracy were all flat or
better alongside the recall gain. Applied in `fusion.py`'s
`DEFAULT_DENSE_WEIGHT`.

**No new query-expansion or confidence-gate change was justified** --
no abbreviation-style gap comparable to FIR/NCR appeared in the
failure set, and no evidence supported moving the hybrid confidence
floor from its existing 0.42.

### Before / after (hybrid, top_k=5, 45 non-abstain queries)

| Metric | Before | After | Δ |
| --- | --- | --- | --- |
| Recall@5 | 0.7407 | 0.8074 | +0.067 |
| Precision@5 | 0.1600 | 0.1733 | +0.013 |
| MRR | 0.6341 | 0.6670 | +0.033 |
| nDCG@5 | 0.6324 | 0.6734 | +0.041 |
| Top-1 citation correctness | 0.5333 | 0.5556 | +0.022 |
| Abstention accuracy | 0.9796 | 0.9796 | unchanged |

Recall moved 0.7407→0.7852 from the title fix alone, then →0.8074
after the RRF retune. No new wrong-Act false positives: hybrid's
false-answer list stayed empty throughout (bm25's 4 pre-existing
out-of-domain false answers, q28/q29/q35/q49, are untouched by this
work and unrelated to it). 60/60 Python tests pass.

**What remains, and why it's not (yet) another fix:**

- **q17** ("government cannot punish me for something that wasn't a
  crime" → `constitution:20`) and **q46** ("constitutional equality
  and legal protection of women from abuse at home" →
  `constitution:15`) -- the correct chunk doesn't enter either
  method's top-50 candidate pool at all, even with the title now
  indexed. A genuine embedding-model/vocabulary gap (the paraphrase
  shares almost no vocabulary with the statute text): needs a
  legal-domain-tuned embedding model or corpus/query-set growth, not a
  retrieval-pipeline change.
- **q15** (`bnss:38`, "can my lawyer be present when police question
  me") -- BNSS section 38's own title wasn't recovered by the
  *separate*, PDF-coordinate-based `extract_gazette_titles()` pass
  (BNSS coverage note: ~51% of sections recovered). Same category of
  problem as the Constitution fix, different mechanism; not this
  session's dominant cluster.
- **q21/q22/q45** (multi-source queries needing both a BNSS/JJ-Act
  procedural section and `constitution:22`) -- already receive partial
  recall credit since the other relevant chunk in each pair ranks #1;
  the constitutional citation sits at rank 11-22 among genuinely
  adjacent sections. Corpus density, not a bug.

## Query preprocessing: mostly deferred, one narrow exception added

No general synonym expansion, spelling correction, or query rewriting
was added. This section's original conclusion held for a while: the
paraphrase category in this evaluation tests whether the *retrieval
methods themselves* (dense embeddings specifically) handle vocabulary
variation without needing a preprocessing layer, and hybrid's
paraphrase-query results were adequate without one.

The stated trigger condition -- "revisit only if future evaluation
queries expose failures specifically attributable to ... abbreviations"
-- was met after the corpus expanded to include BNSS's FIR chapter
(ss.173-196): "how do I file an FIR" false-abstained, because "FIR"
(the term nearly every citizen actually uses) appears almost nowhere
in BNSS's own statutory text (s.173 is titled "Information in
cognizable cases" and never uses the abbreviation). `app/retrieval/
query_expand.py` was added specifically for this: a fixed dict of 2
well-established Indian legal abbreviations (FIR, NCR), expanded by
*appending* the spelled-out form to the query at search time so the
original tokens are preserved. This is not a general synonym model, a
misspelling corrector, or a reranker -- it is the same narrow,
evaluation-justified exception the original deferral decision always
allowed for, and should stay that narrow unless evaluation names
another specific gap.

## Topic-relevance guard: closing the out-of-domain gap without another threshold raise

The "hybrid floor was raised 0.40→0.42" limitation below flagged that
two stress-test out-of-domain queries ("what is the income tax slab",
"how do I get a driving licence") still scored ~0.45-0.49 -- inside
the same range as a genuine low-confidence paraphrase (q20 at
0.4531) -- so no single global dense-score threshold could separate
them without also losing q20. Inspecting the actual top hits confirmed
why: "income tax slab" retrieves Constitution Article 276 (state
taxation power, which genuinely says "tax on income"), and "driving
licence" retrieves IT Act Section 22 (digital signature certificate
"licence" applications) -- both share real vocabulary with the query,
just from a completely different real-world topic. A bounded score
cannot distinguish "the right law, weakly matched" from "the wrong
law, strongly matched on one shared word," because both land in the
same numeric band.

Tried and rejected before landing on the actual fix: a lexical
term-overlap ratio between the query's content words and the top
result's indexed text. Measured across the full 49-query eval set, it
did not separate the two cases -- genuine paraphrase queries
deliberately avoid literal term overlap (by design, that's what the
`paraphrase` category tests) and scored as low as 0.0-0.4 overlap,
the same range as the out-of-domain queries, so this signal would have
rejected genuine paraphrases at any threshold that also caught the
false positives. A BM25-top1/dense-top1 source-agreement signal was
also measured and rejected the same way (genuine paraphrase queries
disagreed on source just as often as the out-of-domain queries did).

The fix that shipped instead: `app/safety/topic_relevance.py`, a
curated deterministic phrase-pattern guard run before retrieval (see
`docs/ARCHITECTURE.md`'s "Topic-relevance guard" and
`docs/PROJECT_STATE.md`'s corresponding entry for the full design
rationale and code pointer). It matches the query's topic directly
(company registration, income tax, driving licence/vehicle
registration, identity documents, everyday non-civic subjects) instead
of trying to infer topic mismatch from a retrieval score, so it is
unaffected by vocabulary overlap either way.

Verified effect (`python eval/run_eval.py`, same 49-query set): hybrid
recall@5/precision@5/MRR/nDCG@5/top-1-citation-correctness on the 45
non-abstain queries are byte-identical to the pre-guard numbers below
(0.8074/0.1733/0.6670/0.6734/0.5556) -- expected, since the guard only
changes pre-retrieval gating for abstain-expected queries, never
ranking for queries it doesn't match. Abstention accuracy: hybrid
stayed at 0.9796 (it was already catching these cases via the score
gate for two of the three original stress-test false positives);
bm25-only mode improved 0.9184→0.9796, because bm25 has no bounded
score to fall back on and previously answered all 4 out-of-domain
control queries confidently from the wrong Act -- the guard runs
before mode-specific search, so it protects every mode uniformly, not
just hybrid.

## New single-column source PDFs (BNS/BNSS/BSA/CPA2019/JJ Act): re-established baseline

The user replaced the source PDFs for these five sources with plain
single-column India Code "bare Act" text (consolidated as on 6th
October 2025) in place of the old two-column gazette layout -- see
`docs/PROJECT_STATE.md` and `docs/LEGAL_SOURCES.md`'s "New
single-column PDFs" for the extraction/chunking integration details.
This measurably changed the indexed text for ~1,274 sections (cleaner
extraction, near-100% titles instead of 40-57%, and in at least one
case -- BNSS s.43 -- genuinely different current statutory wording, not
just formatting), so the existing RRF weighting (tuned against the old
embeddings) was re-checked rather than assumed to still be optimal.

**Same weights, new corpus** (before any re-tuning): hybrid recall@5
0.8074 -> 0.7926 (a real dip), while MRR, nDCG@5, and top-1 citation
correctness all *improved* (0.6670->0.6748, 0.6734->0.6861,
0.5556->0.5778). No new wrong-Act false positives; abstention accuracy
unchanged. This mixed signal -- some metrics up, recall down -- pointed
at a fusion-weighting mismatch rather than a corpus-quality problem,
since precision-flavored metrics (which don't depend on RRF's relative
weighting reaching every relevant chunk) improved while recall (which
does) dropped.

**Re-swept RRF** using the same method as prior sessions (k in
`{3,5,8,10,15}`, dense weight in `{1,1.3,1.5,1.8,2,2.2,2.5,3}`, BM25
weight fixed at 1.0) against the new index: dense weight 3.0 (k
unchanged at 5) was a clean improvement over both the pre-swap baseline
and the un-retuned post-swap numbers on every metric measured -- not a
trade-off. Applied in `fusion.py`'s `DEFAULT_DENSE_WEIGHT`.

**One evaluation-justified citizen-language expansion.** BNSS s.38 (now
correctly titled "Right of arrested person to meet an advocate of his
choice during interrogation", vs. ~51% title coverage before) still
didn't surface in the top-50 fusion candidate pool for q15's citizen
phrasing, "can my lawyer be present when police question me" -- direct
inspection found its dense rank was 18 and bm25 rank 74, both too low
to matter, because the query and the section title share almost no
literal vocabulary ("lawyer"/"advocate", "police question"/
"interrogation") despite describing the same right. Tested directly
against `search()`: appending "interrogation" alone (the single term
measured to matter -- "advocate" alone helped less) moves BNSS s.38
from outside the top-20 to rank 1. Added as `query_expand.py`'s
`_CONCEPT_PHRASES` (a phrase-pattern sibling to the existing
abbreviation dict), scanned against every other query in
`eval/queries.jsonl` to confirm the trigger phrase fires only on q15.

**q17 and q46 checked again and confirmed NOT vocabulary-expansion
problems.** Re-measured against the new index: `constitution:20`
(q17's target) sits at dense rank 89, `constitution:15` (one of q46's
two targets) at dense rank 50 -- both outside or at the very edge of
the 50-candidate fusion pool a query-expansion term would need to pull
them into. Unlike q15, there's no single missing term that plausibly
closes an 89-rank gap without guessing at unverified terminology (q17's
query paraphrases the legal concept "ex post facto law", a term that
doesn't appear anywhere in the Constitution's own text, so appending it
wouldn't help retrieval and would only be an unverified label). Per the
explicit instruction not to force expansion without evaluation
justification, nothing was added for either query -- they remain the
same embedding-model/corpus-density limitation documented in "Failure-
analysis-driven fixes" above, now re-confirmed against a materially
different corpus and still present.

### Before / after (hybrid, top_k=5, 45 non-abstain queries)

| Metric | Before (old PDFs) | After (new PDFs + RRF re-tune + concept expansion) | Δ |
| --- | --- | --- | --- |
| Recall@5 | 0.8074 | 0.8370 | +0.030 |
| Precision@5 | 0.1733 | 0.1822 | +0.009 |
| MRR | 0.6670 | 0.7096 | +0.043 |
| nDCG@5 | 0.6734 | 0.7227 | +0.049 |
| Top-1 citation correctness | 0.5556 | 0.6222 | +0.067 |
| Abstention accuracy | 0.9796 | 0.9796 | unchanged |

No new wrong-Act false positives at any stage of this work. All 6
previously-fixed regression queries (FIR, bail, burden of proof,
child-in-conflict-with-law, consumer complaint, RTI abstention) and the
out-of-domain topic guard were re-verified end to end and remain
correct.

**Note on scope:** the RRF re-tune and the topic-relevance guard (see
`docs/PROJECT_STATE.md`) both change different things -- the guard
changes only pre-retrieval *abstention gating*, never ranking, so it
doesn't affect the recall/MRR/nDCG/top-1 numbers above at all; the RRF
re-tune changes only *ranking* for non-abstain queries and doesn't
touch abstention behavior. They were verified independently and don't
interact.

## Embedding fine-tuning: not yet justified

Phase 5 of this session's work asked whether the remaining retrieval
failures justify building a larger citizen-language dataset and
fine-tuning the dense embedding model. Answer: not yet, on the current
evidence. Only 2 of 45 non-abstain eval queries (q17, q46) fail for a
genuine embedding-model reason after this session's fixes (down from a
pre-session baseline that already had exactly these two as the sole
unresolved cluster) -- a 49-query hand-curated set is not statistically
robust enough to justify the cost of fine-tuning (data collection,
training infrastructure, ongoing re-evaluation, and losing the
"off-the-shelf, well-understood model" simplicity `all-MiniLM-L6-v2`
currently offers) on the strength of 2 known failures.

**Trigger condition to revisit:** if the eval set grows to roughly
150-300+ hand-verified queries (matching the corpus's continued growth)
and a *consistent* pattern of embedding-driven misses emerges --
several queries per session, not 1-2 isolated cases -- fine-tuning
becomes worth evaluating. If that trigger is met, the training-data
shape that would make sense for this project:

- **Contrastive pairs**, not classification labels: (citizen-phrased
  query, correct chunk text) positive pairs, ideally with 1-3 hard
  negatives per query (a topically-adjacent but wrong chunk, the same
  shape of confusion this project's false-answer cases already show --
  e.g. BNSS s.39 for a "bail" query).
- **Source**: `eval/queries.jsonl` extended well past its current 49
  entries, using the same hand-verification discipline (a human checks
  `relevant_chunk_ids` against the real chunk text, never guessed) --
  not synthetically generated, to avoid training on the same kind of
  unverified paraphrase risk this project's anti-fabrication stance
  rejects everywhere else.
- **Rough size**: a few hundred to low thousands of pairs is the
  typical range for fine-tuning a small sentence-transformer via
  contrastive/triplet loss on a domain-specific corpus this size (~1,800
  chunks); exact count should be set by how many genuine failure
  patterns exist once the eval set is large enough to characterize
  them, not picked in advance.
- **Evaluation discipline**: any fine-tuned model must be evaluated the
  same way hybrid was evaluated against BM25 (this document's own
  methodology) before replacing `all-MiniLM-L6-v2` -- real
  before/after numbers on the labeled eval set, not an assumption that
  domain-tuning helps.

No training was started this session, per explicit instruction.

## Citizen-language evaluation: a much larger, real gap found

Every evaluation above used `eval/queries.jsonl` (49 queries), which is
dominated by direct-lexical and lightly-paraphrased queries -- on that
set hybrid looked strong (recall@5 0.8370) with only two known
embedding-limited failures (q17, q46). This session built a second,
larger evaluation set specifically to test whether that strength holds
up against how citizens actually type -- `eval/queries_human.jsonl`,
129 hand-verified queries (every `relevant_chunk_ids` checked against
real chunk text via `get_section()`, none fabricated) spread across
ten categories (direct terminology, ordinary citizen language,
paraphrase, colloquial, misspelling, abbreviation, vague-but-answerable,
multi-source, ambiguous, hard-negative, out-of-domain) and all 9
ingested sources. `eval/run_eval.py` now takes a `--queries` flag
(default unchanged) so either set can be run without duplicating the
harness; `eval/diagnose.py` is a new read-only script for dumping a
query's full (uncapped) BM25/dense/hybrid rank of its target chunk(s),
used throughout this investigation instead of guessing from rankings
truncated to top-5.

**Result: recall@5 dropped to 0.5551 (from 0.8370) and abstention
accuracy dropped to 0.7674 (from 0.9796)** on the citizen-language set,
before any fix. Broken down by category (`recall@5`):

| Category | n | recall@5 |
| --- | --- | --- |
| hard_negative | 13 | 0.923 |
| direct_lexical | 15 | 0.933 |
| abbreviation | 10 | 0.600 |
| paraphrase | 15 | 0.600 |
| ambiguous | 2 | 0.500 |
| ordinary_citizen | 20 | 0.450 |
| multi_source | 8 | 0.438 |
| misspelling | 10 | 0.400 |
| vague_answerable | 10 | 0.300 |
| colloquial | 15 | 0.267 |

This is the real finding: direct terminology and even deliberately
close lexical decoys (`hard_negative`) are handled well -- hybrid isn't
confused by near-miss sections. The failure is concentrated in
categories that describe a *scenario* rather than name a *legal
concept* ("my landlord's goons broke my door down" vs "house-trespass
and house-breaking"). The original 49-query set's `paraphrase` category
undersold this because its paraphrases were already fairly close to
statutory register; ordinary citizen storytelling is a substantially
harder case the smaller set never exercised at scale.

### Root-cause split (per-query full-rank diagnosis)

For every citizen-language query hybrid missed at top-5, `eval/
diagnose.py` was used to get each target chunk's *uncapped* BM25 rank
and dense rank (not just "in/out of top-5"), split into three groups:

1. **Confidence-gate-only failures (10 of 30 original false-abstains):**
   `search()` finds the target in its own top-5, but `handle_
   legal_query()`'s hybrid confidence gate (`dense_score >= 0.42`)
   still rejects it -- the citizen phrasing produces a genuinely lower
   dense score than the paraphrase-heavy queries the threshold was
   tuned against, even when the retrieved chunk is correct. A further
   check found 3 of these 30 are not gate failures at all but the
   Risk/UPL safety layer correctly redirecting "what can I get/do if
   ..." personal-outcome-shaped phrasing (`risk_personalized_advice`)
   -- expected, correct behavior, not a retrieval defect, and a design
   note for future eval-set authors: phrasing a scenario as "what can I
   do" risks exercising the safety layer instead of retrieval.
2. **BM25-vocabulary-dominant failures (~9 of 20 pure retrieval misses):**
   dense rank is moderate (6-56, near or inside the top-50 fusion pool)
   but BM25 rank is in the hundreds to low-thousands (near-zero lexical
   overlap), so the candidate is either outside the pool or too weakly
   scored by BM25's 1x weight to reach top-5 even with dense's help.
3. **Dense-embedding-dominant failures (~4 of 20):** BM25 rank is
   excellent (as good as rank 1) but dense rank is catastrophic
   (hundreds to 965), and because dense is weighted 3x in fusion, a
   dense failure this severe crushes the fused score even when BM25
   alone would have ranked the chunk first. This is a structural
   consequence of a dense-weighted fusion formula: it assumes dense is
   usually the stronger signal, which is false specifically on the
   subset of citizen phrasing dense handles worst.

A real bug was found and fixed while classifying these: `app/
retrieval/query_expand.py`'s `_WORD_BOUNDARY` regex for FIR/NCR
compiled case-sensitively (`\bFIR\b`, no `re.IGNORECASE`), so a citizen
typing "fir" or "fil fir" in lowercase -- which is how almost everyone
actually types it -- never triggered the expansion at all. Fixed with
`re.IGNORECASE`.

### Query expansion: evaluated as insufficient for this gap, two more narrow entries added anyway

Two more `_CONCEPT_PHRASES` entries were added, each verified the same
way as the existing "police question" entry (confirmed unranked
before, confirmed the append fixes it, scanned both eval sets for
false-fire risk before adding):

- `afford` + `lawyer`/`advocate` (either order) -> "legal aid legal
  services entitlement" -- moves `lsa:13` from unranked to rank 2.
- `refund` / `money back` -> "consumer complaint" -- moves `cpa2019:35`
  into the top-5 for both queries that use this phrasing.

One eval-set correction was made alongside this: `h058`'s original
target (`cpa2019:84`, manufacturer liability) was a real but less
directly actionable legal basis for "shop won't give my money back";
corrected to `cpa2019:35` (the complaint-filing procedure), the more
defensible single ground truth, matching `h022`'s target reasoning for
the same scenario type.

**Effect (hybrid, citizen-language set, 118 non-abstain queries):**
recall@5 0.5551 -> 0.5805, abstention accuracy 0.7674 -> 0.7907. Real,
but small relative to the size of the gap. Re-verified the original
49-query set is byte-identical after these changes (0.8370 recall@5
unchanged) -- both expansion entries and the case-fix are additive and
scoped, not general changes. 66/66 Python tests still pass.

**Conclusion: query expansion is evaluated as insufficient to close
this gap.** Two clean, generalizable, recurring-pattern fixes were
found and added; the other ~20 retrieval misses are each a distinct,
idiosyncratic scenario-to-statute mapping (kidnapping-for-ransom vs
plain kidnapping, "roughed me up while taking stuff" vs robbery,
"barge into my house without any paper" vs search-warrant provisions,
etc.) -- adding a curated phrase for each would mean dozens of
one-off entries, which is exactly the general-synonym-dictionary
anti-pattern this project has deliberately avoided throughout. This is
not a vocabulary-list problem; it's a representation problem.

### RRF weight retuning: tried, not a clean win, not applied

Before concluding this needs embedding-level work, the RRF dense
weight was swept against the citizen-language set (same k=5, weight in
`{1, 1.5, 2, 2.5, 3}`) to rule out a fusion-hyperparameter explanation:

| dense weight | citizen recall@5 | original-set recall@5 |
| --- | --- | --- |
| 1.0 | 0.5424 | 0.7926 |
| 1.5 | 0.5890 | 0.8148 |
| 2.0 | 0.5932 | 0.8148 |
| 2.5 | 0.5847 | 0.8148 |
| 3.0 (current) | 0.5805 | 0.8370 |

No weight in this grid improves both sets at once -- weight 2.0 is
marginally better for citizen-language (+0.013) but measurably worse
for the original set (-0.022), unlike every previous re-tune in this
document, which was a clean win on every metric. This is real evidence
the gap is not a fusion-weighting problem: the underlying dense
*signal* is what's wrong for this query population, not how much it's
weighted. `DEFAULT_DENSE_WEIGHT` is left at 3.0 -- not changed on a
mixed trade-off.

### A generalizable embedding artifact: boilerplate "short title" sections

While diagnosing `h046`-equivalent multi-source failures (a case
carried over from the original set's q46), a specific, reproducible
embedding weakness was found: a source's own `:1` chunk ("Short title,
extent and commencement" -- pure administrative boilerplate, no
substantive legal content) scores anomalously high in dense similarity
for *any* query broadly about that Act's subject, apparently because
the chunk's text literally contains the Act's full name (e.g. `pwdva:1`
contains the string "Protection of Women from Domestic Violence Act,
2005"), which lexically/semantically resembles a topical query about
that subject. Confirmed not PWDVA-specific -- checked across four other
sources against a generic topical query for each:

| chunk | dense rank | query |
| --- | --- | --- |
| `cpa2019:1` | 5 / 1801 | "what protections do consumers have" |
| `jj2015:1` | 27 / 1801 | "what happens when a child breaks the law" |
| `lsa:1` | 88 / 1801 | "how can I get free legal aid" |
| `it_act:1` | 615 / 1801 | "punishment for cyber terrorism" |

`cpa2019:1` and `jj2015:1` are inside or near the 50-candidate fusion
pool despite carrying zero substantive answer content -- a real,
corpus-wide dense-embedding false-positive pattern, not an isolated
PWDVA quirk. This is a concrete, reusable hard-negative pattern for any
future fine-tuning (see below): every source's own `:1` short-title
chunk should be paired as a hard negative against topical queries about
that Act.

### Embedding fine-tuning: now better justified, still not started

This session's evidence is materially stronger than the prior
"2 isolated failures" baseline that kept fine-tuning deferred:
~20-27 genuine citizen-language retrieval/confidence-gate failures
across 118 non-abstain queries (not 2), a clear category-level pattern
(scenario-description language specifically, not paraphrase broadly),
query expansion demonstrated insufficient for most of it, RRF retuning
demonstrated not a clean fix, and a reproducible, generalizable
embedding artifact (boilerplate short-title false positives) found
independent of any single query. This plausibly meets the trigger
condition recorded in this document's prior "Embedding fine-tuning: not
yet justified" section ("a *consistent* pattern of embedding-driven
misses ... several queries per session, not 1-2 isolated cases").

**No training was started or approved this session, per explicit
instruction.** If the user approves proceeding, the recommended design:

- **Objective:** `sentence_transformers.losses.MultipleNegativesRankingLoss`,
  fine-tuning the existing `all-MiniLM-L6-v2` checkpoint (never training
  from scratch). This loss takes `(anchor, positive, hard_negative)`
  triplets, uses the explicit hard negative *and* every other positive
  in the batch as an in-batch negative, and is the standard
  Sentence-Transformers recipe for retrieval fine-tuning with a small
  labeled set -- the right fit here given this project's total labeled
  pairs (178 across both eval sets) is small relative to a
  from-scratch-training corpus.
- **Positive pairs:** every `(query, relevant_chunk_id)` pair from both
  `eval/queries.jsonl` (49) and `eval/queries_human.jsonl` (129) --
  178 total, all hand-verified against real chunk text, none
  synthetically generated (this project's anti-fabrication discipline
  applies to training data exactly as it applies to citations).
  Multi-source queries contribute one pair per relevant chunk.
- **Hard negatives**, one to three per anchor, drawn from concrete
  patterns this session's diagnosis actually surfaced (not invented):
  - **Same-Act, wrong-section decoys** confirmed this session:
    `bsa:121` vs `bsa:122` (estoppel/estoppel-of-tenant), `bns:116` vs
    `bns:117` (hurt cluster), `bnss:173` vs `bnss:174`
    (cognizable/non-cognizable), `bns:97`/`bns:137`/`bns:140`
    (kidnapping cluster), `cpa2019:34`/`47`/`58` (District/State/
    National Commission), `it_act:66C` vs `66D` (identity theft vs
    cheating by personation), `jj2015:4` vs `jj2015:19` (Board vs
    Children's Court).
  - **The boilerplate short-title pattern** found this session: every
    source's own `:1` chunk as a hard negative against every positive
    pair belonging to that same source -- a systematic, corpus-wide
    pattern (confirmed across `pwdva`, `cpa2019`, `jj2015`, `lsa`,
    `it_act`), not a one-off.
  - **Semantically-similar-but-legally-wrong** decoys, e.g. the actual
    top dense hits `q17` returned in this session's diagnosis
    (`it_act:84C`, `cpa2019:72`, `bns:250` -- all generic "punishment
    for X offence" sections the model confused with the specific
    ex-post-facto concept it was asked about).
- **Evaluation discipline (unchanged from this document's standing
  rule):** any fine-tuned checkpoint must be evaluated against both
  eval sets the same way hybrid was evaluated against BM25 -- real
  before/after numbers, including a check that it doesn't regress the
  49-query set's near-perfect direct-lexical/hard-negative performance
  while chasing citizen-language recall -- before it replaces
  `all-MiniLM-L6-v2` anywhere.
- **Scale note:** 178 anchors is on the small side for this loss (typical
  ranges start in the low thousands); growing `queries_human.jsonl`
  toward the previously-documented 150-300+ trigger range (this session
  deliberately stopped at 129 per the "don't spend the whole session
  generating 300-500" instruction, once the initial set was clearly
  enough to answer the human-language-bottleneck question) before
  training would likely improve the fine-tune's own quality, not just
  the evaluation's statistical confidence.

## Embedding fine-tuning experiment (run1): not promoted

Following the citizen-language evaluation above, a first embedding
fine-tuning experiment was run to test whether legal-domain fine-tuning
of `all-MiniLM-L6-v2` could close the citizen-language recall gap.
**Result: not promoted.** The full write-up, including a methodology
correction discovered mid-evaluation, follows.

### Training data (`services/ai/finetune/build_dataset.py`)

Every `(query, positive_chunk_id)` pair was drawn directly from the two
hand-verified eval sets (`eval/queries.jsonl`, `eval/queries_human.jsonl`)
-- 180 pairs across 153 query groups (multi-source queries contribute
one pair per relevant chunk; near-duplicate queries across the two sets,
e.g. `q23`/`h076`'s identical "how do I file an FIR", and six
deliberately-kept same-concept pairs like `q17`/`h040`, are merged into
one group by exact-text match plus a small hand-verified cross-reference
list, so they can never span more than one split).

Hard negatives were mined from the **existing production retrieval
index**, not chosen at random, per four strategies:

| neg_type | count | source |
| --- | --- | --- |
| `same_act_nearby` | 360 | a different chunk from the same source, within 6 positions of the positive in document order (same chapter/cluster) |
| `bm25_strong_wrong` | 346 | in the query's live top-10 BM25 results, not a relevant chunk |
| `dense_strong_wrong` | 272 | in the query's live top-10 dense results (current production model), not a relevant chunk |
| `boilerplate` | 177 | the source's own unit `:1` ("Short title...") chunk -- the generalizable false-positive pattern found during citizen-language evaluation |

1155 total triplets, split by query group (not by row, to prevent
leakage) 70/15/15 -> **train 801 / val 183 / test 171**, with an
assertion in `build_dataset.py` that no query group appears in more
than one split. Reproduce with `python finetune/build_dataset.py`
(seeded, deterministic).

### Training (`services/ai/finetune/train.py`)

- **Base model:** `sentence-transformers/all-MiniLM-L6-v2` (the current
  production model) -- continued training, never trained from scratch.
- **Loss:** `MultipleNegativesRankingLoss` (standard Sentence-Transformers
  query->passage retrieval objective), using each triplet's explicit
  hard negative plus in-batch negatives from the rest of the batch.
- **Chunk text format:** `"{title}. {text}"`, identical to
  `index_build.py`'s `_index_text()` -- the fine-tune is trained on
  exactly what it will be searched against, never a different
  representation.
- **Config (run1):** batch size 16, 4 epochs, lr 2e-5, warmup ratio 0.1,
  seed 42, evaluated every 50 steps against the val split via
  `TripletEvaluator`, best checkpoint kept. Uses sentence-transformers'
  legacy `.fit()` API (still requires `datasets`/`accelerate` in this
  version, added in `requirements-finetune.txt`, not a production
  dependency).
- **Duration:** 1359.7s (~22.7 min) on CPU (no GPU available in this
  environment), 12 cores, ~204 total optimizer steps.
- **Val triplet accuracy:** 0.7705 (pre-training) -> 0.8743 (best
  checkpoint, reached by epoch 2, held through epoch 4).
- **Held-out test triplet accuracy** (`test.jsonl`, never touched during
  training or checkpoint selection): 0.7251 -> 0.7895 -- a genuine,
  uncontaminated generalization signal on the narrow triplet-ranking
  task (positive vs. one specific hard negative).

### A methodology correction found mid-evaluation: train/val contamination

The first full-eval-set comparison (`finetune/eval_candidate.py`, which
builds a temporary index with the candidate model's dense vectors
without touching production) showed spectacular numbers -- hybrid
recall@5 0.8370 -> 0.9889 on the original 49-query set, 0.5805 -> 0.8898
on the citizen 129-query set, and `q17`/`q18`/`q40`/`q46` all moving to
dense rank 1. **These numbers are not a valid measure of generalization
and are not reported as the result.** Every query in `eval/queries.jsonl`
and `eval/queries_human.jsonl` was also a training-data source (Phase 2
built the fine-tuning set directly from these two files, per
instruction) -- so any query whose `(query, positive)` pair landed in
`train` was directly optimized on that exact pair, and cross-checking
found **all six of the queries Phase 5 was specifically asked to
inspect (q17, q18, q23, q26, q40, q46) were in the training split**.
Their dramatic improvement reflects memorization of the exact text,
not evidence the model generalizes to new phrasing of the same legal
concepts. Evaluating a fine-tuned model against the same data used to
build its training set and reporting the result as "improvement" would
be exactly the kind of unsupported claim this project's evaluation
discipline exists to prevent -- so a second, corrected evaluation was
run before drawing any conclusion.

### The honest result: held-out (test-split) evaluation

`services/ai/finetune/eval_heldout.py` re-runs the same metrics
restricted to the 25 queries in the `test` split (5 from
`queries.jsonl`, 20 from `queries_human.jsonl`) -- these `(query,
positive)` pairs were never used for training or checkpoint selection.

| Set | Mode | Metric | Base | Candidate (run1) |
| --- | --- | --- | --- | --- |
| original (n=5) | hybrid | recall@5 | 0.900 | 0.900 (unchanged) |
| original (n=5) | hybrid | MRR / top1 correctness | 0.867 / 0.80 | 1.000 / 1.00 |
| citizen (n=20) | hybrid | recall@5 | 0.550 | 0.550 (**unchanged**) |
| citizen (n=20) | hybrid | MRR | 0.500 | 0.475 (slightly worse) |
| citizen (n=20) | hybrid | top1 correctness | 0.45 | 0.40 (slightly worse) |
| citizen (n=20) | hybrid | abstention accuracy | 0.65 | 0.60 (slightly worse) |

The 5-query original-set slice is too small to draw any conclusion from
(and recall@5 there didn't move regardless). The 20-query citizen slice
is the meaningful one, and recall@5 is **exactly unchanged**, with MRR,
top-1 correctness, and abstention accuracy all mildly *worse*.

A per-query hit/miss diff (`finetune/per_query_diff.py`) confirms this
isn't coincidental cancellation hiding a real shift: of the 20 held-out
citizen queries, **18 are byte-identical hit/miss outcomes between base
and candidate, one improved (`h078`), one regressed (`h027`)** -- a
wash, not a directional change in either direction.

### Diagnosis

The held-out triplet-ranking accuracy genuinely improved (0.7251 ->
0.7895) -- the model did learn *something* that generalizes to unseen
queries at the narrow task of "is the positive closer than this one
specific hard negative." That did not translate into full-corpus
retrieval improvement (ranking correctly among all 1801 chunks, a much
harder task) on queries outside the training set. The most likely
cause, given the evidence: **153 query groups (115 in the actual
training split) is too small a training set** for this fine-tune to
learn a broadly better semantic space rather than narrow adjustments
around the specific triplets it saw -- consistent with this document's
own earlier "Embedding fine-tuning: not yet justified" section, which
set exactly this expectation ("a few hundred to low thousands of pairs
is the typical range... 150-300+ [eval] queries" as the trigger point
to revisit). At 178 total labeled queries feeding the fine-tune, this
session sits at the low edge of that range, and the result is
consistent with that prediction rather than contradicting it.

A second, hypothesis-driven experiment (larger batch size, to give
`MultipleNegativesRankingLoss` more in-batch negative diversity per
step -- a standard, well-documented lever for this loss) was attempted
twice (batch size 32, then a more conservative 20) and both runs were
killed by the environment before completing, at a point in the log too
early to attribute to the batch-size change itself (this environment
has ~8GB total RAM with only ~2.7-3.3GB free at the time, and the same
early-kill pattern occurred at batch 20, barely different from run1's
working batch 16) -- an infrastructure instability, not a hyperparameter
finding. Per the standing instruction not to blindly re-run experiments
against a failing environment, this was not retried further; **run1
stands as the sole, complete, honestly-evaluated experiment.**

### Safety gate

Even had the recall numbers been favorable, the following were checked
and found clean on both the full (contaminated) and held-out
evaluations: zero wrong-Act false positives on hybrid mode in either
set (`abstention_false_answer_ids` empty throughout); the short-title
boilerplate artifact's dense rank *improved* (moved further from top)
for every probed source under the candidate model (`pwdva:1` 1 -> 177,
`cpa2019:1` 5 -> 110, `jj2015:1` 27 -> 33, `lsa:1` 88 -> 63, `it_act:1`
615 -> 826) -- a genuinely encouraging signal specifically for the
pattern this fine-tune targeted, even though it didn't move the
aggregate held-out recall number. This is recorded for a future
attempt with a larger dataset, not as grounds to promote run1.

### Decision: **not promoted**

The production embedding model (`sentence-transformers/all-MiniLM-L6-v2`,
`DENSE_EMBEDDING_MODEL` unset/default) and the production dense index
(`data/index/`) were never modified by this experiment --
`finetune/eval_candidate.py`/`eval_heldout.py` build a temporary index
in the OS temp directory and never write to `services/ai/data/index/`.
No re-sweep of `DEFAULT_DENSE_WEIGHT` was needed since nothing about
the production retrieval path changed.

**Recommended next step, if fine-tuning is revisited:** grow
`eval/queries_human.jsonl` toward the previously-documented 150-300+
range (this session deliberately capped it at 129 to first confirm
human-language retrieval was the real bottleneck, which it is) before
re-attempting fine-tuning -- the evidence here points at training-set
size as the limiting factor, not the loss function, hard-negative
strategy, or batch size. The infrastructure (`finetune/build_dataset.py`,
`finetune/train.py`, `finetune/eval_candidate.py`,
`finetune/eval_heldout.py`, `finetune/per_query_diff.py`) is reusable
as-is against a larger eval set.

## Citizen-language evaluation set expanded to 313 query groups

The prior section's citizen-language finding rested on 129 hand-verified
queries. That was enough to establish *that* human-language retrieval is
the bottleneck, but not enough to characterise *why* with any statistical
confidence -- and the fine-tuning experiment above concluded that the
labelled set's size, not the loss function or hard-negative strategy, was
the limiting factor. This session grew `eval/queries_human.jsonl` from
**129 to 313 query groups** (184 added) and re-measured. **No retrieval
code, index, embedding model, RRF weight, query-expansion entry, or
confidence threshold was changed** -- this session is measurement only.

Every added positive was verified the same way as the original 129: the
intended Act and section were identified first, the real chunk text was
read out of `data/legal-corpus/<source>/chunks.jsonl`, and the query was
only kept if it is genuinely answerable from that text. No section number
was guessed and no mapping was inferred from general legal knowledge.

### Composition

| Category | n | What it tests |
| --- | --- | --- |
| `ordinary_citizen` | 55 | Scenario description in everyday words |
| `colloquial` | 44 | Slang/informal register ("nicked", "goons", "barge in") |
| `paraphrase` | 34 | Formal-register rewording with low term overlap |
| `hard_negative` | 29 | A strong but legally wrong decoy exists |
| `vague_answerable` | 29 | Under-specified but answerable from one section |
| `direct_lexical` | 24 | Exact statutory terminology (control group) |
| `misspelling` | 22 | Real typing errors |
| `out_of_domain` | 22 | Non-legal; abstention is correct |
| `abbreviation` | 18 | FIR/NCR/BNS/IPC/CrPC/CWC/DLSA/NCDRC |
| `multi_source` | 18 | Evidence genuinely spans 2+ chunks |
| `insufficient_evidence` | 10 | **New category** (see below) |
| `ambiguous` | 8 | Several sections are all legitimately correct |

281 positive groups / 32 abstain-expected groups; 26 groups have more
than one relevant chunk; 219 distinct corpus chunks are referenced.

Source coverage (by relevant-chunk reference, all 9 ingested Acts):
`bns` 76, `bnss` 74, `constitution` 28, `bsa` 27, `jj2015` 27,
`cpa2019` 26, `it_act` 22, `pwdva` 21, `lsa` 12.

**`insufficient_evidence` is the one new category, and it was added for a
specific reason**: `out_of_domain` only ever contained *non-legal*
queries (biryani, cricket scores, PAN cards), which the deterministic
topic-relevance guard catches by phrase pattern before retrieval even
runs. That left an entire class untested -- a question that is
unmistakably a legal question, in this system's own subject area, about
an Act that simply is not in the corpus (divorce, POCSO, Motor Vehicles,
rent control, minimum wages, stamp duty, SC/ST Atrocities, arbitration,
labour notice periods, RTI). Abstaining is the only correct answer there,
and nothing in the existing eval set measured it. It turned out to be the
single most informative addition (see "Abstention" below).

Duplicate/near-duplicate control: exact-duplicate detection over
whitespace/punctuation-normalised query text, plus a `difflib` ratio scan
at a 0.85 threshold across all 313 queries. One flagged pair from this
session's draft (a misspelled respelling of an existing query, carrying no
independent information) was replaced with a different concept before the
evaluation was run. The one remaining flagged pair (`h066` "how to fil
fir" / `h076` "how to file an FIR") is the pre-existing deliberate
misspelling-vs-abbreviation pair and is kept.

### Results (top_k=5, 281 non-abstain groups, one full run)

| Metric | BM25 | Dense | Hybrid |
| --- | --- | --- | --- |
| Recall@5 | 0.3855 | 0.6115 | **0.6246** |
| Precision@5 | 0.0861 | 0.1359 | **0.1381** |
| MRR | 0.2972 | 0.4723 | **0.4874** |
| nDCG@5 | 0.3137 | 0.5027 | **0.5160** |
| Top-1 citation correctness | 0.2321 | 0.3737 | **0.3879** |
| Abstention accuracy (all 313) | 0.9201 | 0.7188 | 0.7572 |
| Wrong-Act top-1 rate | 0.359 | 0.181 | **0.196** |

Hybrid still beats both single methods on every retrieval-quality metric,
as it does on both smaller sets -- the architecture conclusion this
document was originally written to justify holds at 6.4x the original
evaluation size. BM25's high abstention accuracy is the same artefact
this document has flagged since the beginning and is *not* a point in its
favour: BM25 answered **all 21** of the abstain-expected queries it saw as
false positives and simply almost never false-abstains, so the ratio
flatters it. Its wrong-Act top-1 rate (0.359, nearly double hybrid's) is
the honest read of the same behaviour.

### Do not compare these percentages to the earlier ones directly

Recall@5 on this set (0.6246) is *higher* than on the 129-query set
(0.5805), and that is a composition effect, not an improvement. Nothing
in the retrieval path changed. Scoring the original `h001`-`h129` rows in
isolation out of this same run reproduces the earlier numbers exactly:

| Slice | n | Recall@5 | Precision@5 | MRR | nDCG@5 | Top-1 |
| --- | --- | --- | --- | --- | --- | --- |
| Original `h001`-`h129` | 118 | 0.5805 | 0.1237 | 0.4273 | 0.4604 | 0.3136 |
| Added `h130`-`h313` | 163 | 0.6564 | 0.1485 | 0.5310 | 0.5563 | 0.4417 |
| Combined | 281 | 0.6246 | 0.1381 | 0.4874 | 0.5160 | 0.3879 |

0.5805 is byte-identical to the previously recorded figure, which is the
control that proves the pipeline is unchanged. The added rows score
higher mainly because they deliberately rebalanced the set toward
under-tested Acts and toward control categories (`direct_lexical`,
`hard_negative`) that the original 129 under-weighted. The 49-query
`eval/queries.jsonl` set was also re-run unchanged as a second control:
hybrid recall@5 0.8370 / precision@5 0.1822 / MRR 0.7096 / nDCG@5 0.7227 /
top-1 0.6222 / abstention 0.9796 -- every figure identical to the
previously documented values.

### The category split is the real result, and it is now stable

Hybrid, recall@5 by category:

| Category | n | Recall@5 | Top-1 |
| --- | --- | --- | --- |
| `hard_negative` | 29 | 0.966 | 0.655 |
| `direct_lexical` | 24 | 0.958 | 0.833 |
| `abbreviation` | 18 | 0.722 | 0.333 |
| `ordinary_citizen` | 55 | 0.600 | 0.273 |
| `ambiguous` | 8 | 0.562 | 0.375 |
| `paraphrase` | 34 | 0.559 | 0.353 |
| `misspelling` | 22 | 0.500 | 0.364 |
| `multi_source` | 18 | 0.500 | 0.389 |
| `vague_answerable` | 29 | 0.483 | 0.345 |
| `colloquial` | 44 | 0.477 | 0.205 |

Collapsed: **citizen-language categories** (`ordinary_citizen`,
`colloquial`, `vague_answerable`, `misspelling`, n=150) score recall@5
**0.527**; **legal-terminology categories** (`direct_lexical`,
`abbreviation`, `paraphrase`, n=76) score **0.724**; `hard_negative`
scores **0.966**. The 0.20 gap between how a citizen types and how a
statute is written is the finding, and at n=150 vs n=76 it is no longer a
small-sample impression.

Two things the larger set changed relative to the 129-query read:

- **`ordinary_citizen` is much less bad than it looked** (0.450 -> 0.600).
  The earlier 20-query sample happened to over-represent hard scenarios.
- **`hard_negative` got *better*, not worse, as it grew** (0.923 -> 0.966
  across 13 -> 29 queries), including 7 newly added Act-name/short-title
  probes and a deliberate inverse pair (`h108` "freedom of speech and
  expression" -> Article 19 with Article 105 as decoy; `h306` "freedom of
  speech inside parliament" -> Article 105 with Article 19 as decoy).
  **Both directions resolve correctly**, which is a genuinely strong
  result and rules out "the retriever is just confused between adjacent
  sections" as an explanation for anything else here.

Per-Act (single-source groups, hybrid recall@5): `lsa` 0.900,
`constitution` 0.714, `it_act` 0.688, `bns` 0.648, `jj2015` 0.619,
`bnss` 0.617, `pwdva` 0.562, `cpa2019` 0.550, `bsa` 0.520. No Act is
catastrophically worse than the others; this is not a corpus-quality
problem localised to one source.

### Root-cause split (per missed target chunk, uncapped ranks)

For all 119 relevant chunks hybrid missed at top-5, the target's
*uncapped* BM25 and dense rank were dumped and bucketed by which stage
actually failed (`_FUSION_CANDIDATE_POOL` is 50, so "in pool" means
rank <= 50):

| Bucket | n | % | Meaning |
| --- | --- | --- | --- |
| `bm25_vocabulary` | 39 | 32.8% | Dense found it (rank <= 50), BM25 nowhere -- so it carries only one list's fusion contribution and lands below 5 |
| `fusion_ranking` | 36 | 30.3% | **Both** methods had it in their top-50, fusion still ranked it below 5 |
| `representation_gap` | 29 | 24.4% | Neither method's top-50 contains it at all |
| `dense_embedding` | 15 | 12.6% | BM25 found it, dense rank catastrophic -- and dense is weighted 3x, so it crushes the fused score |

By category, the buckets separate cleanly: `representation_gap` is
dominated by `colloquial` (10) and `ordinary_citizen` (6);
`bm25_vocabulary` by `ordinary_citizen` (11) and `vague_answerable` (8);
`fusion_ranking` by `multi_source` (9), `paraphrase` (5),
`vague_answerable` (5) and `ambiguous` (4).

**The `fusion_ranking` bucket is new information and it changes a
standing decision.** This document has twice deferred reranking on the
explicit grounds that the misses were *not* "correct chunk present but
mis-ordered in an otherwise-good candidate list" -- at 49 and at 129
queries that was true and was verified each time. At 313 queries it is no
longer true: 36 missed chunks are exactly that shape, and they cluster in
`multi_source`/`ambiguous`/`paraphrase`, precisely the queries where more
than one section is defensible and ordering is the whole problem. That is
a reranker-shaped failure mode, and it is the largest single actionable
bucket after BM25 vocabulary. It is **not** implemented this session
(measurement only), but the evidence that previously blocked it no longer
holds.

### Abstention: the informative failure

| Mode | Accuracy (313) | False answers (should abstain) | False abstains (should answer) |
| --- | --- | --- | --- |
| bm25 | 0.9201 | 21 (11 OOD + 10 insufficient_evidence) | 4 |
| dense | 0.7188 | 5 | 83 |
| hybrid | 0.7572 | 7 | 69 |

Hybrid's 7 false answers are the headline: **2 of 22 `out_of_domain`
(0.909 correct) but 5 of 10 `insufficient_evidence` (0.500 correct)**.
The deterministic topic-relevance guard plus the dense-score floor handle
non-legal queries well. They do not handle *legal* queries about
un-ingested Acts at all, because such a query shares genuine legal
vocabulary with genuine legal content and lands in the same score band as
a real match. The concrete cases:

| Query | Answered with | Why it is wrong |
| --- | --- | --- |
| "what is the penalty for drunk driving" | `bns:355` | Misconduct in public by a drunken person -- not a driving offence; the Motor Vehicles Act is not ingested |
| "how do I get a divorce in india" | `bnss:219` | Prosecution for offences against marriage -- not matrimonial law |
| "what does the law against caste-based atrocities cover" | `constitution:16` | Equality of opportunity -- not the SC/ST Atrocities Act |
| "what is the punishment under the POCSO act" | `bns:198` | Public servant disobeying law -- POCSO is only *cited by name* in the corpus, never reproduced |
| "how do I file an application for information from a government office" | `it_act:6` | Electronic records in Government -- the RTI Act is the known un-ingested source |
| "what are the court fees for filing a civil suit" | `bnss:400` | Costs in non-cognizable cases -- not the Court Fees Act |
| "who won the last general election in india" | `constitution:58` | Qualifications for President -- shares election vocabulary only |

This is the same failure mode as the original out-of-domain gap the
topic-relevance guard was built for, one level harder: the guard works by
recognising *subjects it knows are outside scope*, and "family law",
"motor vehicles", "POCSO" are outside scope in exactly the same way that
"income tax" is. Extending the curated pattern set to name the Acts the
corpus does **not** contain is the obvious, in-keeping next step, and it
is the same narrow-curated-list discipline this project already applies
in `query_expand.py`, `topic_relevance.py`, and `_KNOWN_ARTICLE_TITLES`.
It was not done this session (measurement only).

Hybrid's 69 false abstains are almost entirely `ordinary_citizen` (33)
and `colloquial` (24) -- the confidence gate rejecting a *correct* top hit
because citizen phrasing produces a lower dense score than the phrasing
the 0.42 floor was tuned against. This reproduces the 129-query finding at
5x the sample size and confirms it was not a small-sample artefact.

### q17 / q46 and the short-title artefact, re-measured

Both tracked failures remain present and remain measurable:

- **q17 equivalent (`h040`, "is retroactive criminalization permitted
  under the constitution" -> `constitution:20`)**: bm25 rank 1180/1766,
  dense rank 63/1801, not in the fusion pool. Total miss; the five chunks
  returned instead are all generic sentencing/remission sections. The
  original phrasing (`q17`) is worse still: dense rank 113. Unchanged
  diagnosis -- a representation gap, and one a reranker cannot touch.
- **q46 equivalent (`h098`)**: `pwdva:3` now ranks 4 (a hit);
  `constitution:15` is still missed at bm25 63 / dense 68, outside the
  50-candidate pool. Partial recall only.
- **The short-title boilerplate artefact reproduces, and `h098` shows it
  at rank 1**: the top result for "equality and protection for women
  facing violence at home" is `pwdva:1` ("Short title, extent and
  commencement"), a chunk with no substantive content, ahead of the
  actual definition section.

Re-probed across all 9 sources with a fresh set of topical queries:

| Boilerplate chunk | dense rank | bm25 rank | probe query |
| --- | --- | --- | --- |
| `pwdva:1` | 3 | 157 | "which law protects a woman from violence by her own family" |
| `cpa2019:1` | 5 | (unranked) | "what protections do consumers have" |
| `bns:1` | 10 | 37 | "bharatiya nyaya sanhita list of punishments" |
| `jj2015:1` | 27 | 1344 | "what happens when a child breaks the law" |
| `lsa:1` | 88 | 112 | "how can I get free legal aid" |
| `bnss:1` | 309 | **4** | "bharatiya nagarik suraksha sanhita rules about taking bail" |
| `bsa:1` | 579 | 1102 | "what counts as evidence in a court case" |
| `it_act:1` | 615 | 1176 | "punishment for cyber terrorism" |
| `constitution:1` | 921 | (unranked) | "what basic rights are guaranteed to every citizen" |

Two things are new here. First, the artefact fires hardest when the query
*names the Act* -- which is ordinary citizen behaviour, not an artificial
probe (`bns:1` at dense rank 10). Second, **it is not dense-only**:
`bnss:1` sits at BM25 rank 4 for a query naming the Sanhita, because the
short-title chunk is the one place in 531 sections where the Act's full
name literally appears. Previous write-ups characterised this as a
dense-embedding artefact; it is more precisely an artefact of the
short-title chunk being the corpus's only carrier of the Act's own name,
and it affects both retrieval methods. Despite that, the seven dedicated
short-title probe queries added this session (`h259`-`h265`) all resolve
to their substantive target at top-5 -- the boilerplate chunk appears in
the returned window (e.g. `pwdva:1` at rank 4 for `h259`) but does not
displace the right answer.

### A separate finding: the FIR query misses on both eval sets

`h076` ("how to file an FIR") and the original set's `q23` ("how do I
file an FIR") both fail to retrieve `bnss:173` at top-5 today --
`bnss:173` sits at bm25 rank 16-18 and dense rank 20-21, while the top of
the list is taken by `bnss:177` ("Report how submitted") and `bnss:193`
("Report of police officer on completion of investigation"). The token
"report", appended by `query_expand.py`'s FIR expansion, dominates. This
is not a regression: `q23` is one of the pre-existing misses inside the
49-query set's unchanged 0.8370 recall, and the earlier "FIR regression
query re-verified" note referred to the *pipeline answering with a
relevant citation*, not to the labelled chunk's top-5 rank. An `h076`
note claiming its wording was identical to `q23`'s was corrected in the
dataset while confirming this -- the wordings differ, and the pair is now
documented as a measurement of how little phrasing change it takes to
lose the target.

### Does the larger dataset justify embedding fine-tuning?

**Partly, and less exclusively than the 129-query read suggested.**

**Stronger:** the citizen-vs-statute gap is confirmed at a sample size
where it means something (0.527 vs 0.724 recall@5 over 150 and 76
queries). 44 of 119 missed chunks (`representation_gap` 29 +
`dense_embedding` 15, 37.0%) are failures no reranker and no fusion
retune can reach -- the target is either outside both candidate pools or
so badly embedded that a 3x-weighted dense signal actively buries it.
Those are embedding-quality failures by definition. The labelled pool
available for training also roughly doubles: 313 groups here plus 49 in
`eval/queries.jsonl` is ~362 groups, materially more than the 153 the
run1 experiment concluded was too small.

**Weaker, or at least less exclusive:** the largest actionable bucket is
no longer embedding-shaped. `bm25_vocabulary` (32.8%) plus
`fusion_ranking` (30.3%) is 63% of missed chunks, and both are
candidate-generation/ordering problems. `fusion_ranking` in particular is
the exact pattern this document twice cited as *absent* when deferring
reranking, and it is now the second-largest bucket. Separately, the
single clearest correctness risk this session surfaced is not a ranking
problem at all: it is 5-of-10 confident wrong-Act answers on legal
questions about un-ingested Acts, which fine-tuning would not fix and
might worsen (a model tuned to map citizen language onto *this* corpus
more aggressively has more, not less, reason to answer a POCSO question
from the BNS).

**Recommendation, on this evidence:** fine-tuning is now adequately
supported by data volume and by a confirmed, measured failure class, but
it should not be the *next* experiment, because three cheaper changes
address larger buckets and one addresses a correctness risk rather than a
quality metric. Suggested order:

1. **Extend the topic-relevance guard to name un-ingested Acts**
   (family law, motor vehicles, POCSO, rent control, labour/wages,
   stamp duty/registration, SC/ST Atrocities, arbitration, RTI). Directly
   targets the 5 wrong-Act false answers -- a correctness risk in a
   legal-information product, not a metric. Cheapest change here, and
   squarely within the existing curated-pattern discipline.
2. **Re-evaluate the confidence gate for citizen phrasing.** 69 false
   abstains, 57 of them `ordinary_citizen`/`colloquial`, on queries whose
   correct chunk *was* retrieved. This is threshold behaviour on a query
   population the threshold was never tuned against.
3. **Add the deferred cross-encoder reranker** over the existing fused
   candidates, gated available-if-installed like dense retrieval is. The
   `fusion_ranking` bucket (36 chunks) is precisely what it fixes, and
   the stated blocking condition for adding it is now measurably met.
4. **Then** re-attempt embedding fine-tuning against the ~362-group
   labelled pool, with the run1 infrastructure unchanged, evaluated
   held-out-only as run1 finally was.

No training was started, no retrieval code was touched, and nothing was
committed this session.

## Safety guard, confidence-gate calibration, and the rejected reranker

The 313-query evaluation above ended with three candidate interventions
ranked ahead of embedding fine-tuning. This section records what
happened when all three were actually attempted. Summary: **one shipped,
one was investigated and deliberately not changed, one was implemented,
measured, and rejected.** The production retrieval architecture
(BM25 + dense + weighted RRF, dense weight 3.0, k=5, hybrid confidence
floor 0.42) is unchanged by everything below.

The committed starting point for this work is
`4f7fd54 feat(ai): expand citizen-language retrieval evaluation`.

### Baseline being measured against

313-query citizen-language set, hybrid, 281 non-abstain groups:

| Metric | Value |
| --- | --- |
| Recall@5 | 0.6246 |
| Precision@5 | 0.1381 |
| MRR | 0.4874 |
| nDCG@5 | 0.5160 |
| Top-1 citation correctness | 0.3879 |
| Abstention accuracy (all 313) | 0.7572 |
| Wrong-Act top-1 rate | 0.196 |
| False accepts (should abstain, answered) | 7 |
| False abstains (should answer, abstained) | 69 |

49-query control, hybrid: recall@5 0.8370, precision@5 0.1822, MRR
0.7096, nDCG@5 0.7227, top-1 0.6222, abstention 0.9796.

### 1. Corpus-coverage guard: shipped

`app/safety/corpus_coverage.py`, run in `handle_legal_query()` after the
topic-relevance guard and before retrieval. It closes the failure class
the `insufficient_evidence` category was invented to expose: a query
that genuinely *is* a legal question in this service's subject area but
names an Act the corpus does not contain. Such a query shares real legal
vocabulary with real legal content, so it clears the dense-score floor
and gets answered confidently from the wrong Act -- the same structural
problem `topic_relevance.py` was built for, one level harder, and
equally unfixable by moving a bounded threshold.

Six categories, one per demonstrated failure, and nothing else:

| Query | Was answered from | Now |
| --- | --- | --- |
| "what is the penalty for drunk driving" | `bns:355` (misconduct in public by a drunken person) | abstains |
| "how do I get a divorce in india" | `bnss:219` (prosecution for offences against marriage) | abstains |
| "what does the law against caste-based atrocities cover" | `constitution:16` (equality of opportunity) | abstains |
| "what is the punishment under the POCSO act" | `bns:198` (public servant disobeying law) | abstains |
| "what are the court fees for filing a civil suit" | `bnss:400` (costs in non-cognizable cases) | abstains |
| "How do I file an RTI application?" (`q35`, 49-query set) | wrong-Act answer in bm25 mode | abstains |

**Result: hybrid false accepts 7 -> 1; abstention accuracy 0.7572 ->
0.7764. bm25-mode abstention on the 49-query control 0.9796 -> 1.0000.**
Retrieval-quality metrics are untouched by construction (the guard only
changes pre-retrieval gating, never ranking), and this was verified
rather than assumed -- recall@5/precision@5/MRR/nDCG@5/top-1 are
byte-identical on both eval sets before and after.

**Every pattern was checked against real indexed corpus text before
being added**, because the obvious discriminators are unsafe:

- bare `divorce` appears in `bnss:144`/`bnss:146` (maintenance for a
  divorced woman), `bsa:44` and `jj2015:45` -- all genuinely answerable,
  so only divorce *procedure* phrasings match.
- bare `drunk` is the literal subject of `bns:355`, so only
  drunk-*driving* phrasings match.
- bare `scheduled caste` appears in `constitution:15`, `constitution:16`,
  `constitution:46` and `lsa:12`, so the SC/ST entry keys off
  "atrocities" (zero occurrences anywhere in the corpus) and the Act's
  own name.
- bare `court fee` appears in `lsa:21` (court-fee refund on a Lok Adalat
  award), a real answerable question, so only filing-cost phrasings
  match.

Over-blocking is the failure mode that would matter most here, so it is
asserted, not spot-checked: `test_guard_never_fires_on_a_query_that_
expects_an_answer` scans all 362 labelled queries across both eval sets
and fails on a single fire against an `expect_abstain=False` row.
Measured: **zero false fires**, plus zero fires across twelve
hand-built adversarial near-miss probes drawn from the bullet list
above. 8 tests in `tests/test_corpus_coverage.py`.

One `topic_relevance.py` addition came from the same evaluation: "who
won the last general election in india" (`h279`) was answered from
`constitution:58` (qualifications for President) on shared election
vocabulary alone. Two patterns (`election results?`, `who won ...
election`) were added to the existing `everyday_nonlegal` category.
Bare "election" is deliberately not matched -- BNS ss.169-177 (election
offences) and Constitution Part XV are genuinely ingested; all five
genuine election-offence phrasings were verified to still pass through.

**Residual, documented rather than papered over:** `h286` ("how do I
file an application for information from a government office") still
answers from `it_act:6`. It is the RTI question deliberately phrased
without naming RTI, and a phrase-pattern guard cannot reach a query that
names nothing. Closing it would need a semantic classifier, which is out
of scope by standing decision. It is the sole remaining false accept in
hybrid mode.

**Scope discipline:** five other un-ingested subjects in the same eval
category (rent control, minimum wages, stamp duty, arbitration, labour
notice periods) are deliberately *absent* from the pattern list, because
the confidence gate already abstains correctly on them. Adding them
would be speculative rather than evidence-driven. Same "extend only when
evaluation names a specific gap" rule as `query_expand.py`'s
abbreviation dict and `chunk.py`'s `_KNOWN_ARTICLE_TITLES`.

### 2. Confidence gate: investigated, deliberately not changed

The 313-query evaluation's 69 false abstains -- 57 of them
`ordinary_citizen`/`colloquial`, on queries whose correct chunk *was*
retrieved into the top-5 -- looked like a straightforward calibration
problem. It is not. Measuring the gate signal (hybrid = top hit's
`dense_score`) across all 362 labelled queries, grouped by what the gate
*should* do:

| Group | n | min | p25 | median | p75 | max |
| --- | --- | --- | --- | --- | --- | --- |
| should answer | 220 | 0.181 | 0.482 | 0.599 | 0.693 | 0.889 |
| should answer (citizen-language only) | 78 | 0.181 | 0.390 | 0.456 | 0.537 | 0.760 |
| should answer (legal-terminology only) | 81 | 0.394 | 0.559 | 0.648 | 0.728 | 0.889 |
| answered from wrong Act | 42 | 0.167 | 0.369 | 0.442 | 0.537 | 0.682 |
| should abstain (post-guard) | 15 | 0.127 | 0.181 | 0.264 | 0.352 | 0.429 |

The signal *is* miscalibrated for citizen language -- median 0.456
against 0.648 for legal terminology, so the 0.42 floor sits above the
25th percentile of citizen queries that deserve an answer. But the
citizen-language true-positive distribution sits almost exactly on top
of the wrong-Act distribution (median 0.456 vs 0.442). **There is no
threshold that separates them.** Sweeping the floor:

| threshold | citizen TPs kept | wrong-Act admitted | TP per wrong-Act |
| --- | --- | --- | --- |
| 0.30 | 72 | 36 | 2.00 |
| 0.34 | 68 | 34 | 2.00 |
| 0.36 | 65 | 32 | 2.03 |
| 0.38 | 59 | 31 | 1.90 |
| 0.40 | 55 | 26 | 2.12 |
| **0.42 (current)** | **48** | **23** | **2.09** |
| 0.44 | 42 | 21 | 2.00 |
| 0.46 | 36 | 20 | 1.80 |

The ratio is **flat at ~2.0 across the entire range**. Moving the
threshold does not find a better operating point; it slides along a line
of constant trade-off. Every genuine citizen answer recovered costs
roughly half a wrong-Act answer, at every setting.

A second hypothesis was tested before concluding: perhaps the problem is
*what* the gate reads, not the number. The product shows every retrieved
excerpt, so "is there confident evidence anywhere in the returned
window" is arguably the better question than "is rank 1 confident". Two
alternative signals were measured -- `max` and `mean` of `dense_score`
over the returned top-5. At the zero-false-accept operating point all
three are within noise of each other (top-1 @0.44: 177 answered / 43
false abstains / 21 wrong-Act; max-of-5 @0.45: 176 / 44 / 21; mean-of-5
@0.40: 171 / 49 / 22). **No signal re-parameterisation helps.**

One candidate was genuinely tempting: 0.43 removes the last false accept
(`h286` sits at 0.4292) and two wrong-Act answers, costing five genuine
answers. It was **not** applied. Moving a global threshold to catch a
single labelled query is overfitting to the eval set, and `h286` is
already understood as a guard-shaped problem, not a threshold-shaped
one. `DEFAULT_MIN_SCORE_BY_MODE["hybrid"]` stays at 0.42.

This is a negative result, and it is the useful kind: it rules out the
cheapest remaining intervention on measurement rather than on taste, and
it says the citizen-language gap is a *representation* problem showing
up in the gate, not a gate problem.

### 3. Cross-encoder reranking: implemented, measured, rejected

Earlier revisions of this document deferred reranking twice on the
grounds that the misses were not reranking-shaped. The 313-query
root-cause split overturned that premise -- 36 of 119 missed chunks
(30.3%) sat inside *both* methods' top-50 pools while fusion still
ranked them below 5. So the reranker was built and measured rather than
deferred a third time.

**Reachability ceiling, measured before implementing anything** (130
relevant chunks hybrid misses at top-5, both eval sets):

| candidate pool | reachable | share of misses |
| --- | --- | --- |
| 25 | 84 | 64.6% |
| **50 (current `_FUSION_CANDIDATE_POOL`)** | **100** | **76.9%** |
| 75 | 111 | 85.4% |
| 100 | 113 | 86.9% |

Pool 50 was kept -- it is what candidate generation already produces,
and 75 costs 50% more inference for 11 more reachable chunks. The
premise was therefore sound: three quarters of the misses were in
principle recoverable by reordering alone.

**Implementation:** `sentence-transformers` `CrossEncoder` with
`cross-encoder/ms-marco-MiniLM-L-6-v2`, local, no external API, gated
behind `RETRIEVAL_RERANK` and degrading to plain hybrid if unavailable.
It reordered only the existing fused candidates -- never adding or
dropping one, so the BM25+dense+RRF recall ceiling was untouched.

**A domain-mismatch warning showed up before any evaluation.** Probed
directly, the model separates a MS MARCO-style pair cleanly (+8.85
relevant vs -4.32 irrelevant) but compresses to near-nothing on
statutory text (-10.34 vs -11.05 for a clearly-relevant vs
clearly-irrelevant BNSS pair). Correct ordering, almost no confidence
margin. This is why its score was deliberately never wired into the
confidence gate.

**Targeted experiment first** (30 known fusion-ranking failures):
66.7% of reachable missed targets improved rank, 50% newly entered the
top-5, mean rank 13.6 -> 10.4, and the FIR queries moved from rank ~18
to rank 2. On that evidence the full evaluation was authorised.

**Full evaluation result, 313-query set (hybrid, vs the post-guard
baseline):**

| Metric | Baseline | + reranker | Δ |
| --- | --- | --- | --- |
| Recall@5 | 0.6246 | 0.6412 | **+0.017** |
| Precision@5 | 0.1381 | 0.1416 | +0.004 |
| MRR | 0.4874 | 0.4846 | **-0.003** |
| nDCG@5 | 0.5160 | 0.5205 | +0.005 |
| Top-1 citation correctness | 0.3879 | 0.3772 | **-0.011** |
| Abstention accuracy | 0.7764 | 0.6677 | **-0.109** |
| False abstains | 69 | 103 | **+34** |
| Wrong-Act top-1 rate | 0.196 | 0.189 | +0.007 |
| **`hard_negative` recall@5** | **0.966** | **0.793** | **-0.173** |

**49-query control, hybrid:**

| Metric | Baseline | + reranker |
| --- | --- | --- |
| Recall@5 | 0.8370 | **0.8074** |
| Precision@5 | 0.1822 | **0.1733** |
| MRR | 0.7096 | **0.6996** |
| nDCG@5 | 0.7227 | **0.7070** |
| Top-1 | 0.6222 | **0.6000** |
| Abstention | 0.9796 | **0.9388** |

On the control set the reranker is worse on **every single metric** --
not a trade-off, just degradation.

#### Why it was rejected

The +1.7pp recall@5 on the citizen set was the only thing it bought, and
three findings outweigh it.

**(a) The hard-negative regression is disqualifying.** `hard_negative`
is the category built to test resistance to legally-wrong-but-lexically-
attractive sections -- the most safety-relevant slice in the set. Its
recall fell 0.966 -> 0.793 (zero-hit groups 1 -> 6). Two of the five
regressions are the exact failure this product must never make:

| Query | Wants | Reranked top-3 |
| --- | --- | --- |
| "bharatiya nagarik **suraksha sanhita** rules about taking bail" | `bnss:478` | `bns:200`, `bns:209`, `bnss:4` |
| "bharatiya **nyaya sanhita** list of punishments" | `bns:4` | `bnss:220`, `bns:200`, `bnss:33` |
| "punishment for grievous hurt" | `bns:117` | `bns:122`, `bns:119`, `bns:125` |
| "who decides consumer disputes at the national level" | `cpa2019:58` | `cpa2019:53`, `cpa2019:76`, `cpa2019:81` |
| "what does the legal services authorities law say about who gets help" | `lsa:12` | `lsa:5`, `lsa:13`, `lsa:4` |

The first two name their Act *in full* and are answered from the other
Sanhita. A retrieval stage that cannot keep the BNS and the BNSS apart
on a query that spells out which one it wants is not safe to put in
front of citizens, whatever it does to aggregate recall.

**(b) The abstention regression is a second safety failure.**
Accuracy 0.7764 -> 0.6677, false abstains 69 -> 103. Mechanism confirmed:
the reranker promotes chunks with lower `dense_score` to rank 1, which
depresses the gate signal, so queries whose correct chunk it had just
pulled into view were suppressed anyway. The recall gain and the
abstention loss are partly the same queries.

**(c) The short-title artifact got worse.** Of ten probes, three moved
the boilerplate `:1` chunk closer to rank 1 and only one moved it away.
Most clearly, `h259` ("which law protects a woman from violence by her
own family") regressed from a correct `pwdva:3` top-1 to the contentless
`pwdva:1` ("Short title, extent and commencement"). This is explicable:
a title-like passage naming the Act looks like an ideal match to a
topical question, which is precisely what an MS MARCO cross-encoder
rewards.

A per-query diff makes the shape of the trade explicit: **29 fixed, 25
broken** -- near parity in count, but asymmetric in composition. It
fixed `ordinary_citizen`/`colloquial` (recall-flavoured) and broke
`hard_negative` (safety-flavoured).

**(d) Cost.** The 313-query evaluation took ~34 minutes against ~4
minutes un-reranked, an ~8x wall-clock increase from 594 cross-encoder
invocations over 50 candidates each. That is per-query latency a
citizen-facing endpoint would have to absorb, for a negative
safety result.

#### Status change: tested and rejected, not merely deferred

This matters for future sessions. Reranking was previously an *untested
deferral* -- "we think the misses aren't this shape." It is now a
**tested and rejected approach**: the premise was verified correct
(76.9% of misses were reachable in the candidate pool), the intervention
was implemented properly, and it still failed on legal-safety grounds.

Do not re-propose a cross-encoder reranker for this project on the
strength of the candidate-pool argument alone -- that argument is
already known to be true and already known to be insufficient. A future
attempt would need to answer the actual failure: a general-purpose
reranker has no notion that BNS and BNSS are different statutes, and
rewards boilerplate that names the Act. A legal-domain-tuned
cross-encoder might; `ms-marco-MiniLM` demonstrably does not.

All reranker code was removed after measurement. `app/retrieval/
search.py` was restored byte-identically to `4f7fd54`, and both eval
sets were re-run to confirm the production path is back to its exact
baseline (49-query hybrid recall@5 0.8370; 313-query hybrid recall@5
0.6246, `hard_negative` 0.966, wrong-Act 0.196).

### Where this leaves embedding fine-tuning

Three of the four candidate interventions from the previous section are
now resolved: the topic/coverage guard shipped and fixed a real safety
gap; confidence calibration was investigated and found to have no
available operating point; reranking was built and rejected. The
remaining failures are, by elimination, concentrated where the evidence
always pointed -- `representation_gap` (29 of 119 misses) and
`dense_embedding` (15 of 119), 37.0% combined, which no reranker and no
gate change can reach.

That does not automatically make fine-tuning correct; it makes it the
next thing worth *evaluating*, with the labelled pool now at ~362 query
groups (313 + 49) against the 153 that run1 concluded was too small.
The standing evaluation discipline is unchanged: held-out-only
measurement, no promotion without real before/after numbers on both eval
sets, and no promotion at all if `hard_negative` recall or the wrong-Act
rate degrades -- the reranker's failure mode is the exact thing a
fine-tune could also cause, and it would be caught the same way.

**No training has been started, and none is authorised.**

## Remaining limitations (as recorded at M9 -- see the note below)

> **Historical, with one item since superseded.** This list was written
> at M9. The first bullet no longer describes the deployed
> configuration: the hybrid floor was recalibrated in M12 against the
> production path over the final 1,827-chunk corpus and the 402-group
> labelled pool, and is now **0.41**, not 0.42. The remaining bullets
> still hold. The final limitation list is in `docs/PROJECT_STATE.md`
> Part A, section 9.

- ~~The confidence-gate thresholds (all three modes) are tuned against a
  49-query hand-curated set over a 1,783-chunk corpus~~ -- **superseded
  in M12.** The hybrid floor is now swept on the production path (the
  normalised text the product actually retrieves on) against a 362-row
  labelled pool, on a tune split with held-out validation, and sits at
  **0.41** over the final **1,827-chunk** corpus. The underlying caveat
  survives the recalibration and is worth keeping: these are real floors
  backed by real numbers, but a much larger labelled set would make them
  statistically robust in a way they still are not. Re-run
  `python eval/run_eval.py --production-path --mode hybrid` and re-sweep
  after any significant corpus growth.
- The hybrid floor was raised 0.40->0.42 after stress-testing
  out-of-domain queries against the expanded corpus found real false
  positives (see `docs/PROJECT_STATE.md`'s "Retrieval/evaluation
  hardening"). That raise alone was not a complete fix -- two of the
  three stress-test false positives found (both ~0.45) still cleared
  the raised floor, and closing that gap fully would have cost a
  genuine query (q20, at 0.4531) under a single global threshold. This
  is now resolved by a smarter, non-score-based signal instead of
  another threshold nudge -- see "Topic-relevance guard: closing the
  out-of-domain gap without another threshold raise" above. It closes
  the specific, curated set of subjects it recognizes; a genuinely
  novel out-of-domain phrasing that doesn't match any curated pattern
  and still scores above the dense-score floor remains a possible gap
  (same accepted trade-off as `query_expand.py`'s abbreviation dict --
  narrow and curated, extended only when evaluation names a new case).
- Bail, compounding of offences, and burden of proof -- the three
  near-miss topics this document originally flagged here -- are no
  longer near-misses: BNSS's bail chapter, s.359, and BSA's
  burden-of-proof sections are all now ingested, and all three now
  answer with a directly relevant citation (verified end to end, see
  `docs/PROJECT_STATE.md`). Two similarly-shaped topics (FIR, child in
  conflict with law) were also confirmed fixed the same way.
- Dense embeddings depend on the optional `sentence-transformers`
  install (`requirements-full.txt`); this environment's global
  TensorFlow/Keras install was incompatible with `transformers`'s TF
  integration path (`ValueError: ... Keras 3 ... not yet supported`).
  Worked around by setting `USE_TF=0` before the first `transformers`
  import (`app/retrieval/embeddings.py`) so only the PyTorch backend
  loads -- harmless in environments without TensorFlow installed at
  all, but worth knowing about if dense mode ever fails to import in a
  new environment.

## M6-era RAG research plan (no implementation authorised)

This section is a **plan only**. Nothing in the retrieval implementation,
the corpus, the embeddings, the thresholds, the safety gates or the
evaluation sets was changed by the M6 engineering-hardening work, and no
experiment below has been started. It exists so a later session begins
from measured evidence rather than from intuition, and so the two
approaches already tested and rejected are not silently retried.

### The frozen baseline (M6-era; NOT the final system)

> **Historical.** "Frozen baseline" here means "frozen for the purposes
> of the M6-era experiments proposed below" -- it is **not** the frozen
> final system. Since this was written the dense model became
> `data/models/m12_run2`, the hybrid floor became 0.41, the corpus grew
> to 1,827 chunks, and every metric below was superseded. The final
> numbers are at the top of this file. Read the table below only as the
> bar those proposed experiments were asked to clear.

At M6 the production path was BM25 + dense (`all-MiniLM-L6-v2`, 384-dim)
fused with weighted RRF (dense weight 3.0, k=5), behind the risk/UPL,
topic-relevance and corpus-coverage guards, with a hybrid confidence
floor of 0.42. Measured numbers **of that era**, restated here so an
experiment had something to beat:

| Metric | 313-query citizen set | 49-query control |
| --- | --- | --- |
| Recall@5 | 0.6246 | 0.8370 |
| Precision@5 | 0.1381 | 0.1822 |
| MRR | 0.4874 | 0.7096 |
| nDCG@5 | 0.5160 | 0.7227 |
| Top-1 citation correctness | 0.3879 | 0.6222 |
| Abstention accuracy | 0.7572 | 0.9796 |
| Wrong-Act top-1 rate | 0.196 | — |
| False accepts / false abstains | 7 / 69 | — |

`hard_negative` recall is 0.966 and is the single most important number
to protect: it is the measure of not confidently citing a
superficially-similar but legally wrong provision.

The two headline weaknesses are **top-1 citation correctness (0.3879)**
and the **wrong-Act rate (0.196)** — the system finds relevant law but
too often leads with the wrong statute. By elimination, the remaining
misses concentrate in `representation_gap` (29 of 119) and
`dense_embedding` (15 of 119), 37.0% combined.

### Reconciling the proposed experiments against work already done

Two of the five commonly-proposed directions are **not open questions
for this project**, and re-running them as stated would repeat a known
result:

- **Cross-encoder reranking — tested and rejected, do not re-propose on
  the candidate-pool argument.** The premise (76.9% of missed chunks are
  reachable in the fused candidate pool) was verified true, a
  `ms-marco-MiniLM` cross-encoder was implemented properly, and it still
  failed on legal-safety grounds: `hard_negative` recall 0.966 → 0.793
  and abstention accuracy 0.7764 → 0.6677, bought for +1.7pp recall@5.
  The diagnosis was that a general-purpose reranker has no notion that
  BNS and BNSS are different statutes and rewards boilerplate naming an
  Act. A future attempt must answer *that* failure — a legal-domain-tuned
  cross-encoder — not restate the pool argument.
- **Hard negatives — already built, not missing.** `hard_negative` is an
  existing category (29 of the 313 groups). The open work is *expanding*
  it toward the wrong-Act failure mode, not creating it.

Three directions are genuinely open. They are ordered by expected value
against the two headline weaknesses:

### Experiment 1 — structured legal chunks (highest expected value)

Carry `act`, `chapter`, `section`, `heading` and `provision text` as
first-class fields on each chunk rather than flattening them into one
text blob, and make the Act identity available to scoring.

Rationale: this is the only proposed intervention that targets the
wrong-Act rate (0.196) at its cause. The reranker failed precisely
because nothing in the pipeline represents "BNS and BNSS are different
statutes"; structured chunks put that distinction into the
representation instead of hoping a model infers it. It also plausibly
reaches part of `representation_gap`.

Risks to watch: re-chunking changes every embedding, so the whole
baseline must be re-measured, not spot-checked; and finer chunks can
raise precision while quietly costing recall.

### Experiment 2 — citizen-language query understanding

Partly explored already: `query_expand.py` carries a deliberately narrow,
curated abbreviation dictionary, and broader preprocessing was previously
deferred rather than disproven. Genuinely untested: legal synonym
mapping, intent/topic detection, and multi-query retrieval (issue several
reformulations, fuse the results).

**Constraint:** hypothetical-document generation (HyDE) would introduce a
generative model into the legal path. That collides with the standing
"no generative LLM in the legal-answer pipeline" decision, and must not
be attempted without explicit approval, even though it sits in retrieval
rather than in answer construction. Evaluate the deterministic options
first — they are cheaper and carry no hallucination surface.

### Experiment 3 — top-1 / top-3 answer shaping

Do not simply lower `top_k` from 5 to 1. The question worth measuring is
whether retrieving a wide pool, then applying the safety gate, then
returning the 1–3 provisions that survive, improves top-1 citation
correctness and the wrong-Act rate **without** costing recall or
abstention accuracy. Note that this interacts with Experiment 1: if
structured chunks fix Act identity, top-1 shaping becomes much safer.

### Evaluation methodology

Every experiment reports the same table, on both sets, held-out only:

| System | Recall@5 | Precision@5 | F1 | MRR | nDCG@5 | Top-1 citation | Top-3 recall | Abstention accuracy | False accepts | Wrong-Act rate | `hard_negative` recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline (frozen) | | | | | | | | | | | |
| + structured chunks | | | | | | | | | | | |
| + query understanding | | | | | | | | | | | |
| + expanded hard negatives | | | | | | | | | | | |
| Combined | | | | | | | | | | | |

Promotion rules, unchanged from the standing discipline:

1. No promotion without before/after numbers on **both** eval sets.
2. **No promotion at all if `hard_negative` recall or the wrong-Act rate
   degrades**, whatever else improves. This is the rule the reranker
   failed, and it is what makes the abstention behaviour trustworthy.
3. A single improved metric is not evidence; recall bought with
   abstention accuracy is a regression in a legal-information system.
4. Re-run both sets after any corpus change before comparing anything.

### Observation recorded during M6 verification (not acted on)

Running the frozen pipeline locally to confirm the baseline still
behaves, `"Someone is breaking into my house right now"` returned
`policy_decision: answered` rather than an emergency redirect, while
self-harm and domestic-violence phrasings correctly returned
`redirect_emergency` and `"Should I plead guilty in my case tomorrow?"`
correctly returned `redirect_adviser`. Burglary-in-progress is plausibly
inside the documented "active crime" emergency category. This was **not
changed** — the safety gates are frozen — but it is a concrete candidate
for the hard-negative/safety expansion in the work above.

---

# PART C: FINAL MILESTONES (authoritative)

## M12 — production-path evaluation, failure taxonomy, and a fine-tune that finally generalises

**A second measurement series.** `run_eval.py --production-path` retrieves
on `app.query.normalize`'s output — the text `handle_legal_query` actually
searches — closing the M9 "the harness measures a path the product does
not use" gap without touching the historical raw-query series (the
default is unchanged and still reproduces every documented number).
Production-path baselines at the start of M12: control hybrid recall@5
0.8623 / abstention 0.9796 (`q19` the sole false abstain); citizen
0.7199 / 0.8307, zero false accepts, 53 false abstains.

**Failure taxonomy** (every hybrid production-path failure, 112 rows):
G_gate 35 (gold in the top-5, pipeline abstained — 17 with gold at rank
1), F_ranking 23 (in both top-50 pools, below 5), E_one_pool 40 (mostly
absent from BM25 — vocabulary), E_both_pools 14 (representation).

**Promoted, one variable at a time, each measured against both sets:**

1. *Curated spelling layer* (`app/query/spelling.py`) + seven
   probe-verified normalisation rules (theft/theft-by-servant/cheating
   with police- and consumer-stand-downs, e-commerce scam, PWDVA / JJ-CCL
   / CWC abbreviations) + two child-rule extensions ("under 16/17/18",
   turn-spanning order). Citizen production-path recall@5 0.7199 →
   0.7448, abstention 0.8307 → 0.8498; control byte-identical. A GENERIC
   edit-distance corrector against the corpus vocabulary was built and
   REJECTED: statutes don't contain ordinary English, so "unknown token"
   ≠ "misspelled token" ("texting"→"testing", "goons"→"goods").
2. *Gate floor 0.42 → 0.41.* The 0.42 floor was calibrated against
   raw-query scores; on the production path the highest score any
   should-abstain query reaches is 0.399. Swept on a tune split (control
   + odd citizen rows), validated held-out (even rows): zero new false
   accepts, zero wrong-Act change, both splits. Citizen abstention
   0.8498 → 0.8562. An agreement-branch gate (BM25∧dense rank ≤2,
   dense ≥0.30) was measured and REJECTED: +5 good answers, +2 wrong-Act
   — both methods can agree on the same wrong chunk.
3. *Follow-up benchmark 18 → 40 rows* (`queries_followup.jsonl`, all
   targets corpus-verified) with detection fixes (content-cap 3,
   definitional-opening stand-down, pronoun/fragment rules): condition
   follow-ups 19/21 with context vs 3/21 fragment-only; ambiguous 4/4,
   no-context 4/4, standalone-override 3/3, guarded 6/6, not-emergency
   2/2. Residuals: f04 (the M8 FIR-copy recall miss), f24 (rti:19
   ranking).
4. *Emergency tense fix:* "he hit me last year" no longer routes to a
   helpline ("last year|month" added to the historical frame; "last
   week" deliberately kept on the emergency side). 40-case matrix still
   green.

**End state:** control 0.8623 / 0.9796 (unchanged, `q19` only); citizen
recall@5 **0.7448**, MRR 0.5656, top-1 0.4448, abstention **0.8562**,
zero false accepts, 45 false abstains. Remaining taxonomy: G_gate 32
(all now score-depressed below the floor/ceiling squeeze — a
representation problem), F_ranking 29, E_one_pool 32, E_both 9.

**Embedding fine-tune m12_run2 — validated on held-out data, first time.**
The remaining failure mass is representation-shaped, and the labelled
pool (402 groups) is 2.6× run1's fatally-small 153. Same infra, same
group-separated splits (train 1682 / val 340 / test 368 triplets,
leakage-checked), 4 epochs MNRL from the production checkpoint. On the
**test-split-only** queries (never trained or selected on): citizen
recall@5 0.6171 → **0.7024**, MRR 0.4837 → 0.5833, top-1 0.3902 →
0.4878, abstention 0.7561 → 0.8293; original-set MRR/top-1 up,
recall@5 equal, one new false ABSTAIN (`q17`, the historically
unreachable `constitution:20` — conservative direction). Safety screen
over all 362 rows: hard-negative recall 28/29 → **29/29**, wrong-Act
top-1 46 → **22**, zero end-to-end false accepts (every abstain-side row
whose gate score rose is blocked by the model-independent raw-text
guards; emergency routing never touches embeddings). **Not yet flipped
into production:** doing so means distributing a ~90 MB model artifact
(git, HF upload, or object storage) — a deployment decision recorded for
the user. Reproduce with `python services/ai/finetune/build_dataset.py
&& python services/ai/finetune/train.py --run-name m12_run2 && python
services/ai/finetune/eval_heldout.py --run-name m12_run2` (seeded,
deterministic splits). To deploy once distributed: set
`DENSE_EMBEDDING_MODEL` to the artifact path and re-run
`scripts/ingest_corpus.py`.

## M13 — m12_run2 deployed to the production path, promoted, and frozen

**Deployment mechanism (no new infrastructure).** The artifact was copied
to `services/ai/data/models/m12_run2` and the index rebuilt with
`DENSE_EMBEDDING_MODEL=data/models/m12_run2` (run from `services/ai`) —
exactly the one-variable migration path `app/retrieval/embeddings.py`
always documented. The model path is *service-root-relative* and that
relative form is what `index_manifest.json` records; `embeddings.py`
gained a `resolve_model_path()` that resolves it against the service root
at load time only, so the same manifest works on the host (any CWD) and
inside the Docker image, where `docker-compose.yml` already mounts
`./services/ai/data` at `/app/data` read-only — the container picks up
both the new index and the model on restart with **no image rebuild**.
Query-time model selection was already manifest-driven (`search.py` reads
`dense_embedding_model`), so the running service can never encode queries
with a different model than the one that built the mounted index.
`data/models/` is gitignored under the same policy as the index: a build
artifact, reproduced by the seeded pipeline above, never committed.

**Exact artifact identity.** `model.safetensors` SHA-256
`d61d077b4287c2cd1075045dccec0139981751fc1125e1bcd92dc29e0a0ce801`;
aggregate SHA-256 over all 11 files (sorted `relpath:file-sha` walk)
`8a15eb039e298e44b25959903c79808f51c9194b75b92f410d567300981c95fa`;
91,861,927 bytes. Training config as recorded in
`finetune/output/m12_run2/train_config.json` (4 epochs, batch 16, lr 2e-5,
seed 42, MNRL, 1682/340 train/val triplets). After deployment the stored
`dense_vectors.npy` rows were verified to be m12_run2 encodings (cosine
1.0 against fresh encodings of the same index text; the base MiniLM
scores 0.78–0.93 against those rows — the check genuinely discriminates).

**Protocol.** Production-path series (`run_eval.py --production-path
--mode hybrid`), same corpus (1,827 chunks), queries, normalisation,
guards, gate floor (0.41), fusion weights and scoring code on both sides;
the only variable is the embedding model behind the dense index. The M12
baseline was re-reproduced exactly before switching (citizen 0.7448 /
0.5656 / 0.4448 / 0.8562 with 0 false accepts and 45 false abstains;
control 0.8623 / 0.9796 with `q19` sole; follow-up 19/21, 4/4, 4/4, 3/3,
6/6, 2/2). Every candidate number below was then reproduced **twice**,
byte-identically (summary and per-query), after the index-overwrite
incident described at the end of this section was found and eliminated.

**Full-set results (contain trained-on queries — these are the deployed
system's benchmark numbers, not generalisation evidence):**

| citizen 281 | baseline | m12_run2 | | control 46 | baseline | m12_run2 |
|---|---|---|---|---|---|---|
| recall@5 | 0.7448 | **0.9554** | | recall@5 | 0.8623 | **0.9674** |
| MRR | 0.5656 | **0.8800** | | MRR | 0.7341 | **0.9246** |
| nDCG@5 | 0.6040 | **0.8984** | | nDCG@5 | 0.7476 | **0.9261** |
| top-1 citation | 0.4448 | **0.8185** | | top-1 citation | 0.6522 | **0.8913** |
| abstention | 0.8562 | **0.9233** | | abstention | 0.9796 | 0.9592 |
| false accepts | 0 | **0** | | false accepts | 0 | **0** |
| false abstains | 45 | **24** | | false abstains | 1 (q19) | 2 (q19, q17) |
| wrong-Act top-1 | 43 | **19** | | wrong-Act top-1 | 3 | 3 (no new) |

Citizen per-category recall@5: every category improved or equal —
`hard_negative` 0.966 → **1.000**, `misspelling` 0.773 → 1.000,
`ordinary_citizen` 0.745 → 0.982, `multi_source` 0.500 → 0.944,
`ambiguous` 0.537 → 0.933, `colloquial` 0.705 → 0.886. Per-query diff 60
fixed / 6 broken (h027, h060, h079, h194, h198, h252 — four of the six
abstain in the candidate rather than answering wrongly). Control: q18,
q40, q46 fixed, none broken; q17's new false abstain is the historically
unreachable `constitution:20` query, in the conservative direction, as
the M12 held-out screen predicted.

**Held-out-only results (promotion-gate condition 1 — restricted to
`finetune/data/test.jsonl` ids, never trained or selected on):** citizen
41 queries: recall@5 0.7634 → **0.8732**, MRR 0.5687 → 0.7122, top-1
0.4634 → 0.6098, abstention 0.7561 → 0.8293, false accepts 0 → 0, false
abstains 10 → 7. Control 9 queries: recall@5 equal at 0.8333, MRR 0.7259
→ 0.8000, top-1 0.6667 → 0.7778. The held-out improvement reproduces on
the path production actually runs.

**Held-out wrong-Act movement, inspected individually (4 → 8).** h142 and
h148: the candidate *abstains* — the wrong-Act top-1 is never shown, and
the user-visible change is correct-answer → abstention (conservative,
already counted in false abstains). h258 ("protection of action taken in
good faith", 5 labelled targets): candidate top-1 is `rti:21`, which IS
the RTI Act's identically-titled protection section — a label gap (the
row predates RTI ingestion), not a wrong answer; 4 of 5 labelled targets
still in top-5. h252: a genuine mild regression — top-1 moved from
`pwdva:17` to `bnss:144` (maintenance) on a residence/custody query; an
adjacent-domain ranking miss, not a cross-statute confusion. No new case
is a confidently-answered cross-Sanhita error, the full-set wrong-Act
count *fell* 43 → 19, and `hard_negative` (including the bidirectional
BNS/BNSS decoy pair) is 29/29.

**Follow-up benchmark (40 rows):** condition follow-ups 19/21 both sides,
with composition changed — **f04, the long-standing M8 FIR-copy recall
miss, is fixed**; f22 newly misses on ranking; f24 (`rti:19`) unchanged.
Ambiguous 4/4, no-context 4/4, guarded 6/6 with byte-identical reasons,
not-emergency 2/2. Standalone override 2/3: f35 now abstains instead of
answering — conservative direction, recorded as a residual. Fragment-only
baseline hit@5 improved 3/21 → 6/21.

**Live battery on the deployed index** (`handle_legal_query`, the exact
function `POST /legal/answer` wraps): 9/9 — supported query answered
(`constitution:14` top-1), citizen-language stolen-phone complaint
answered (`bnss:106`), misspelled "bale" answered (`bnss:482`/`480`),
ambiguous answered, out-of-domain abstained, un-ingested-Act (divorce)
abstained via the coverage guard, emergency redirected, UPL
personal-outcome abstained, harmful request refused. Citation integrity:
every returned excerpt's chunk_id present in `chunk_manifest.jsonl`, real
source/act_no/unit/official-URL citations.

**One live-test residual found post-deployment** (by
`test_corpus_coverage.py`'s RTI battery, not by either eval set): "can an
officer be penalized for not providing information" now ranks `it_act:44`
first (dense 0.508) and `rti:20` second (0.469) — under the baseline
model `rti:20` was rank 1. IT Act s.44 is itself a genuine
penalty-for-not-furnishing-information provision and the query names no
Act, so the top-1 preference between two legitimately responsive statutes
is ambiguous by construction; the citizen sees both excerpts (the product
always renders the full returned window). The test now asserts
presence-in-window for that one phrasing — same documented convention as
the BNSS s.43 window test — and strict top-1 for the other four RTI
phrasings, all of which still pass. Recorded in the failure taxonomy as
an adjacent-domain top-1 preference (same class as h252), not a safety
failure. No normalisation rule was added for it: tuning the production
path against a single probe after the evaluation numbers were finalised
would invalidate the published comparison.

**Promotion verdict: all nine gate conditions pass — PROMOTED.** The
gate that mattered most going in — the reranker's failure mode of
cross-statute confusion — is where the fine-tune is strongest
(hard-negative 29/29, wrong-Act nearly halved), which is what
justifies promotion where `ms-marco-MiniLM` was rejected.

**An incident worth recording: the test suite silently reverted the
production index.** `tests/test_retrieval.py` and
`tests/test_hybrid_retrieval.py` deliberately rebuild the real
`data/index` via `ingest_all()` + `build_index()`; with
`DENSE_EMBEDDING_MODEL` unset in the test environment that rebuild used
the *default* base model — so the first post-deployment pytest run raced
the candidate evaluation and put a MiniLM index back underneath it
(caught by file mtimes plus the vector-identity probe above; the
candidate evals had already loaded the m12_run2 index into process
memory, which is why their numbers were unaffected — subsequently proven
by byte-identical confirmation re-runs against a cleanly rebuilt index).
Fix shipped in `tests/conftest.py`: before any test runs, the suite pins
`DENSE_EMBEDDING_MODEL` to whatever the on-disk manifest records
(explicit env still wins; a recorded-but-absent local artifact falls
through to the default), so the tests' rebuild now reproduces the
deployed configuration instead of downgrading it. Verified by running the
full suite with the variable unset and checking the manifest and vectors
afterwards. New unit tests for the path resolution:
`tests/test_embeddings_config.py`.

---

## ICCSDI 2026 revision: corrected corpus, case-law guard, repeated seeds

Everything in this section was produced for the ICCSDI 2026 minor
revision, on top of the frozen M13 state plus the two post-freeze
safety-routing commits. Artifacts live in
`finetune/output/revision_eval/` and `finetune/output/seed<N>_rev/`.

**Corrected corpus (1,827 → 1,832 chunks).** The five documented
extraction defects (BNS 217/255 and JJ Act 61/86 merged into the
preceding chunk; RTI s.14 dropped inside the excluded s.13) were fixed
by curated, asserted `section_splits` repairs (see
`docs/LEGAL_SOURCES.md`), the index rebuilt with `m12_run2`, and the
full production-path evaluation re-run for both the base and the
promoted model with `finetune/eval_seeds.py`:

    python finetune/eval_seeds.py --model data/models/m12_run2 --label m12_run2_fixed \
        --json-out finetune/output/revision_eval/m12_run2_fixed.json
    python finetune/eval_seeds.py --model sentence-transformers/all-MiniLM-L6-v2 \
        --label base_fixed --json-out finetune/output/revision_eval/base_fixed.json

**Result: the corpus correction changed no headline metric on either
model.** Citizen-281: recall@5 0.7448 → 0.9554, MRR 0.5656 → 0.8800,
nDCG@5 0.6040 → 0.8984, top-1 0.4448 → 0.8185, wrong-Act top-1 43 → 19,
hard-negative 28/29 → 29/29; control-46 identical to the frozen record;
held-out 41: recall@5 0.7634 → 0.8732, MRR 0.5687 → 0.7122, top-1
0.4634 → 0.6098. Zero false accepts everywhere. The only movement is
one benchmark row, `h017` ("my neighbor broke into my house at night"),
which the post-freeze emergency-routing refinement now routes to
official help (`risk_active_crime`) instead of answering — so false
abstains are 46 base / 25 fine-tuned (was 45/24), held-out 11/8 (was
10/7), abstention accuracy 0.8530 → 0.9201 deployed and 0.7317 → 0.8049
held-out. `h017` is a policy-routed row, not a gate withholding: its
target `bns:331` still ranks 1 at dense 0.587. Follow-up benchmark
unchanged (19/21, 4/4, 4/4, 6/6, 2/2, 2/3; f35 residual). Residual
failure taxonomy over the 281 answer-expected rows: 18 gate-only, 6
retrieval-only, 6 both, 1 policy-routed (31 total). Of the 19 wrong-Act
rows: 7 withheld by the gate (wrong statute never shown), 9 answered
with a labelled target still inside the shown top-5 window, 3 answered
with no target in the window (h036, h040, h252); none is a BNS/BNSS
confusion.

**Case-law coverage guard.** A fresh scripted citation audit
(`eval/audit_citations.py`: 26 probes across every route, 95 excerpts,
zero citation defects, including the five repaired sections) surfaced
one behaviour gap: "supreme court judgment on privacy" was answered
with five statutory excerpts. No judgment of any court is ingested, so
`corpus_coverage.py` gained a narrow `case_law` category with its own
message (`CASE_LAW_MESSAGE`), built under the guard's usual discipline:
patterns require the case-law framing itself ("case law", "precedent",
a court name beside "judgment/ruling/verdict", "judgment on <topic>"),
bare "judgment" keeps answering (BNSS pronouncement, Art. 137 review),
and the 362-labelled-query over-block scan plus four hand-written
answerable near-misses pass. Tests in `tests/test_corpus_coverage.py`.
No benchmark row matches the new category, so every recorded number
above is unaffected.

**Repeated-seed stability (reviewer-requested).** The frozen protocol's
byte-identical re-runs verify deterministic reproducibility, not seed
variance. `finetune/run_seed_experiment.py` retrains the promoted
configuration under seeds 42–46 — corpus, frozen triplet splits
(`finetune/data/*.jsonl`, untouched), MNRL, 4 epochs, batch 16, lr
2e-5, warmup and evaluation protocol all constant, no per-seed tuning —
and evaluates each run on the production path (deployed + held-out)
with `eval_seeds.py`. Per-seed results:
`finetune/output/seed<N>_rev/seed_eval.json`; summary recorded in the
revision report alongside the paper.

**Repeated-seed results (held-out citizen 41, production path).**
Recall@5 0.8634 ± 0.0134 (per-seed 0.8732 / 0.8732 / 0.8488 / 0.8732 /
0.8488 for seeds 42–46; the worst seed clears the base encoder's 0.7634
by 8.5 pp), MRR 0.7170 ± 0.0214, top-1 citation correctness 0.6244 ±
0.0408, abstention accuracy 0.7805 ± 0.0345 (false abstains 8/10/7/10/10).
Deployed benchmark across seeds: recall@5 0.9581 ± 0.0021, MRR 0.8833 ±
0.0033, top-1 0.8263 ± 0.0068, wrong-Act top-1 16–19 (mean 17.2, base
43), hard-negative **29/29 on all five seeds**. The retrained seed-42
run reproduces the promoted `m12_run2` numbers exactly — end-to-end
training determinism on the corrected corpus.

**One stability finding acted on.** Seed 45 produced the sweep's only
false accept: h293 ("what is the minimum wage for a construction
worker", abstain-expected) answered from `bns:146` (unlawful compulsory
labour) over the 0.41 floor. This subject had deliberately been left to
the confidence gate after a probe showed the gate abstaining; the sweep
shows that margin is not seed-robust, which is exactly the guard's
documented extension condition. `corpus_coverage.py` gained a
`minimum_wages` category ("minimum wage(s)" occurs zero times in the
indexed corpus, so the bare phrase is safe), regression-tested in
`tests/test_corpus_coverage.py`. The change is metric-neutral for the
promoted model, which already abstained on that row via the gate; the
seed-45 number is reported as measured, not re-run under the new guard.
Zero false accepts therefore remains a property of the promoted run and
of 4 of 5 seed runs — not a guarantee of the configuration, and the
paper says so.
