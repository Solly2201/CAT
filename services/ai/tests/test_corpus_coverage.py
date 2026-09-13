"""Corpus-coverage guard tests: legal questions about un-ingested Acts.

Deterministic pattern matching only -- no LLM, no ML classifier, run
before retrieval, same standing decision as app.safety.risk and
app.safety.topic_relevance (see docs/PROJECT_STATE.md).

This guard is the narrow fix for a measured failure class: the 313-query
citizen-language evaluation found hybrid retrieval answering 5 of 10
`insufficient_evidence` queries confidently from the wrong Act, because a
legal question about an Act the corpus lacks shares real legal
vocabulary with real legal content and clears the dense-score floor.
The tests below lock in both halves of that fix -- it must catch the
demonstrated failures, and it must not block anything the corpus can
actually answer.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.generation.pipeline import handle_legal_query  # noqa: E402
from app.safety.corpus_coverage import (  # noqa: E402
    CASE_LAW_MESSAGE,
    EXCLUDED_PROVISION_MESSAGE,
    NOT_IN_CORPUS_MESSAGE,
    classify_coverage_gap,
)

EVAL_DIR = os.path.join(os.path.dirname(__file__), "..", "eval")
INDEX_MANIFEST = os.path.join(
    os.path.dirname(__file__), "..", "data", "index", "chunk_manifest.jsonl"
)

# A built index is a generated artifact and is gitignored, so a clean
# checkout has the corpus PDFs but no index. CI deliberately does not
# build one either -- its requirements pull the BM25-only dependency
# set, without the sentence-transformer model a hybrid index needs.
#
# Most tests in this file are unaffected, because their queries abstain
# at this guard before retrieval is ever reached. The one that asserts a
# query IS answered genuinely needs a real index, so it skips where none
# has been built rather than failing. (Two other test modules happen to
# build an index in their setup, but they sort after this one, so
# relying on that would be an ordering accident rather than a fixture.)
needs_index = pytest.mark.skipif(
    not os.path.exists(INDEX_MANIFEST),
    reason="no built index (run scripts/ingest_corpus.py); CI does not build one",
)

# --- the exact evaluation failures this guard was built for ---------------
# Each of these was answered confidently from the wrong Act before the
# guard existed; the comment records what it wrongly cited.

MEASURED_WRONG_ACT_FAILURES = [
    ("what is the penalty for drunk driving", "motor_vehicles"),        # was bns:355
    ("how do I get a divorce in india", "matrimonial"),                 # was bnss:219
    ("what does the law against caste-based atrocities cover", "sc_st_atrocities"),  # was constitution:16
    ("what is the punishment under the POCSO act", "pocso"),            # was bns:198
    ("what are the court fees for filing a civil suit", "court_fees_civil_procedure"),  # was bnss:400
]


def test_measured_wrong_act_failures_are_now_caught():
    for text, expected_category in MEASURED_WRONG_ACT_FAILURES:
        assert classify_coverage_gap(text) == expected_category, text


def test_measured_wrong_act_failures_abstain_end_to_end():
    """The guard must actually change pipeline behavior, not just
    classify -- and it must abstain rather than redirect, since these
    are real legal questions, not emergencies or personal-advice asks."""
    for text, expected_category in MEASURED_WRONG_ACT_FAILURES:
        answer = handle_legal_query(text)
        assert answer.abstained is True, text
        assert answer.policy_decision == "abstained", text
        assert answer.reason == f"not_in_corpus_{expected_category}", text
        assert answer.message == NOT_IN_CORPUS_MESSAGE, text
        assert answer.excerpts == [], text


def test_rti_is_no_longer_a_coverage_gap():
    """RTI was the one registered-but-un-ingested source, and this guard
    used to abstain on it. It is now ingested (27 sections), so the guard
    must stand aside and let retrieval answer -- keeping the old rule
    would make the corpus unreachable."""
    for text in (
        "How do I file an RTI application?",
        "what does the right to information act say",
        "how do I get information from a government department",
        "who is a public information officer",
        "can I appeal if my information request is refused",
    ):
        assert classify_coverage_gap(text) is None, text


@needs_index
def test_rti_questions_are_answered_from_the_rti_act():
    """The end-to-end contract: an information-access question must come
    back citing the RTI Act, not a lexically-similar section of BNSS,
    BSA or PWDVA -- the substitution measured before ingestion.

    The officer-penalty phrasing asserts presence-in-window rather than
    strict rank 1, under the same product property the BNSS s.43 test in
    test_retrieval.py documents: every returned excerpt is shown to the
    citizen, never just a single "best" one. Under the promoted
    m12_run2 embedding model (M13, docs/RETRIEVAL_EVALUATION.md) that
    query ranks it_act:44 first (dense 0.508) and rti:20 second (0.469)
    -- IT Act s.44 is itself a genuine penalty-for-not-furnishing-
    information provision and the query names no Act, so demanding
    rank 1 here would pin a preference between two legitimately
    responsive statutes rather than guard against the pre-ingestion
    failure (RTI questions answered from *unrelated* Acts), which the
    strict top-1 assertions on the other four phrasings still cover.
    """
    strict_top1 = (
        "how do I get information from a government department",
        "how long does the government have to reply",
        "can I appeal an information refusal",
        "how do I file an RTI application",
    )
    for text in strict_top1:
        answer = handle_legal_query(text)
        assert not answer.abstained, text
        assert answer.excerpts, text
        assert answer.excerpts[0].chunk_id.startswith("rti:"), (
            f"{text!r} answered from {answer.excerpts[0].chunk_id}"
        )

    text = "can an officer be penalized for not providing information"
    answer = handle_legal_query(text)
    assert not answer.abstained, text
    assert answer.excerpts, text
    assert any(e.chunk_id.startswith("rti:") for e in answer.excerpts), (
        f"{text!r} returned no RTI excerpt at all: "
        f"{[e.chunk_id for e in answer.excerpts]}"
    )


def test_amended_institutional_sections_are_not_served():
    """ss.13, 16 and 27 were replaced by the RTI (Amendment) Act 2019 and
    the ingested copy predates them; s.25 is excluded for measured
    retrieval harm. None may reach the corpus as current law.

    Runs ingestion rather than reading the built index, so it holds on a
    clean checkout and in CI. Chunking is pure text processing and needs
    no embedding model. It is also the stronger assertion: ingestion
    itself refuses to run when an excluded unit is one the chunker never
    produced, so this proves the exclusion is doing real work rather
    than naming sections that were never there.
    """
    from app.ingestion.pipeline import ingest_source, load_chunks
    from app.ingestion.sources import APPROVED_SOURCES

    excluded = set(APPROVED_SOURCES["rti"].exclude_units)
    assert excluded == {"13", "16", "25", "27"}, sorted(excluded)
    assert APPROVED_SOURCES["rti"].exclude_reason.strip(), "an exclusion must state why"

    ingest_source("rti")
    units = {chunk.unit_number for chunk in load_chunks("rti")}
    assert units, "RTI ingestion produced no chunks"
    assert excluded.isdisjoint(units), sorted(excluded & units)
    # The citizen-facing provisions must survive that exclusion.
    for section in ("3", "6", "7", "8", "9", "10", "11", "18", "19", "20"):
        assert section in units, section


# --- must NOT block anything the corpus genuinely answers -----------------
# Every probe below is a near-miss on one of the guard's own patterns and
# maps to real ingested text. These are the cases that made the obvious
# discriminators ("divorce", "drunk", "scheduled caste", "court fee")
# unsafe to match bare -- see app/safety/corpus_coverage.py's docstring.

ANSWERABLE_NEAR_MISSES = [
    # bnss:144 / bnss:146 -- maintenance for a woman who has been divorced
    "can a divorced woman claim maintenance from her husband",
    "what does the law say about a divorced wife's allowance",
    # bns:355 -- misconduct in public by a drunken person
    "punishment for misconduct in public by a drunken person",
    # bns:281 -- rash driving IS in the corpus; only drunk driving is not
    "what is rash driving on a public way",
    # constitution:15 / constitution:16 / lsa:12 -- Scheduled Castes
    "does the constitution prohibit discrimination on grounds of caste",
    "who qualifies for legal services if they are from a scheduled caste",
    # lsa:21 -- court-fee refund on a Lok Adalat award
    "is the court fee refunded when a case is settled in a lok adalat",
    # bsa:126 / bsa:3 -- civil proceedings
    "are husband and wife competent witnesses in civil cases",
    "what evidence is relevant in civil proceedings",
    # bns:63-71 / jj2015 -- child sexual offences ARE partly covered
    "what is the punishment for a sexual offence against a child",
    "what happens to a child in conflict with law",
    # bns:82 -- bigamy, adjacent to but not matrimonial procedure
    "punishment for marrying again during the lifetime of a spouse",
]


def test_answerable_near_misses_are_not_blocked():
    for text in ANSWERABLE_NEAR_MISSES:
        assert classify_coverage_gap(text) is None, text


def test_guard_never_fires_on_a_query_that_expects_an_answer():
    """Scanned across BOTH labelled eval sets (362 query groups). A single
    fire on an expect_abstain=False row is over-blocking and a recall
    regression, so this is asserted rather than spot-checked."""
    over_blocked = []
    for name in ("queries.jsonl", "queries_human.jsonl"):
        path = os.path.join(EVAL_DIR, name)
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row["expect_abstain"]:
                    continue
                if classify_coverage_gap(row["query"]) is not None:
                    over_blocked.append((name, row["id"], row["query"]))
    assert over_blocked == [], f"guard over-blocks answerable queries: {over_blocked}"


def test_guard_falls_through_silently_for_unrecognized_subjects():
    """None means 'no named out-of-corpus subject recognized', NOT
    'covered' -- those queries still go to retrieval and the confidence
    gate. Several un-ingested subjects are deliberately absent from the
    pattern list because the score gate already abstains on them."""
    for text in ("how much stamp duty do I pay to register a sale deed",
                 "can my landlord increase the rent whenever he wants"):
        assert classify_coverage_gap(text) is None, text


def test_minimum_wage_is_caught_after_seed_sweep_evidence():
    """Originally left to the confidence gate (a probe showed the gate
    abstaining). The repeated-seed experiment showed that margin is not
    robust: seed 45 answered this exact query from bns:146 over the
    floor, so the subject moved from gate-reliant to guard-named -- the
    guard's documented "add the rule when evaluation names the case"
    discipline."""
    assert classify_coverage_gap(
        "what is the minimum wage for a construction worker"
    ) == "minimum_wages"


INGESTED_SOURCE_NAMES = [
    "Constitution",
    "Bharatiya Nyaya Sanhita",
    "Bharatiya Nagarik Suraksha Sanhita",
    "Bharatiya Sakshya Adhiniyam",
    "Consumer Protection Act 2019",
    "Juvenile Justice Act 2015",
    "Information Technology Act",
    "Protection of Women from Domestic Violence Act",
    "Legal Services Authorities Act",
]


def test_message_lists_every_ingested_source():
    """The abstention message tells the user exactly what this service
    does hold. If a source is ever added or removed from ingestion, this
    fails and forces the message to be updated rather than silently
    going stale."""
    for name in INGESTED_SOURCE_NAMES:
        assert name in NOT_IN_CORPUS_MESSAGE, name
    assert "indiacode.nic.in" in NOT_IN_CORPUS_MESSAGE


def test_message_does_not_name_the_act_governing_the_question():
    """Anti-fabrication: the guard says what this service lacks, it never
    asserts which Act actually governs the user's question. Stating that
    would be an unsourced legal claim, which is exactly what this
    project's no-generation stance exists to prevent."""
    for act in ("Motor Vehicles Act", "Hindu Marriage Act", "POCSO",
                "Prevention of Atrocities", "Court Fees Act"):
        assert act not in NOT_IN_CORPUS_MESSAGE, act


