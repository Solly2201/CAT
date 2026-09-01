import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .generation.disclaimer import DISCLAIMER_TEXT, DISCLAIMER_VERSION
from .generation.pipeline import handle_legal_query
from .ingestion.sources import APPROVED_SOURCES
from .query.context import ConversationContext
from .retrieval.search import get_section, search

logger = logging.getLogger("cap-ai")

# Set once the embedding model and index are resident, so /health can say
# whether the first real query will be fast or will pay the load cost.
_warm = {"ready": False, "seconds": None, "error": None}


def _warm_up() -> None:
    """Load the embedding model and the index before serving traffic.

    Measured on this corpus, a cold first query costs ~15.4s, of which
    ~12.1s is the sentence-transformer load; BM25 (23ms) and the dense
    vectors (4ms) are negligible, and a warm query is ~31ms. Left alone
    that entire cost lands on whichever citizen asks the first question
    after a deploy.

    This changes *when* the model is loaded, never *what* is loaded or how
    it is used -- no retrieval parameter, threshold, index or ranking
    behaviour is touched. The existing process-lifetime caches in
    app.retrieval.search are what make it stick; this only populates them
    early by issuing one throwaway query.

    A failure here is logged and recorded rather than raised. The service
    still starts, /corpus/* and the non-dense paths keep working, and the
    first real query retries the load and surfaces the error the way it
    always did -- so a missing index or an offline model cache degrades
    the service instead of preventing it from booting.
    """
    started = time.perf_counter()
    try:
        search("warm up", top_k=1)
        _warm["ready"] = True
        _warm["seconds"] = round(time.perf_counter() - started, 3)
        logger.info("AI warm-up complete in %.3fs", _warm["seconds"])
    except Exception as exc:  # noqa: BLE001 - startup must not be fatal
        _warm["error"] = f"{type(exc).__name__}: {exc}"
        logger.warning("AI warm-up failed (%s); first query will load on demand", _warm["error"])


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Opt-out for tests and for any environment that wants a fast boot;
    # the tests monkeypatch retrieval and must not pay for a model load.
    if os.environ.get("AI_SKIP_WARMUP", "").lower() not in ("1", "true", "yes"):
        _warm_up()
    yield


app = FastAPI(
    title="CAP AI Service",
    version="0.1.0",
    description="Service boundary for CAP's later RAG, vision, safety and evaluation pipelines.",
    lifespan=lifespan,
)


class ReadinessResponse(BaseModel):
    status: str
    service: str
    enabled_capabilities: list[str]
    #: Whether the embedding model and index are already resident. False
    #: means the next query pays the load cost rather than that the
    #: service is broken.
    retrieval_warm: bool = False
    warmup_seconds: float | None = None
    warmup_error: str | None = None


@app.get("/health", response_model=ReadinessResponse)
def health_check() -> ReadinessResponse:
    return ReadinessResponse(
        status="ok",
        service="cap-ai",
        enabled_capabilities=[
            "service-boundary",
            "corpus-ingestion",
            "corpus-retrieval",
            "legal-answer",
        ],
        retrieval_warm=_warm["ready"],
        warmup_seconds=_warm["seconds"],
        warmup_error=_warm["error"],
    )


# --- Module 1A: legal corpus browser -----------------------------------
# Retrieval only. No LLM generation happens anywhere in this service --
# see the standing "no generative LLM in the legal-answer pipeline"
# decision in docs/PROJECT_STATE.md. Module 1B (below) wraps this same
# retrieval layer with Risk/UPL and a confidence gate; it never adds
# generation on top of it.

class SourceSummary(BaseModel):
    source_id: str
    display_name: str
    act_no: str
    official_url: str
    as_on_date: str
    coverage_note: str
    unit_label: str


@app.get("/corpus/sources", response_model=list[SourceSummary])
def list_sources() -> list[SourceSummary]:
    return [
        SourceSummary(
            source_id=s.source_id,
            display_name=s.display_name,
            act_no=s.act_no,
            official_url=s.official_url,
            as_on_date=s.as_on_date,
            coverage_note=s.coverage_note,
            unit_label=s.unit_label,
        )
        for s in APPROVED_SOURCES.values()
    ]


