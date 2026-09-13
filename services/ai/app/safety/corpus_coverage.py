"""Deterministic guard for legal topics this corpus does not contain.

Runs BEFORE retrieval in `app.generation.pipeline.handle_legal_query`,
immediately after `app.safety.topic_relevance`. Rule-based only, by
design -- no ML/LLM classifier, matching this project's standing
decision that the legal-answer pipeline never uses generation and that
gating stays deterministic (see docs/PROJECT_STATE.md).

Why this is a separate guard from `topic_relevance.py`
------------------------------------------------------
`topic_relevance.py` answers "is this a legal question at all?" and
redirects non-legal subjects (income tax filing, driving licences,
recipes) to a government-services portal. This module answers a
different question: "this *is* a legal question, in this service's own
subject area -- but is the Act it asks about actually in the corpus?"
The two need different user-facing messages. Telling someone with a
POCSO question to try india.gov.in would be unhelpful and slightly
insulting; telling them plainly that this service only holds ten
specific India Code sources, and that theirs is not one of them, is
honest and actionable.

The gap this closes
-------------------
The 313-query citizen-language evaluation added an
`insufficient_evidence` category: legal questions about Acts the corpus
genuinely does not contain. Hybrid retrieval abstained correctly on
20/22 non-legal `out_of_domain` queries but on only 5/10 of these,
because a legal question about an un-ingested Act shares real legal
vocabulary with real legal content and therefore lands in the same
dense-score band as a genuine match. A bounded score cannot separate
"the right Act, weakly matched" from "the wrong Act, strongly matched on
shared legal vocabulary" -- the identical reasoning that produced
`topic_relevance.py`, one level harder. Measured failures this guard
exists to fix (each answered confidently from the wrong Act):

| Query | Was answered from | Actually governed by |
| --- | --- | --- |
| "what is the penalty for drunk driving" | `bns:355` (misconduct in public by a drunken person) | Motor Vehicles Act |
| "how do I get a divorce in india" | `bnss:219` (prosecution for offences against marriage) | matrimonial law |
| "what does the law against caste-based atrocities cover" | `constitution:16` (equality of opportunity) | SC/ST (Prevention of Atrocities) Act |
| "what is the punishment under the POCSO act" | `bns:198` (public servant disobeying law) | POCSO |
| "what are the court fees for filing a civil suit" | `bnss:400` (costs in non-cognizable cases) | Court Fees Act / CPC |

Named subjects versus described subjects
----------------------------------------
The table above is handled by `_CATEGORY_PATTERNS`: the query *names*
the un-ingested Act or its distinctive subject, so one phrase catches
it. An earlier revision of this docstring recorded the harder case as
unclosable without a semantic classifier:

    A query that describes an un-ingested Act's subject *without naming
    it* cannot be caught by a phrase guard at all.

That was measured and found wrong, and `_COMPOSED_RULES` now closes it.
A 24-question probe of out-of-corpus subjects showed 14 answered
confidently from unrelated Acts, all in two domains where citizens
almost never use the statutory name:

| Query | Was answered from | Actually governed by |
| --- | --- | --- |
| "how do I get information from a government department" | `bsa:` unpublished official records | RTI Act 2005 |
| "who is a public information officer" | BNSS / BSA | RTI Act 2005 |
| "can I appeal if my information request is refused" | BNSS / CPA 2019 | RTI Act 2005 |
| "a government officer is demanding a bribe to process my file" | BNSS police investigation / PWDVA | Prevention of Corruption Act 1988 |
| "where do I report bribery by a clerk" | BNSS / BNS / BSA | Prevention of Corruption Act 1988 |

The `bsa` answer is the reason this mattered enough to fix: the section
on *unpublished official records* tells a citizen they cannot obtain
official records, which is the exact opposite of the entitlement they
were asking about.

The evaluation set's own `h286` -- "how do I file an application for
information from a government office", written specifically so that it
"cannot be matched lexically" -- was the single remaining `false_answer`
on the 313-query citizen-language set at the time, and now abstains.

What makes these catchable deterministically is that neither domain is
identified by a single word -- "information", "officer", "records" and
"money" are all ordinary corpus vocabulary -- but each is identified
reliably by a *co-occurrence of concepts*: an access verb applied to an
administrative record held by a government body; or an illicit payment
attached to a public official. That is the same SUBJECT x FRAME
composition `app/safety/risk.py` already uses to grade severity without
a keyword blacklist, applied to coverage instead of severity. No model,
no embedding, no threshold -- every decision traces to a named concept
group and is reportable as one.

Scope discipline
----------------
This is emphatically NOT a list of every Indian Act. It carries one
entry per *demonstrated* evaluation failure, and nothing else. Several
other un-ingested subjects in the same eval category (rent control,
minimum wages, stamp duty, arbitration, labour notice periods) are
deliberately absent: the confidence gate already abstains correctly on
them, so adding patterns would be speculative rather than
evidence-driven. The same probe re-confirmed this -- all seven labour
and civic-service questions in it abstained correctly with no guard at
all, so no labour or municipal-services rule was written. If a future
confidence-threshold change turns any of them into a false answer, add
it then -- same "curated dict, extend only when evaluation names a
specific gap" rule as `topic_relevance.py`, `query_expand.py`'s
abbreviation dict, and `chunk.py`'s `_KNOWN_ARTICLE_TITLES`.

Every pattern below was checked against the actual indexed corpus text
before being added, because several obvious-looking discriminators are
unsafe:

- bare "divorce" appears in `bnss:144`/`bnss:146` (maintenance for a
  divorced woman), `bsa:44` and `jj2015:45` -- all genuinely answerable,
  so only divorce *procedure* phrasings are matched.
- bare "drunk" is the literal subject of `bns:303`'s neighbour
  `bns:355` ("Misconduct in public by a drunken person"), so only
  drunk-*driving* phrasings are matched.
- bare "scheduled caste" appears in `constitution:15`, `constitution:16`,
  `constitution:46` and `lsa:12`, so the SC/ST entry keys off
  "atrocities" (zero occurrences anywhere in the corpus) and the Act's
  own name instead.
- bare "court fee" appears in `lsa:21` (court-fee refund on a Lok Adalat
  award), which is a real answerable question, so only
  filing-cost phrasings are matched.
- bare "bribe" is **in the corpus four times and answerably so**: BNS
  punishes electoral bribery (gratification to induce an electoral
  right, including "bribery by treating"), BNS punishes taking
  gratification to screen an offender or to help recover stolen
  property, and BSA lets a witness's credit be impeached by proof of
  bribery. What is absent is the citizen's actual question -- a public
  servant demanding payment to do their job, which the Prevention of
  Corruption Act 1988 governs. The corruption rule therefore requires a
  public-official concept *and* stands down whenever the electoral,
  witness or offence-screening context that the corpus does cover is
  present.
- bare "copy of" and bare "information" are heavily corpus-covered:
  BNSS gives the informant a free copy of the FIR and the accused
  copies of the police report, judgments are supplied as certified
  copies, the Constitution and BNSS require grounds of arrest to be
  communicated, and CPA 2019 gives consumers a right to be informed.
  The information-access rule therefore stands down on any
  court/police/case/consumer context.

Known accepted limitations
--------------------------
- POCSO is cited by name inside `bnss:366`, `bnss:397` and `jj2015:2`
  as a cross-reference, so a narrow query like "are POCSO trials held in
  camera" is technically answerable from `bnss:366` and this guard will
  abstain on it anyway. That is the intended trade-off: abstaining on a
  rare answerable phrasing is much cheaper than answering "what is the
  punishment under POCSO" from an unrelated BNS section.
- A question that mixes a covered subject with an uncovered one -- "the
  police officer wants money to register my FIR" -- abstains as
  corruption, losing the FIR-registration remedy that BNSS does cover.
  Same trade-off as the POCSO note above, and preferred to answering a
  bribery question from police-procedure law.
"""
from __future__ import annotations

