# Citizen Assistance Technology (CAT)

> Your rights. Your service. Your voice.

CAT is an India-focused citizen platform that answers legal questions
**only from official statutory text it has actually retrieved**, teaches
the same law in plain language, and gives citizens two civic workflows
(issue reports and petitions) with a simulated authority side.

CAT provides public awareness and information only. It is not legal
advice or legal representation. For real-world legal implications,
contact a qualified legal adviser. In an immediate emergency, call
**112**.

> **Status: FROZEN at `c24eda2` (M13).** M10-M13 are complete. This
> README describes the final system. `docs/PROJECT_STATE.md` is the
> authoritative current-state document and also carries the full
> milestone history.
>
> *Naming note:* the product is **CAT**. The npm workspace scope
> (`@cap/web`, `@cap/api`, `@cap/contracts`), the FastAPI service title
> and the seeded local accounts still use the project's earlier `cap`
> identifier. That is a code-level name only, deliberately left
> unchanged at the freeze.

## Repository layout

```text
apps/web/                 React + TypeScript citizen-facing application
services/api/             Node + Express core application API
services/ai/              Python + FastAPI AI-service boundary
packages/contracts/       Shared API/domain contracts
docs/                     Architecture, project state, evaluation, source inventory
infra/                    nginx and local infrastructure configuration
```

## 1. Modules

| Module | What it does |
| --- | --- |
| **Learn** | 71 grounded learning articles across 12 categories, 216 quiz questions and 35 "What should I do?" FAQs. Every substantive paragraph cites the exact Article or section it was written against. Static, authored content -- the frontend never calls the AI service to render it. |
| **Legal Assistant** | `POST /api/legal/answer`. A citizen question runs through deterministic safety and coverage guards, then hybrid retrieval, then a confidence gate. The response is the **verbatim retrieved excerpt(s)** with real citations, or an abstention / clarification / redirect. Supports safe multi-turn follow-ups. |
| **Civic Reporting** | Citizen issue reports with optional photo (metadata stripped before storage), deterministic duplicate handling, and an authority workflow: declared transition table, server-controlled status history, staff-assigned priority with SLA deadlines, paginated and filtered authority queues. |
| **Petitions** | Petition lifecycle, one signature per account enforced by a unique compound index in MongoDB, public browse/detail with deterministic free-text search, and an authority moderation queue with a formal response panel. |

## 2. Technology stack

| Technology | What it actually does here |
| --- | --- |
| **React 18 + TypeScript + Vite + Tailwind** | The citizen-facing UI (`apps/web`). React Router for routing, React Query for server state, React Hook Form + Zod for forms. |
| **Node.js 20 + Express** | The main application API (`services/api`): auth/RBAC, civic reports, petitions, media, and the proxy to the AI service. All business workflows live here. |
| **MongoDB + Mongoose** | Application/domain data -- users, reports, petitions, signatures, status history. Two correctness guarantees (one signature per citizen per petition, unique user email) are enforced by unique indexes, not by application code. |
| **Python 3.11 + FastAPI** | The AI / legal-retrieval service (`services/ai`): ingestion, index build, retrieval, the safety layer and deterministic answer assembly. It is a boundary, not a second application -- it owns no user data. |
| **rank-bm25** | Lexical retrieval. Carries the statutory-term half of a query (exact section titles, Act vocabulary). |
| **sentence-transformers** | Semantic retrieval. Encodes chunks and queries into 384-dim vectors; the production checkpoint is the fine-tuned `m12_run2` artifact (see section 5). Local only -- no paid API, no external inference call. |
| **Weighted Reciprocal Rank Fusion** | Combines the BM25 and dense **rankings** (not their scores, which are on incomparable scales) into one ordering. |
| **Deterministic safety / coverage rules** | Plain Python rule sets that decide whether retrieval runs at all and whether an answer may be shown. No classifier, no model, no generation. |
| **pypdf + pdfplumber** | Corpus ingestion from official PDFs, including a coordinate-based extractor for the two-column India Code gazette layout. |
| **Docker + Docker Compose** | Reproducible five-service local stack (web, api, ai, mongo, redis) with health checks and volume-persisted media / index / model data. |
| **GitHub Actions** | CI: typecheck, unit tests, production build, diff hygiene, the Python suite, and a MongoDB-service integration job. A separate scheduled workflow builds and smoke-tests the whole Compose stack. |