class SearchResult(BaseModel):
    chunk_id: str
    score: float
    text: str
    title: str
    citation: dict
    coverage_note: str


@app.get("/corpus/search", response_model=list[SearchResult])
def search_corpus(
    q: str = Query(..., min_length=2, description="Search text"),
    source: str | None = Query(default=None, description="Restrict to one source_id"),
    top_k: int = Query(default=5, ge=1, le=20),
) -> list[SearchResult]:
    if source is not None and source not in APPROVED_SOURCES:
        raise HTTPException(status_code=400, detail=f"Unknown source '{source}'")
    try:
        results = search(q, top_k=top_k, source_id=source)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return [SearchResult(**r) for r in results]


class SectionDetail(BaseModel):
    chunk_id: str
    text: str
    title: str
    citation: dict
    coverage_note: str


@app.get("/corpus/sections/{source_id}/{unit_number}", response_model=SectionDetail)
def get_section_detail(source_id: str, unit_number: str) -> SectionDetail:
    if source_id not in APPROVED_SOURCES:
        raise HTTPException(status_code=404, detail=f"Unknown source '{source_id}'")
    result = get_section(source_id, unit_number)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"{source_id}:{unit_number} not found -- it may not be ingested yet "
            f"(see coverage_note on /corpus/sources).",
        )
    return SectionDetail(**result)


# --- Module 1B: deterministic legal answers -----------------------------
# Risk/UPL -> retrieval -> confidence gate -> deterministic response, per
# docs/ARCHITECTURE.md. No generative LLM anywhere in this path -- every
# excerpt returned is the verbatim retrieved chunk text with its real
# citation. Public endpoint (no auth) by deliberate v1 decision -- basic
# legal information should not require an account -- so the disclaimer
# is attached to every response rather than relying on account-level
# acceptance at registration.


class LegalQueryContext(BaseModel):
    """The previous exchange, sent back by the client. Untrusted input:
    the pipeline re-runs every deterministic guard over the combined
    text, so context cannot carry retrieval past a safety decision."""

    previous_question: str = Field(..., min_length=2, max_length=2000)


class LegalQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    context: LegalQueryContext | None = None


class LegalExcerpt(BaseModel):
    chunk_id: str
    text: str
    source: str
    act_no: str
    unit: str
    official_url: str
    verified_as_on: str
    coverage_note: str


class LegalAnswerResponse(BaseModel):
    excerpts: list[LegalExcerpt]
    message: str | None
    abstained: bool
    policy_decision: str
    reason: str | None
    sources: list[str]
    disclaimer_version: str
    disclaimer_text: str
    # Structured safety outcome from app.safety.risk, so the frontend can
    # frame a redirect without parsing the message string.
    severity: str
    authority_guidance: bool
    # Multi-turn context: True when the previous question was folded into
    # retrieval, with the exact combined text -- shown to the user so no
    # interpretation happens invisibly.
    context_applied: bool = False
    resolved_question: str | None = None


@app.post("/legal/answer", response_model=LegalAnswerResponse)
def legal_answer(payload: LegalQueryRequest) -> LegalAnswerResponse:
    conversation = (
        ConversationContext(previous_question=payload.context.previous_question)
        if payload.context
        else None
    )
    try:
        result = handle_legal_query(payload.question, context=conversation)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    excerpts = [
        LegalExcerpt(
            chunk_id=e.chunk_id,
            text=e.text,
            source=e.citation["source"],
            act_no=e.citation["act_no"],
            unit=e.citation["unit"],
            official_url=e.citation["official_url"],
            verified_as_on=e.citation["verified_as_on"],
            coverage_note=e.coverage_note,
        )
        for e in result.excerpts
    ]
    return LegalAnswerResponse(
        excerpts=excerpts,
        message=result.message,
        abstained=result.abstained,
        policy_decision=result.policy_decision,
        reason=result.reason,
        sources=result.sources,
        disclaimer_version=DISCLAIMER_VERSION,
        disclaimer_text=DISCLAIMER_TEXT,
        severity=result.severity,
        authority_guidance=result.authority_guidance,
        context_applied=result.context_applied,
        resolved_question=result.resolved_question,
    )