import re

# One category per demonstrated evaluation failure. Phrase-level, never
# bare keywords -- see the module docstring for why each discriminator
# was chosen and which safe-looking alternatives were rejected.
_CATEGORY_PATTERNS: list[tuple[str, list[str]]] = [
    ("pocso", [
        r"\bpocso\b",
        r"\bprotection of children from sexual offences\b",
    ]),
    ("motor_vehicles", [
        r"\bmotor vehicles? act\b",
        r"\bdrunk(en)? driving\b",
        r"\bdrink(ing)? and driv(e|ing)\b",
        r"\bdriving under the influence\b",
        r"\btraffic challan\b",
    ]),
    ("matrimonial", [
        r"\b(get|getting|file|filing|apply for|applying for|obtain|obtaining)\s+(a\s+|an\s+|my\s+)?divorce\b",
        r"\bdivorce\s+(procedure|petition|process|case|proceedings|papers|law)\b",
        r"\bgrounds for divorce\b",
        r"\bmutual consent divorce\b",
        r"\bhindu marriage act\b",
        r"\bspecial marriage act\b",
        r"\bjudicial separation\b",
    ]),
    ("sc_st_atrocities", [
        r"\batrociti(es)?\b",
        r"\bsc\s*/\s*st act\b",
        r"\bscheduled castes and scheduled tribes\s*\(?\s*prevention\b",
    ]),
    ("court_fees_civil_procedure", [
        r"\bcourt[- ]fees?\s+(for|to)\b",
        r"\bhow much\b[^?]{0,30}\bcourt[- ]fees?\b",
        r"\bcivil procedure code\b",
        r"\bcode of civil procedure\b",
        r"\bcpc\b",
    ]),
    # Minimum-wage questions. The Minimum Wages Act is not ingested, and
    # this subject was originally left to the confidence gate after a
    # probe showed the gate abstaining on it. The repeated-seed
    # experiment then demonstrated that margin is not robust: one of
    # five retrained seeds (seed 45) answered "what is the minimum wage
    # for a construction worker" over the floor, from bns:146 (unlawful
    # compulsory labour). One entry per demonstrated failure, as always;
    # "minimum wage(s)" occurs zero times in the indexed corpus, so the
    # bare phrase is safe. Other labour subjects stay with the gate --
    # no seed run answered any of them.
    ("minimum_wages", [
        r"\bminimum wages?\b",
    ]),
    # An explicit request for case law. No judgment of any court is
    # ingested -- the corpus is statute only -- but a judgment request
    # shares heavy vocabulary with ingested text (the Constitution's
    # Supreme Court chapter, BNSS's judgment-pronouncement provisions),
    # so retrieval would otherwise answer it confidently with statutes
    # the citizen did not ask for. Demonstrated by the revision's
    # citation-audit probe "supreme court judgment on privacy", answered
    # with five statutory excerpts. Patterns deliberately require the
    # case-law framing itself ("case law", "precedent", a court name
    # directly beside "judgment/ruling/verdict", or "judgment on
    # <topic>") -- bare "judgment" is genuine BNSS/Constitution
    # vocabulary ("when is judgment pronounced", "review of judgments")
    # and must keep answering.
    ("case_law", [
        r"\bcase[- ]law\b",
        r"\bprecedents?\b",
        r"\b(supreme court|high court)\s+(judgments?|judgements?|"
        r"rulings?|verdicts?)\b",
        r"\b(landmark|recent|latest|famous)\s+(judgments?|judgements?|"
        r"rulings?|cases?|verdicts?)\b",
        r"\b(judgments?|judgements?|rulings?|verdicts?)\s+(on|about|"
        r"regarding)\b",
        r"\bcourt\s+(has\s+)?rule[ds]?\s+(on|about|that)\b",
    ]),
]