# --- described, not named: the composed concept rules ---------------------
# The guard's phrase list only catches a query that *names* an
# un-ingested Act. These are the same subjects described in citizen
# language, which a 24-question probe found being answered confidently
# from unrelated Acts. Each pair records the domain it belongs to.

DESCRIBED_OUT_OF_CORPUS = [
    # Prevention of Corruption Act 1988 -- a public servant demanding
    # payment for official work. Still not in the corpus, so still
    # guarded. The right-to-information entries that lived here were
    # removed when the RTI Act was ingested; see the two tests above.
    ("a government officer is demanding a bribe to process my file", "public_corruption"),
    ("how do I complain about a corrupt official", "public_corruption"),
    ("where do I report bribery by a clerk", "public_corruption"),
    ("the clerk wants money to release my certificate", "public_corruption"),
    ("a public servant asked me for a bribe", "public_corruption"),
]


def test_described_out_of_corpus_subjects_are_caught():
    for text, expected_category in DESCRIBED_OUT_OF_CORPUS:
        assert classify_coverage_gap(text) == expected_category, text


def test_described_out_of_corpus_subjects_abstain_end_to_end():
    """As with the named failures, classification alone is not the
    contract -- the pipeline must actually abstain and cite nothing."""
    for text, expected_category in DESCRIBED_OUT_OF_CORPUS:
        answer = handle_legal_query(text)
        assert answer.abstained is True, text
        assert answer.reason == f"not_in_corpus_{expected_category}", text
        assert answer.excerpts == [], text