**Provisioned but not load-bearing, stated honestly.** Redis runs as a
Compose service and `REDIS_URL` is validated at boot, but no application
code connects to it -- rate limiting uses `express-rate-limit`'s
in-process store, which is correct for the single API instance this
project deploys and is recorded as a known limitation (section 10). A
Socket.IO server is mounted on the HTTP server and emits a readiness
handshake; no product feature uses real-time updates.

## 3. High-level architecture

```text
apps/web/            React + TypeScript citizen UI
       |
       v
services/api/        Node + Express application API  --->  MongoDB
       |                                                   local media storage
       v
services/ai/         Python + FastAPI AI service     --->  BM25 + dense index
                                                           over the legal corpus
packages/contracts/  Shared API/domain contracts (Zod)
```

The web app never talks to the AI service directly. Every legal call goes
`web -> /api/legal/answer (Node) -> /legal/answer (FastAPI)`, so the AI
boundary stays replaceable and traffic still passes the API's rate
limiting, logging and disclaimer handling.

Full detail -- including the civic and petition state machines -- is in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 4. Legal retrieval and safety architecture

The legal-answer pipeline, exactly as `handle_legal_query` implements it:

```text
USER QUESTION
   |
   v  Risk / UPL policy          harmful_request -> refuse; emergency -> helpline;
   |                             serious -> caution, retrieval still runs
   v  Context resolution         resolve a follow-up against the previous turn,
   |                             or ask for a restatement -- never guess
   v  Guard re-run               the combined text is client-supplied, so every
   |                             deterministic guard runs again; stricter wins
   v  Topic relevance            known non-legal subject -> abstain before retrieval
   |
   v  Corpus coverage            names an Act this corpus lacks -> abstain
   |
   v  Query normalization        append statutory vocabulary to the RETRIEVAL text only
   |
   v  BM25 + dense retrieval     top-50 candidate pool from each
   |
   v  Weighted RRF               k=5, dense weight 3.0, BM25 weight 1.0 -> top-5
   |
   v  Confidence / evidence gate hybrid floor 0.41 on the top hit's dense score
   |
   v  Citation verification      citations are structural manifest metadata, never text
   |
   v  DETERMINISTIC RESPONSE     the verbatim excerpt(s) + citations + disclaimer
```

If evidence is insufficient the pipeline **ABSTAINS** ("no verified
information found"), **CLARIFIES** (a follow-up it cannot resolve
safely), or **ROUTES** (an official helpline, a legal-aid service, or a
government-services portal). It never fills the gap.

### Deterministic safety routing

Every query is assessed by the deterministic safety router
(`services/ai/app/safety/risk.py`) **before** any legal retrieval runs.
No LLM and no trained classifier is involved: the router is a rule-based
policy that combines three independent signals -- the **subject** of the
query (tiered by potential harm), its **framing** (informational vs.
instructional vs. personal), and its **immediacy** (whether the
situation is presented as live) -- plus grammatical constraints and
tense, rather than matching single keywords. Every routing decision is
therefore auditable: the matched category is returned in the response's
`reason` field.

The four outcomes:

| Severity | Behaviour |
| --- | --- |
| `normal` | Straight through to the ordinary legal retrieval pipeline, unchanged. |
| `serious` | A real legal matter affecting the asker: a live accusation, an interrogation, an imminent arrest -- or a serious incident they personally experienced that is now over (a past burglary, a past assault, abuse that has ended). A caution and a legal-aid route lead the response (`redirect_adviser`); retrieval still runs so the general law can be shown behind the same confidence gate, never as a plain answer. |
| `emergency` | An immediate-danger situation presented as real and current. A fixed official-helpline message is returned and **zero retrieval happens** -- retrieved legal provisions are never shown as the answer to someone in danger. |
| `harmful_request` | A request for help obstructing justice (destroying evidence, fabricating an alibi, intimidating a witness, evading an investigation). Refused outright; no retrieval. |

The router distinguishes an active personal-safety situation from a
legal-information question about the same crime:

```text
"I am being kidnapped"                    -> emergency (helpline, no retrieval)
"there is a thief in my house right now"  -> emergency (helpline, no retrieval)
"What is the punishment for kidnapping?"  -> normal legal retrieval
"What is the punishment for murder?"      -> normal legal retrieval
```

A purely educational framing ("what does the law say about...",
impersonal, non-urgent) keeps heavy subject words on the normal path,
and an explicitly historical account of the asker's own victimisation
("my husband used to beat me years ago", "there was a thief in my house
yesterday") routes to the `serious` adviser tier rather than to a
helpline -- immediacy always defeats the historical reading, never the
reverse. Emergency
messages are fixed configuration text naming only official national
helplines (112, 181, 1098, 1930); nothing is generated or invented.

This is a deliberately conservative rule policy, not an exhaustive
emergency classifier: it will not recognise every possible phrasing of
danger, and anything it does not recognise falls through to the ordinary
guards and confidence gate. Its contract is pinned by the severity
matrix in `services/ai/tests/test_safety.py`.

### The 0% generative LLM invariant

**No generative LLM runs anywhere in the legal-answer pipeline. Not as a
generator, not as a reranker, not as a fallback, not as a classifier.**

An LLM-generation design (provider abstraction, a working Gemini
integration, citation validation over generated text) was fully built
early in the project and then deliberately discarded once weighed against
hallucination risk in a legal-information context. This is a standing
decision, not a temporary state.

What the invariant buys, concretely: there is no free text to fact-check,
because nothing writes any. Every user-visible legal sentence is either a
verbatim chunk of an official Act or one of a small set of hand-written,
test-pinned templates. Multiple or conflicting sources are returned as
separate excerpts with separate citations rather than merged into one
synthesized paragraph. `sentence-transformers` appears in the stack as an
*encoder*: it turns text into vectors for similarity search and emits no
words.

## 5. Final corpus and final model

**Corpus -- 10 official Acts, 1,832 chunks** (counted from
`services/ai/data/index/chunk_manifest.jsonl`; the ICCSDI 2026 revision
recovered five previously mis-attributed or dropped sections -- BNS
217/255, JJ Act 61/86, RTI s.14 -- see `docs/LEGAL_SOURCES.md`,
"Curated section-split repairs"):

| Source | Chunks | Source | Chunks |
| --- | ---: | --- | ---: |
| Bharatiya Nagarik Suraksha Sanhita, 2023 | 531 | Juvenile Justice Act, 2015 | 112 |
| Constitution of India | 366 | Consumer Protection Act, 2019 | 107 |
| Bharatiya Nyaya Sanhita, 2023 | 358 | Information Technology Act, 2000 | 92 |
| Bharatiya Sakshya Adhiniyam, 2023 | 170 | Protection of Women from DV Act, 2005 | 37 |
| | | Legal Services Authorities Act, 1987 | 32 |
| | | Right to Information Act, 2005 | 27 |

Coverage is deliberately partial and every gap is recorded -- see
[docs/LEGAL_SOURCES.md](docs/LEGAL_SOURCES.md). CAT does **not** claim
complete coverage of Indian law.

**Model -- `data/models/m12_run2`**, a fine-tune of
`sentence-transformers/all-MiniLM-L6-v2` (384-dim,
MultipleNegativesRankingLoss, 4 epochs, batch 16, lr 2e-5, seed 42,
1682/340 train/val triplets). `model.safetensors` SHA-256
`d61d077b...0ce801`. It is a **gitignored build artifact**, reproduced by
the seeded pipeline in `services/ai/finetune/` -- never committed. See
section 12 for how it is loaded.

**Retrieval configuration:** hybrid mode, top-50 candidate pool per
method, weighted RRF (k=5, dense 3.0 / BM25 1.0), top_k 5, confidence
floor 0.41 evaluated against the top hit's dense score.

## 6. Final production evaluation

These are the deployed system's benchmark numbers on the path production
actually runs (`run_eval.py --production-path --mode hybrid`). The
baseline is the same pipeline with only the embedding model reverted.
Every candidate number was reproduced twice, byte-identically.

| Metric | Citizen 281 | Control 46 |
| --- | --- | --- |
| Recall@5 | 0.7448 -> **0.9554** | 0.8623 -> **0.9674** |
| MRR | 0.5656 -> **0.8800** | 0.7341 -> **0.9246** |
| nDCG@5 | 0.6040 -> **0.8984** | 0.7476 -> **0.9261** |
| Top-1 citation correctness | 0.4448 -> **0.8185** | 0.6522 -> **0.8913** |
| Abstention accuracy | 0.8562 -> **0.9233** | 0.9796 -> 0.9592 |
| False accepts | 0 -> **0** | 0 -> **0** |
| Wrong-Act top-1 | 43 -> **19** | 3 -> 3 (no new) |
| Hard-negative recall | **29/29** | -- |

**The 281- and 46-query sets contain queries the model was trained on.
They are the deployed system's benchmark, not generalisation evidence.**

The generalisation claim is the separate **held-out-only** evaluation,
restricted to ids in `finetune/data/test.jsonl` that were never trained
or selected on -- citizen 41 queries: recall@5 0.7634 -> **0.8732**, MRR
0.5687 -> 0.7122, top-1 0.4634 -> 0.6098, abstention 0.7561 -> 0.8293,
zero false accepts. Control 9 queries: MRR 0.7259 -> 0.8000, top-1 0.6667
-> 0.7778.

`docs/RETRIEVAL_EVALUATION.md` carries the full method, the per-category
splits, the individually inspected regressions, and the experiments that
were measured and **rejected** (cross-encoder reranking, a
citizen-language concept index, a generic spelling corrector, an
agreement-branch gate).

## 7. Context / follow-up capability

The Legal Assistant resolves a safe follow-up ("what if I'm a minor?") by
**deterministic composition** with the previous question -- no model, no
LLM. The combined text is shown back to the citizen verbatim, so nothing
is interpreted invisibly, and every safety guard re-runs against it with
the stricter outcome winning, so context can never carry a query past a
decision the first turn already lost. A follow-up that cannot be resolved
safely asks for a restatement instead of guessing.

Measured on a 40-row corpus-verified benchmark: condition follow-ups
19/21 with context versus 6/21 fragment-only, ambiguous 4/4, no-context
4/4, guarded 6/6, not-emergency 2/2, standalone override 2/3.

## 8. Civic and petition workflows

- **Civic:** report -> (optional photo, metadata stripped) -> deterministic duplicate handling -> authority review through a declared transition table -> server-controlled status history with actor names -> staff priority and SLA deadline -> citizen-visible outcome. Duplicate handling is an exact-resubmission SHA-256 fingerprint enforced by a unique sparse index, plus a nearby-recent-same-category *warning the citizen can override* -- never a refusal of an independent report.
- **Petitions:** create -> moderation -> publish -> sign (one signature per account, unique compound index) -> authority formal response. An ADMIN signature recount implements the documented count-drift recovery.
- **Legal to Learn link:** an answer surfaces the Learn articles and FAQs grounded in the very provisions it cited, via an exact `sourceId:unitNumber` metadata join -- no similarity model, no invented relationship.

Not built, by decision: civic vision/ML, automatic categorisation or
priority prediction, the petition recommendation agent, notifications,
analytics.

## 9. Testing and CI

All verified at the freeze:

| Suite | Result | Command |
| --- | --- | --- |
| Python (AI service) | **369 passed** | `cd services/ai && python -m pytest tests/ -q` |
| API unit (vitest) | **318 passed** | `npm test -w @cap/api` |
| Web unit (vitest) | **278 passed** | `npm test -w @cap/web` |
| Monorepo typecheck | clean | `npm run typecheck` |
| Production build | clean | `npm run build` |
| DB integration (real MongoDB) | CI job | `npm run test:integration -w @cap/api` |
| Compose stack smoke | scheduled CI job | `.github/workflows/integration.yml` |

`.github/workflows/ci.yml` runs typecheck, tests, build and `git diff
--check`, plus the MongoDB integration job and the Python suite, on every
push and pull request. The retrieval evaluation is deliberately **not**
in CI: it is an offline research workflow, not a per-commit check.

The Compose-stack workflow builds all images and asserts the live legal
path end to end (an in-domain question returns cited excerpts with a
disclaimer; an out-of-domain question abstains).

## 10. Known limitations

- **Coverage is partial.** 10 Acts. POCSO, motor vehicles, matrimonial law, SC/ST atrocities and court fees/CPC are not ingested and are named by the corpus-coverage guard, which abstains on them *before retrieval* rather than answering from an adjacent Act. Labour/workplace, tenancy, data protection, stamp duty and arbitration are also not ingested but carry no guard rule: a probe confirmed the confidence gate already abstains on them correctly, and the guard deliberately carries one entry per demonstrated failure rather than a list of every Indian Act. See `docs/LEGAL_SOURCES.md`.
- **RTI is ingested from a pre-2019 copy.** ss.13, 16 and 27 (replaced by the RTI (Amendment) Act 2019) are excluded rather than served as current law; s.25 is excluded for measured retrieval harm; no RTI fee figure is stated anywhere, because the Act leaves it to rules that are not ingested.
- **Four sections across two sources** (BNS 217/255, JJ Act 61/86) merge into the preceding chunk because of a source-PDF layout quirk -- a citation-accuracy defect for those four, not content loss.
- **One residual retrieval preference:** "can an officer be penalized for not providing information" ranks `it_act:44` above `rti:20`. Both are genuine penalty-for-not-furnishing-information provisions and the query names no Act; the RTI section stays in the window the citizen sees.
- **Rate limiting is in-process** (single API instance). `REDIS_URL` is validated but nothing connects to Redis.
- **Media is served from disk**, not streamed; email verification requires a configured `SMTP_URL` (production self-registration answers 503 rather than issuing a challenge nobody can receive).
- **English only.** The service boundary keeps multilingual expansion isolated, but nothing multilingual is built.

Every gap, including the ones closed and why, is enumerated in
`docs/PROJECT_STATE.md`.

## 11. Local development

**Prerequisites:** Node.js 20+ and npm 10+, Docker Desktop, Python 3.11+.

```bash
# 1. JavaScript
npm install
docker compose up -d mongo redis
npm run dev:api            # http://localhost:4000
npm run dev:web            # http://localhost:5173
npm run seed -w @cap/api   # demo accounts; refuses to run under NODE_ENV=production

# 2. AI service (from services/ai/)
pip install -r requirements-full.txt        # hybrid; requirements.txt alone = BM25-only
export DENSE_EMBEDDING_MODEL=data/models/m12_run2
python scripts/ingest_corpus.py             # builds bm25.pkl + dense_vectors.npy
uvicorn app.main:app --reload --port 8000
```

Or bring the whole stack up with `docker compose up`.

**Adding or updating a source:** drop `raw.txt` (or `raw.pdf`, extracted
automatically on first ingest) into
`services/ai/data/legal-corpus/<source_id>/`, register `source_id` in
`app/ingestion/sources.py`'s `APPROVED_SOURCES` if it is new, and re-run
`python scripts/ingest_corpus.py`. No retrieval code changes.

**Re-running the evaluation** after any corpus, retrieval or model
change:

```bash
cd services/ai
python eval/run_eval.py --production-path --mode hybrid           # control 46
python eval/run_eval.py --production-path --mode hybrid --human   # citizen 281
python eval/run_context_eval.py                                   # 40-row follow-up benchmark
```

**Optional environment variables:** `RETRIEVAL_MODE`
(`bm25` | `dense` | `hybrid`, default auto) and `LEGAL_CHAT_MIN_SCORE`
(overrides the confidence floor for the active mode; per-mode defaults
live in `services/ai/app/generation/pipeline.py`).

## 12. Deployment

The AI service loads its embedding model from **`DENSE_EMBEDDING_MODEL`**,
whose production value is `data/models/m12_run2` -- a
*service-root-relative* path. `embeddings.resolve_model_path()` resolves
it against the service root at load time only, so the same
`index_manifest.json` works on the host (any CWD) and inside the
container, where `docker-compose.yml` mounts `./services/ai/data` at
`/app/data` read-only.

**The system does not depend on an accidental untracked artifact.** The
model directory is gitignored under the same policy as the index: both
are build artifacts, both are reproduced deterministically by seeded
scripts in this repository (`finetune/train.py` and
`scripts/ingest_corpus.py`), and the exact expected hashes are recorded
in `docs/RETRIEVAL_EVALUATION.md`'s M13 section. A ~90 MB model binary is
deliberately not committed.

At query time the service always follows what `index_manifest.json`
records -- the model that actually built the mounted index -- so a
running service can never encode queries with a different model than the
index was built with. Changing the model is therefore: set the variable,
re-run `scripts/ingest_corpus.py`, restart. **No image rebuild is
required** for a model or index change, because `data/` is mounted rather
than baked in.

Required for a real deployment: a generated `JWT_SECRET` (the API refuses
to boot in production with the placeholder), a non-wildcard `WEB_ORIGIN`,
`MONGODB_URI`, `AI_SERVICE_URL`, and `SMTP_URL` if self-registration is
enabled. See `.env.example`.

## Local demo accounts

**Development only.** Created by `npm run seed -w @cap/api`, which
refuses to run when `NODE_ENV=production`. All are pre-verified and have
accepted the current legal-information disclaimer. Never seed them into a
deployed environment.

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@cap.local` | `CAPAdmin!2026` |
| Authority | `authority@cap.local` | `CAPAuthority!2026` |
| Citizen | `shreshtha.bindal26@nmims.in` | `CapStone@22!` |
| Citizen (test) | `user@test.com` | `CapStone@22!` |

Replace these credentials and the JWT secret before any non-local
deployment. The API enforces the second half of that: under
`NODE_ENV=production` it refuses to start while `JWT_SECRET` is still the
development placeholder.

## Safety and source policy

- The Legal Assistant answers only from retrieved, approved official sources, and attaches citations with a verification date.
- If evidence is missing, relevance is low, or the question seeks personalised legal advice, it abstains and redirects to appropriate official support.
- High-risk situations (active crime, violence, harassment, domestic violence, child safety, self-harm, medical emergency, cyber financial fraud) never reach retrieval; only official national numbers (112, 181, 1098, 1930) are named, as fixed configuration data.
- Only Admins may access retained unblurred source images. User-facing and Authority views use privacy-masked derivatives.

---

**Documentation:** [PROJECT_STATE](docs/PROJECT_STATE.md) (authoritative
current state and history), [ARCHITECTURE](docs/ARCHITECTURE.md),
[RETRIEVAL_EVALUATION](docs/RETRIEVAL_EVALUATION.md),
[LEGAL_SOURCES](docs/LEGAL_SOURCES.md)