# ---------------------------------------------------------------------
# Concept groups for the composed rules.
#
# Each group is a family of surface forms for ONE idea. A composed rule
# fires only when every one of its required groups matches somewhere in
# the query and none of its stand-down group does, so no single ordinary
# word ("officer", "information", "money") can trigger an abstention on
# its own. Written as concepts rather than phrases because citizens
# describe these two domains in wildly varying words but always combine
# the same underlying ideas.
# ---------------------------------------------------------------------

# The thing being sought: an administrative record or information held
# by the state. Deliberately excludes "evidence", "statement" and
# "report", which are court/police vocabulary the corpus does cover.
_ADMIN_RECORD = (
    r"\b(information|records?|documents?|files?|papers?|data|"
    r"certificates?|copies|copy)\b"
)

# The body holding it. "office"/"officer" are ordinary words and appear
# here only as one required half of a pair, never alone.
_GOVERNMENT_BODY = (
    r"\b(government|govt\.?|sarkari|public authority|public office|"
    r"public department|ministry|municipal|municipality|corporation office|"
    r"panchayat|tehsil|collectorate|revenue office|state office|"
    r"government (department|office|officer|official|body|agency)|"
    r"department|office|officer|official|authority)\b"
)

# Asking for / obtaining it.
_ACCESS_ACT = (
    r"\b(get|getting|obtain|obtaining|access|accessing|see|seeing|"
    r"inspect|inspecting|request(ed|ing)?|ask(ed|ing)?|apply|applying|"
    r"applied|application|seek(ing)?|demand(ed|ing)?|find out|know|"
    r"file|filing|submit(ting)?)\b"
)

