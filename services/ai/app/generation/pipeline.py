"""Deterministic legal-answer pipeline -- no generative LLM.

Flow:
    question
        -> Risk/UPL check (app.safety.risk), deterministic rules
        -> topic-relevance guard (app.safety.topic_relevance)
        -> corpus-coverage guard (app.safety.corpus_coverage)
        -> app.retrieval.search (retrieval-only)
        -> confidence gate
        -> LegalAnswer built directly from the retrieved chunks

Standing project decision: the legal-answer path never uses a
generative LLM to produce an answer, to eliminate hallucination risk
(see docs/PROJECT_STATE.md). Every excerpt in a LegalAnswer is the
verbatim retrieved chunk text with its real citation -- nothing here
invents, paraphrases, or infers legal content. Multiple sources are
returned as multiple separate excerpts rather than merged into one
synthesized paragraph, so conflicting or overlapping evidence is
preserved by construction, not by special-case "conflict" logic.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from ..query.context import CLARIFICATION_MESSAGE, ConversationContext, resolve_context
from ..query.normalize import normalize_for_retrieval
from ..retrieval.search import search as _search
from ..safety.corpus_coverage import classify_coverage_gap, coverage_message
from ..safety.risk import (
    SEVERITY_EMERGENCY,
    SEVERITY_HARMFUL_REQUEST,
    SEVERITY_NORMAL,
    SEVERITY_SERIOUS,
    assess_query,
)
from ..safety.topic_relevance import OUT_OF_DOMAIN_MESSAGE, classify_topic
from .context import distinct_sources

ABSTENTION_MESSAGE = "No verified information found."

# Provisional, documented floors -- NOT a validated relevance measure.
# Empirical testing against the built index showed off-topic queries can
# score higher than genuine low-coverage topic queries with this corpus's
# unfiltered BM25 tokenization (e.g. "pizza toppings in mumbai" outscored
# "bail"), so no defensible cutoff exists in the data. These floors only
# catch degenerate near-zero matches. Override via LEGAL_CHAT_MIN_SCORE
# (applies to whichever mode is actually in effect for the top result).
#
# BM25 and dense-cosine scores are on entirely different scales --
# BM25 is an unbounded corpus-relative lexical score, cosine similarity
# is bounded in [-1, 1] -- so a single global threshold would be
# meaningless for one or the other. Values below were chosen by
# sweeping thresholds against eval/queries.jsonl's labeled
# answer/abstain queries (see docs/RETRIEVAL_EVALUATION.md) and picking
# the point that eliminates outright wrong-topic top hits while still
# answering most genuinely-covered queries -- not a perfect separator
# (none exists on this corpus/query set), but a measured one.
DEFAULT_MIN_SCORE_BY_MODE = {
    "bm25": 3.0,
    "dense": 0.45,
    # 0.42, raised from 0.40 after the corpus expansion to BNS/BNSS/BSA/
    # CPA2019/JJ Act full text (1,783 chunks, up from ~430): a stress
    # test of clearly out-of-domain queries ("How do I register a
    # company in India?", "What is the income tax slab?", "How do I get
    # a driving licence?") found dense scores 0.41-0.45 on the larger
    # corpus -- topically-adjacent-word false positives (e.g. "company"
    # also appears in a BNSS summons-service section) that would have
    # answered confidently from the wrong Act. Checked against
    # eval/queries.jsonl's full set of genuine (non-abstain) queries:
    # every one still clears 0.42 except q19, which already failed at
    # 0.40 too (a separate, pre-existing paraphrase-calibration gap --
    # see docs/RETRIEVAL_EVALUATION.md). 0.42 does not fully separate
    # every out-of-domain false positive from genuine queries (a
    # residual gap remains for "income tax slab" / "driving licence"
    # specifically, both ~0.45) -- closing that fully would cost real
    # recall (q20 sits at 0.4531) and likely needs a smarter signal
    # than a single global threshold, not a further blanket raise.
    # 0.41, lowered from 0.42 in M12 after the production-path measurement
    # the raw-query sweeps could never see: the gate reads the dense score
    # of the NORMALISED text (handle_legal_query retrieves on
    # app.query.normalize's output), and on that path the highest score
    # any should-abstain query in the 362-row labelled pool reaches is
    # 0.399 -- the 0.42 floor was calibrated against raw-query scores.
    # Swept on a tune split (control + odd citizen rows) and validated on
    # held-out even citizen rows: 0.41 recovers gold-top-1 answers with
    # ZERO new false accepts and ZERO wrong-Act change on both splits.
    # The old 0.4117 company-registration stress case is now caught by
    # the topic-relevance guard before the gate (test_pipeline pins the
    # end-to-end behaviour). A deeper cut was measured and REJECTED: an
    # agreement branch (BM25 and dense both ranking the same top hit
    # <=2, dense >= 0.30) bought 5 good answers at 2 new wrong-Act
    # answers -- both retrieval methods can agree on the same wrong
    # chunk, so cross-method agreement is not the safety signal it looks
    # like. Do not re-propose it without a feature that separates
    # agreeing-right from agreeing-wrong.
    "hybrid": 0.41,  # gates on the top hit's dense_score, not its RRF score -- see _passes_confidence_gate
}
DEFAULT_MIN_SCORE = DEFAULT_MIN_SCORE_BY_MODE["bm25"]  # kept for direct build_legal_answer() callers/tests


def _min_score(mode: str = "bm25") -> float:
    raw = os.environ.get("LEGAL_CHAT_MIN_SCORE")
    if raw is not None:
        try:
            return float(raw)
        except ValueError:
            pass
    return DEFAULT_MIN_SCORE_BY_MODE.get(mode, DEFAULT_MIN_SCORE)


@dataclass
class Excerpt:
    chunk_id: str
    text: str
    citation: dict
    coverage_note: str


@dataclass
class LegalAnswer:
    excerpts: list[Excerpt] = field(default_factory=list)
    # Set for abstention/redirect cases, and also alongside excerpts on a
    # serious-matter response, where the caution comes first and the
    # retrieved law follows it.
    message: str | None = None
    abstained: bool = False
    reason: str | None = None
    # "answered" | "abstained" | "redirect_emergency" | "redirect_adviser" | "refused"
    policy_decision: str = "answered"
    sources: list[str] = field(default_factory=list)
    # Safety severity from app.safety.risk: "normal" | "serious" |
    # "emergency" | "harmful_request". Carried through to the API so the
    # frontend can frame the response without parsing its text.
    severity: str = SEVERITY_NORMAL
    # True when the response points at an authority, helpline or legal-aid
    # service rather than at legal text alone.
    authority_guidance: bool = False
    # Multi-turn context (app.query.context): True when the previous
    # question was deterministically folded into the retrieval text, and
    # the exact combined text used -- shown to the user so nothing is
    # interpreted invisibly.
    context_applied: bool = False
    resolved_question: str | None = None


def _passes_confidence_gate(results: list[dict]) -> bool:
    """Reciprocal Rank Fusion's score is a sum of 1/(k+rank) terms, so it
    reflects a chunk's *relative* rank position within a small candidate
    pool, not its *absolute* relevance -- on this corpus it compresses
    into a narrow band (~0.027-0.033) for the single top hit regardless
    of whether the query is genuinely covered (see
    docs/RETRIEVAL_EVALUATION.md), which makes it useless as a
    confidence-gate signal. Gating hybrid mode on the top hit's
    dense_score (bounded, and empirically the best-separated signal
    available) instead of its fused "score" avoids that trap. bm25 and
    dense modes gate on their own native score as before.
    """
    if not results:
        return False
    top = results[0]
    mode = top.get("retrieval_mode", "bm25")
    if mode == "hybrid":
        gate_score = top.get("dense_score")
        if gate_score is None:
            gate_score = top["score"]
    else:
        gate_score = top["score"]
    return gate_score >= _min_score(mode)


def build_legal_answer(results: list[dict]) -> LegalAnswer:
    """Build a deterministic answer directly from already-retrieved results.

    `results` must already be retrieved (via app.retrieval.search) and
    Risk/UPL-cleared by the caller -- this function only handles the
    confidence gate and response assembly.
    """
    if not results:
        return LegalAnswer(
            message=ABSTENTION_MESSAGE, abstained=True, reason="no_matching_content", policy_decision="abstained"
        )

    if not _passes_confidence_gate(results):
        return LegalAnswer(
            message=ABSTENTION_MESSAGE, abstained=True, reason="insufficient_evidence", policy_decision="abstained"
        )

    excerpts = [
        Excerpt(chunk_id=r["chunk_id"], text=r["text"], citation=r["citation"], coverage_note=r["coverage_note"])
        for r in results
    ]
    return LegalAnswer(excerpts=excerpts, sources=sorted(distinct_sources(results)), policy_decision="answered")


def handle_legal_query(
    question: str, top_k: int = 5, context: ConversationContext | None = None
) -> LegalAnswer:
    """Full Module 1 entry point: safety policy -> topic guard ->
    corpus-coverage guard -> retrieval -> deterministic answer.

    The safety policy (app.safety.risk.assess_query) runs first and
    decides one of four severities:

    ``harmful_request``
        A request to be shown how to destroy evidence, fabricate an
        alibi, interfere with a witness or evade an investigation.
        Refused outright; no retrieval happens.

    ``emergency``
        A life-threatening situation the person presents as real and
        current. Returns the relevant official helpline immediately, with
        no legal analysis in front of it -- a long explanation is the
        wrong response when someone is in danger. No retrieval happens.

    ``serious``
        A real legal matter affecting the person directly (a live
        accusation, an interrogation, an imminent arrest). Retrieval
        *does* run: the caution goes first, and the general law on the
        topic follows it behind the same confidence gate as any other
        query. What is withheld is personalised procedural coaching, not
        the text of the law -- someone facing an accusation is entitled
        to read the provision that governs it. The response is marked
        ``redirect_adviser`` with ``authority_guidance`` set, so the
        frontend leads with the caution rather than the excerpts.

    ``normal``
        Straight through to the guards below, unchanged.

    The topic-relevance guard runs next: a query matching a known
    out-of-domain subject (see app.safety.topic_relevance) is rejected
    before spending a retrieval call on it, since no score from that
    retrieval could be trusted as a real confidence signal for a topic
    this corpus was never meant to answer.

    The corpus-coverage guard runs third and handles the harder case the
    313-query evaluation exposed: a query that genuinely *is* a legal
    question in this service's subject area, but names an Act the corpus
    does not contain (POCSO, Motor Vehicles, matrimonial law, SC/ST
    Atrocities, RTI, Court Fees). Those share real legal vocabulary with
    real legal content, so they clear the dense-score floor and get
    answered confidently from the wrong Act -- see
    app.safety.corpus_coverage for the measured failures and the
    deliberately narrow scope. It runs before retrieval for the same
    reason the topic guard does, and returns a different message,
    because "try a government services portal" is the wrong advice for
    someone asking a real legal question.

    Citizen-language normalisation (app.query.normalize) runs last, after
    every gate has inspected the raw question, and rewrites only the text
    passed to retrieval -- appending statutory vocabulary so a question
    phrased in ordinary words can reach the provision it is about. It
    cannot influence safety, abstention, citations or the answer text.

    Nothing below changes retrieval, its thresholds, or the abstention
    logic. The safety layer only decides whether retrieval runs at all
    and how its result is framed.
    """
    assessment = assess_query(question)

    if assessment.severity == SEVERITY_HARMFUL_REQUEST:
        return LegalAnswer(
            message=assessment.message,
            abstained=True,
            reason=f"harmful_request_{assessment.category}",
            policy_decision="refused",
            severity=assessment.severity,
            authority_guidance=assessment.authority_guidance,
        )

    if assessment.severity == SEVERITY_EMERGENCY:
        return LegalAnswer(
            message=assessment.message,
            abstained=True,
            reason=f"risk_{assessment.category}",
            policy_decision="redirect_emergency",
            severity=assessment.severity,
            authority_guidance=assessment.authority_guidance,
        )

    # Multi-turn context (app.query.context). A standalone question passes
    # through untouched -- context never overrides explicit new intent. A
    # follow-up that cannot be resolved safely asks for a restatement
    # rather than guessing what it refers to.
    resolution = resolve_context(question, context)
    if resolution.needs_clarification:
        return LegalAnswer(
            message=CLARIFICATION_MESSAGE,
            abstained=True,
            reason="needs_context",
            policy_decision="abstained",
            severity=assessment.severity,
        )

    effective_question = resolution.retrieval_question

    # When the previous question was folded in, the combined text is the
    # question actually being answered -- and the context is
    # client-supplied, therefore untrusted. Every deterministic guard
    # re-runs against the combined text, and the stricter outcome wins,
    # so context can never carry retrieval past a safety decision (e.g. a
    # first turn about divorce, correctly refused by the coverage guard,
    # cannot be reached via an innocuous-looking follow-up).
    if resolution.context_applied:
        combined_assessment = assess_query(effective_question)
        if combined_assessment.severity == SEVERITY_HARMFUL_REQUEST:
            return LegalAnswer(
                message=combined_assessment.message,
                abstained=True,
                reason=f"harmful_request_{combined_assessment.category}",
                policy_decision="refused",
                severity=combined_assessment.severity,
                authority_guidance=combined_assessment.authority_guidance,
            )
        if combined_assessment.severity == SEVERITY_EMERGENCY:
            return LegalAnswer(
                message=combined_assessment.message,
                abstained=True,
                reason=f"risk_{combined_assessment.category}",
                policy_decision="redirect_emergency",
                severity=combined_assessment.severity,
                authority_guidance=combined_assessment.authority_guidance,
            )
        if combined_assessment.severity == SEVERITY_SERIOUS and assessment.severity == SEVERITY_NORMAL:
            assessment = combined_assessment

    topic_category = classify_topic(question)
    if topic_category is None and resolution.context_applied:
        topic_category = classify_topic(effective_question)
    if topic_category is not None:
        return LegalAnswer(
            message=OUT_OF_DOMAIN_MESSAGE,
            abstained=True,
            reason=f"out_of_domain_{topic_category}",
            policy_decision="abstained",
            severity=assessment.severity,
            context_applied=resolution.context_applied,
            resolved_question=effective_question if resolution.context_applied else None,
        )

    coverage_category = classify_coverage_gap(question)
    if coverage_category is None and resolution.context_applied:
        coverage_category = classify_coverage_gap(effective_question)
    if coverage_category is not None:
        return LegalAnswer(
            message=coverage_message(coverage_category),
            abstained=True,
            reason=f"not_in_corpus_{coverage_category}",
            policy_decision="abstained",
            severity=assessment.severity,
            context_applied=resolution.context_applied,
            resolved_question=effective_question if resolution.context_applied else None,
        )

    # Citizen-language normalisation, applied to the retrieval text only.
    #
    # Placement matters and is deliberate. The safety policy above and both
    # guards have already run against the *raw* question, so nothing this
    # appends can talk retrieval past a safety decision or past an
    # abstention -- and the guards keep the exact behaviour their measured
    # baseline was established with. From here the raw question is no
    # longer needed: `build_legal_answer` assembles the response from the
    # retrieved chunks themselves, so the normalised text cannot reach the
    # answer, the citations, or the user.
    results = _search(normalize_for_retrieval(effective_question), top_k=top_k)
    answer = build_legal_answer(results)
    answer.context_applied = resolution.context_applied
    answer.resolved_question = effective_question if resolution.context_applied else None

    if assessment.severity == SEVERITY_SERIOUS:
        return _as_serious_matter(answer, assessment)
    return answer


def _as_serious_matter(answer: LegalAnswer, assessment) -> LegalAnswer:
    """Reframe a retrieved answer as a cautious serious-matter response.

    The excerpts and the confidence gate's verdict are left exactly as
    retrieval produced them -- this only replaces the framing, so the
    caution and the legal-aid route lead, and any law that did clear the
    gate follows as supporting context rather than as an answer to
    "what should I do".
    """
    answer.message = assessment.message
    answer.policy_decision = "redirect_adviser"
    answer.severity = assessment.severity
    answer.authority_guidance = assessment.authority_guidance
    answer.reason = "serious_legal_matter" if answer.excerpts else (answer.reason or "serious_legal_matter")
    # `abstained` stays true when nothing cleared the gate, so a caller
    # can still tell "caution plus law" apart from "caution alone".
    return answer