# --- the bribery that IS in the corpus ------------------------------------
# "bribe" is not a safe bare discriminator: BNS punishes electoral
# bribery and gratification taken to screen an offender, and BSA lets a
# witness's credit be impeached by proof of bribery. Only a public
# servant demanding payment for official work is out of corpus.

COVERED_BRIBERY = [
    "what is the offence of bribery at an election",
    "what is bribery by treating",
    "what happens if a witness is bribed to give evidence",
    "what is the punishment for taking a gratification to screen an offender",
    "is it an offence to accept a gratification to recover stolen property",
]


def test_corpus_covered_bribery_is_not_blocked():
    for text in COVERED_BRIBERY:
        assert classify_coverage_gap(text) is None, text


# --- the record access that IS in the corpus ------------------------------
# BNSS gives the informant a free copy of the FIR and the accused copies
# of the police report, judgments are supplied as certified copies, the
# Constitution and BNSS require grounds of arrest to be communicated, and
# CPA 2019 gives consumers a right to be informed.

COVERED_RECORD_ACCESS = [
    "how do I get a free copy of my FIR",
    "can I get a copy of the police report before my trial",
    "am I entitled to a copy of the judgment against me",
    "must the police tell me the grounds of my arrest",
    "what information must a product label give a consumer",
    "how do I file a consumer complaint",
    "how do I file an FIR",
    "can I inspect the documents filed in my case",
]