# Being refused it, or challenging the refusal.
_REFUSAL_OR_APPEAL = (
    r"\b(refus(e|ed|es|al|ing)|den(y|ied|ies|ial)|reject(ed|ion|s)?|"
    r"withh(o|e)ld(ing)?|not (give|given|provide|provided|reply|replied|"
    r"respond(ed)?|answer(ed)?)|no (reply|response|answer)|"
    r"appeal(s|ed|ing)?|second appeal|first appeal)\b"
)

# How long the state may take. Paired with a government body so that
# "how long can the police detain me" (BNSS, covered) never matches.
_TIME_LIMIT = (
    r"\b(how long|how many days|time limit|deadline|within \w+ days|"
    r"due date|by when|how soon)\b"
)

# Responding to a citizen's application. Separate from _REFUSAL_OR_APPEAL
# because "how long does a department have to answer me" describes a
# pending response rather than a refusal of one.
_RESPOND_ACT = (
    r"\b(answer(ed|ing|s)?|repl(y|ies|ied|ying)|respond(ed|ing|s)?|"
    r"response|decide|decided|deciding|decision|process(ed|ing)?|"
    r"dispose (of)?|disposal|act on|get back)\b"
)

# A request whose object is information. Distinctive enough to stand as
# one half of a pair without a government body, because a citizen who
# says "my information request" is describing the RTI regime whatever
# words they use for the body that received it.
_INFORMATION_REQUEST = (
    r"\b(information|rti)\s+(request|application|appeal|petition|query)\b"
    r"|\brequest(ed|ing)?\s+for\s+information\b"
    r"|\bapplication\s+for\s+information\b"
    r"|\bask(ed|ing)?\s+for\s+(the\s+)?(information|records?|documents?|files?)\b"
)

# Roles and institutions that exist ONLY in the RTI regime. Verified to
# occur zero times across all 1801 indexed chunks, so these are safe on
# their own without a second concept.
_RTI_INSTITUTION = (
    r"\b(public information officer|state public information officer|"
    r"central public information officer|"
    r"information commission(er)?|"
    r"central information commission|state information commission|"
    r"first appellate authority|appellate authority)\b"
    r"|\b(c?pio|spio)\b(?!\s*card)"
)

# Court, police, case and consumer contexts, all of which the corpus
# genuinely answers. Any of these stands the information-access rule
# down -- see the "bare copy of / information" note in the docstring.
_COVERED_RECORD_CONTEXT = (
    r"\b(f\.?i\.?r\.?|first information report|charge[- ]?sheet|"
    r"police|detain(ed|ing)?|detention|custody|remand|"
    r"case diary|case file|court|judge|magistrate|judgment|judgement|"
    r"decree|order of the court|trial|hearing|bail|arrest(ed)?|"
    r"summons|warrant|witness|evidence|testimony|deposition|accused|"
    r"prosecution|chargesheet|"
    r"consumer|product|goods|seller|trader|manufacturer|advertisement|"
    r"service provider|e-?commerce|"
    r"domestic violence|protection officer|child|juvenile|adoption|"
    r"legal aid|lok adalat)\b"
)

# An illicit payment. "gratification" alone is deliberately absent: the
# corpus punishes several gratification offences and answers them well.
_ILLICIT_PAYMENT = (
    r"\b(bribe[sd]?|bribery|bribing|kickbacks?|"
    r"illegal gratification|speed money|rishwat|ghoos|ghus|"
    r"under[- ]the[- ]table|chai[- ]?paani|hafta)\b"
)

# Demanding money for something that should be free / official duty.
_PAYMENT_DEMAND = (
    r"\b(demand(s|ed|ing)?|want(s|ed|ing)?|ask(s|ed|ing)?|"
    r"expect(s|ed|ing)?|insist(s|ed|ing)?)\b[^.?!]{0,32}"
    r"\b(money|cash|payment|bribe|amount|rupees|rs\.?|extra)\b"
)

_CORRUPTION_WORD = r"\bcorrupt(ion|ly)?\b"