def test_corpus_covered_record_access_is_not_blocked():
    for text in COVERED_RECORD_ACCESS:
        assert classify_coverage_gap(text) is None, text


# --- a provision this project holds the Act for, but excluded ----------
# A different kind of gap: the RTI Act IS in the corpus, but ss.13, 16
# and 27 are excluded at ingestion as pre-2019 text. Excluding them left
# tenure and salary questions with no correct answer available, and
# retrieval answered 7 of 8 of them from real, correctly-cited sections
# that do not contain the answer (Definitions, Designation of PIOs,
# Constitution of the Commissions, Removal).

EXCLUDED_PROVISION_QUESTIONS = [
    "how long does an information commissioner serve",
    "what is the term of office of a chief information commissioner",
    "what is the salary of an information commissioner",
    "can an information commissioner be reappointed",
    "what are the conditions of service of a state information commissioner",
    "at what age does an information commissioner retire",
    "who decides the tenure of information commissioners",
    "how many years does a CIC serve",
    "what allowances does a state information commissioner get",
]


@pytest.mark.parametrize("text", EXCLUDED_PROVISION_QUESTIONS)
def test_excluded_service_provisions_are_caught(text):
    assert classify_coverage_gap(text) == "rti_amended_service_provisions", text


@pytest.mark.parametrize("text", EXCLUDED_PROVISION_QUESTIONS)
def test_excluded_service_provisions_say_the_act_is_held(text):
    """The message must not claim the Act is missing -- it is not. It
    has to say which sections are absent and why, or it is simply a
    different false statement."""
    answer = handle_legal_query(text)
    assert answer.abstained is True, text
    assert answer.reason == "not_in_corpus_rti_amended_service_provisions", text
    assert answer.excerpts == [], text
    assert answer.message == EXCLUDED_PROVISION_MESSAGE, text
    assert "I do hold the Right to Information Act" in answer.message
    assert "2019" in answer.message
    assert answer.message != NOT_IN_CORPUS_MESSAGE