# --- provisions this project deliberately does not hold ----------------
#
# A different kind of gap from the ones above. The RTI Act IS in the
# corpus, but ss.13, 16 and 27 are excluded at ingestion: they govern the
# term of office, salary and conditions of service of Information
# Commissioners, and the ingested copy predates the RTI (Amendment) Act
# 2019 that replaced them. Serving that text would state repealed
# institutional law as current.
#
# Excluding them created a second-order problem this rule fixes.
# Measured: 7 of 8 tenure/salary questions were answered confidently from
# rti:2 (Definitions), rti:5 (Designation of PIOs), rti:12 and rti:15
# (Constitution of the Commissions) and rti:17 (Removal) -- real
# sections, correctly cited, none of which contains the answer. The
# provisions that do are precisely the ones we removed, so retrieval can
# only ever return neighbours here.
#
# Deliberately narrow. Questions about what the Commissions DO (s.18),
# how they are constituted and who appoints them (ss.12, 15), how a
# Commissioner is removed (s.17) and how to complain to them (s.18) are
# all genuinely answerable and must not be caught -- so this keys on
# service *terms* only, never on the Commissioner concept alone.
#
# Central-Government rule-making (s.27, also excluded) is deliberately
# NOT included: s.28 covers rule-making by a competent authority and is
# in the corpus, so a rules question has a real partial answer and
# guarding it would over-block.
_INFORMATION_COMMISSIONER = (
    r"\b(chief |state |central )*information commissioners?\b"
    r"|\b(cic|sic)\b(?!\s*card)"
)

_SERVICE_TERMS = (
    r"\b(term of office|tenure|how long\b[^.?!]{0,45}\b(serve|serves|"
    r"hold office|in office|stay|last)|length of (the )?term|"
    r"salary|salaries|pay|allowances|emoluments|pension|"
    r"conditions of service|service conditions|terms of service|"
    r"re[- ]?appoint(ed|ment)?|reappointment|"
    r"retire(ment|s|d)?|retiring age|age of retirement|"
    r"how many years)\b"
)

# Who is taking it -- a public official acting in an official capacity.
_PUBLIC_OFFICIAL = (
    r"\b(public servant|public official|government (officer|official|"
    r"servant|employee|staff)|govt\.? (officer|official)|"
    r"officer|official|clerk|babu|peon|inspector|tehsildar|patwari|"
    r"registrar|municipal|panchayat|department|office|"
    r"police officer|constable|sub[- ]inspector|sho)\b"
)

# Bribery contexts the corpus DOES cover: electoral bribery (BNS),
# bribing a witness (BSA), and gratification to screen an offender or
# recover stolen property (BNS). Any of these stands the rule down.
_COVERED_BRIBERY_CONTEXT = (
    r"\b(election|electoral|vote[rs]?|voting|candidate|polling|"
    r"treating|"
    r"witness|evidence|testimony|perjury|"
    r"screen(ing)?|conceal(ing|ment)?|"
    r"stolen (property|goods)|recover (any )?(movable )?property)\b"
)

# Composed rules: (category, required concept groups, stand-down group).
#
# Order is significant, and corruption is checked first because it is the
# more specific signal. "A government officer is demanding a bribe to
# process my file" satisfies the information-access rule too -- it
# contains an access act, a record and a government body -- but the
# illicit payment is what the question is actually about. Both categories
# abstain with the same message, so this only decides which `reason` code
# the response carries; it is ordered anyway so that reason stays
# truthful and the category counts remain meaningful.
_COMPOSED_RULES: list[tuple[str, list[str], str | None]] = [
    # A public official and an illicit payment.
    (
        "public_corruption",
        [_ILLICIT_PAYMENT, _PUBLIC_OFFICIAL],
        _COVERED_BRIBERY_CONTEXT,
    ),
    # A public official demanding money for official work.
    (
        "public_corruption",
        [_PAYMENT_DEMAND, _PUBLIC_OFFICIAL],
        _COVERED_BRIBERY_CONTEXT,
    ),
    # Reporting corruption by an official.
    (
        "public_corruption",
        [_CORRUPTION_WORD, _PUBLIC_OFFICIAL],
        _COVERED_BRIBERY_CONTEXT,
    ),
    # An Information Commissioner's service terms -- ss.13/16, excluded
    # as pre-2019 text. Requires both concepts, so questions about what
    # the Commissions do or how they are constituted still answer.
    (
        "rti_amended_service_provisions",
        [_INFORMATION_COMMISSIONER, _SERVICE_TERMS],
        None,
    ),
]

_COMPILED = [
    (category, [re.compile(p, re.IGNORECASE) for p in patterns])
    for category, patterns in _CATEGORY_PATTERNS
]

_COMPILED_COMPOSED = [
    (
        category,
        [re.compile(p, re.IGNORECASE) for p in required],
        re.compile(stand_down, re.IGNORECASE) if stand_down else None,
    )
    for category, required, stand_down in _COMPOSED_RULES
]

# What the corpus actually holds, stated plainly. Kept in sync with
# app/ingestion's APPROVED_SOURCES by hand -- if a source is added or
# removed, update this string (guarded by
# tests/test_corpus_coverage.py::test_message_lists_every_ingested_source).
NOT_IN_CORPUS_MESSAGE = (
    "This looks like a legal question about a law I don't have. I only "
    "hold verified India Code text for the Constitution, the Bharatiya "
    "Nyaya Sanhita, the Bharatiya Nagarik Suraksha Sanhita, the "
    "Bharatiya Sakshya Adhiniyam, the Consumer Protection Act 2019, the "
    "Juvenile Justice Act 2015, the Information Technology Act, the "
    "Protection of Women from Domestic Violence Act, the Legal "
    "Services Authorities Act, and the Right to Information Act 2005. "
    "Rather than quote you a section from the "
    "wrong Act, I'd rather say I can't answer this. You can read the "
    "actual Act at indiacode.nic.in, or contact India's free legal aid "
    "services -- Tele-Law or Nyaya Bandhu."
)


# A different statement from NOT_IN_CORPUS_MESSAGE, and the difference
# matters to the reader: the Act IS held, so "I don't have that law"
# would be false. What is missing is three specific sections, for a
# stated reason, and the honest thing is to say which and why.
EXCLUDED_PROVISION_MESSAGE = (
    "I do hold the Right to Information Act 2005, but not the part your "
    "question turns on. Sections 13, 16 and 27 -- the term of office, "
    "salary and conditions of service of Information Commissioners, and "
    "the Central Government's rule-making power -- were replaced by the "
    "Right to Information (Amendment) Act 2019, and the copy I have "
    "predates that amendment. Rather than quote you a version of those "
    "sections that is no longer the law, I've left them out. Everything "
    "else in the Act is here, including how to make a request, the time "
    "limits, the exemptions, appeals and penalties. For the current text "
    "of those three sections, read the amended Act at indiacode.nic.in."
)

#: Categories whose gap is a deliberately excluded provision rather than
#: an Act this project does not hold at all.
EXCLUDED_PROVISION_CATEGORIES = {"rti_amended_service_provisions"}

# A third kind of gap, again with its own honest message: the citizen is
# asking for a court's decision, and this corpus holds no judgment of
# any court -- by design, not omission. Quoting a statute in reply would
# look responsive while answering a different question.
CASE_LAW_MESSAGE = (
    "This looks like a question about a court judgment or case law. I "
    "hold verified statutory text only -- no judgment of any court is in "
    "my corpus -- so rather than quote you a statute as if it were the "
    "ruling you asked about, I'd rather say I can't answer this. Supreme "
    "Court judgments are published at sci.gov.in and other courts' "
    "decisions through the eCourts services; for free legal help, "
    "contact Tele-Law or Nyaya Bandhu."
)

#: Categories answered with CASE_LAW_MESSAGE.
CASE_LAW_CATEGORIES = {"case_law"}


def coverage_message(category: str) -> str:
    """The message that matches the kind of gap `category` describes."""
    if category in EXCLUDED_PROVISION_CATEGORIES:
        return EXCLUDED_PROVISION_MESSAGE
    if category in CASE_LAW_CATEGORIES:
        return CASE_LAW_MESSAGE
    return NOT_IN_CORPUS_MESSAGE


def classify_coverage_gap(text: str) -> str | None:
    """Return the matched un-ingested-subject category, or None.

    None does not mean "covered" -- it means this guard recognizes no
    named out-of-corpus subject, and the query falls through to
    retrieval and the confidence gate exactly as before.
    """
    for category, patterns in _COMPILED:
        if any(p.search(text) for p in patterns):
            return category
    for category, required, stand_down in _COMPILED_COMPOSED:
        if stand_down is not None and stand_down.search(text):
            continue
        if all(p.search(text) for p in required):
            return category
    return None