COMMISSION_QUESTIONS_THE_CORPUS_ANSWERS = [
    # ss.12/15 constitute the Commissions and cover appointment; s.17 is
    # removal; s.18 is powers and functions; s.19 is appeals. All held.
    "what are the powers of the information commission",
    "who appoints the chief information commissioner",
    "how is the central information commission constituted",
    "how can a state information commissioner be removed",
    "how do I complain to the information commission",
    "can I appeal to the information commission",
    "what is the central information commission",
    "how many information commissioners are there",
    # s.28 (rule-making by a competent authority) is in the corpus, so a
    # rules question has a real answer and is deliberately not guarded.
    "what rules can be made under the rti act",
]


@pytest.mark.parametrize("text", COMMISSION_QUESTIONS_THE_CORPUS_ANSWERS)
def test_commission_questions_the_corpus_answers_are_not_blocked(text):
    """The guard keys on service *terms*, never on the Commissioner
    concept alone -- otherwise it would swallow everything the Act does
    say about the Commissions."""
    assert classify_coverage_gap(text) is None, text


# --- case-law requests: no judgment of any court is ingested --------------
# Added for the ICCSDI 2026 revision after a citation-audit probe
# ("supreme court judgment on privacy") was answered with five statutory
# excerpts -- correct citations, wrong kind of law. The corpus is
# statute-only by design, and a judgment request must say so rather than
# look responsive with a statute.

CASE_LAW_REQUESTS = [
    "supreme court judgment on privacy",
    "what did the supreme court rule about aadhaar",
    "landmark judgments on freedom of speech",
    "is there any case law on dowry harassment",
    "high court ruling on bail conditions",
    "what precedent applies to my situation",
]

# Bare "judgment" is genuine statutory vocabulary (BNSS judgment
# pronouncement, Article 137 review of judgments) and must keep
# answering -- the guard requires the case-law framing itself.
JUDGMENT_QUESTIONS_THE_CORPUS_ANSWERS = [
    "when is judgment pronounced in a criminal trial",
    "can the supreme court review its own judgment",
    "can I get a certified copy of the judgment in my case",
    "what happens after the court delivers its judgment",
]


@pytest.mark.parametrize("text", CASE_LAW_REQUESTS)
def test_case_law_requests_are_caught(text):
    assert classify_coverage_gap(text) == "case_law", text


def test_case_law_request_abstains_end_to_end_with_its_own_message():
    answer = handle_legal_query("supreme court judgment on privacy")
    assert answer.abstained
    assert answer.reason == "not_in_corpus_case_law"
    assert answer.message == CASE_LAW_MESSAGE
    assert not answer.excerpts


@pytest.mark.parametrize("text", JUDGMENT_QUESTIONS_THE_CORPUS_ANSWERS)
def test_statutory_judgment_questions_are_not_blocked(text):
    assert classify_coverage_gap(text) is None, text
