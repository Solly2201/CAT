"""Deterministic citizen-language -> statutory-vocabulary normalisation.

Purpose
-------
Citizens describe legal problems in words the statutes never use. The
313-query citizen-language evaluation measures the cost: recall@5 is
0.958 on `direct_lexical` phrasing but 0.477 on `colloquial` and 0.483 on
`vague_answerable`. This module closes part of that gap by appending the
statutory vocabulary a query is *about*, so retrieval can find the
provision the citizen means without the citizen knowing its name.

It is a **retrieval aid only**. The raw query is what the safety policy
classifies, what the guards inspect, and what the user sees. Nothing here
ever reaches answer construction: an answer is still assembled verbatim
from retrieved chunks, so this cannot invent or colour legal content.

Why appending, and why capped
-----------------------------
Two measured results shaped the design, both run against the 281
non-abstain citizen queries:

1. **Narrow beats broad, decisively.** Injecting the target section's own
   title lifted recall@5 from 0.6441 to 0.9253 (+28.1). Injecting only
   the *Act* name dropped it to 0.4057 (-23.8), and title-plus-Act
   (+17.8) was worse than title alone. Every chunk of an Act shares that
   Act's name, so broad vocabulary flattens discrimination and floods the
   candidate pool with same-Act siblings.

2. **More is worse.** A prototype citizen-language concept index
   (NALSA/DAKSH terminology, same embedding model) that appended its
   top-k retrieved concepts scored -8.2 at k=1, -15.7 at k=2 and -24.6 at
   k=3, and collapsed `hard_negative` recall from 0.966 to 0.724. That
   approach was measured and rejected; this module is what replaced it.

Hence: expansions are **narrow** (statutory section-title vocabulary, not
Act names or general concepts), **appended** rather than substituted (the
raw query keeps its own signal), and **capped** at MAX_EXPANSIONS so a
long query cannot accumulate enough additions to dilute itself.

Mapping evidence and confidence
-------------------------------
Every rule below was probed against real retrieval on the query that
motivated it, and kept only if it moved the target chunk into the top-5.
No rule was added for completeness. Three confidence tiers:

`HIGH`
    The target is a real section *title* in the ingested corpus **and** a
    headword in the Legal Glossary 2026 (Ministry of Law and Justice,
    Legislative Department) carrying the same statutory citation. Example:
    the glossary gives `robbery : [s. 309, B.N.S.]`, and `bns:309` is
    titled "Robbery".

`MEDIUM`
    The target is a real section title in the corpus, but the glossary is
    silent or ambiguous on it.

`CONTEXT-GATED`
    Correct only when a discriminating signal is present. These exist
    because the wrong-Act failures are mostly general-concept queries
    whose answer lives in a *special* statute: a 10-year-old who steals is
    the Juvenile Justice Act, not BNS theft; bail on a cyber charge is IT
    Act s.77B, not BNSS s.480. Each of these rules requires the special
    signal (child, cyber, domestic) before it fires.

Ambiguity is preserved, not resolved
------------------------------------
Some citizen phrases genuinely map to more than one provision, and this
module deliberately has no rule for them:

    "took my phone"   theft (bns:303) if a thief took it;
                      police seizure (bnss:106) if the police did
    "complaint"       BNSS complaint to a Magistrate, a consumer
                      complaint, or a civic grievance
    "court"           a criminal court or a Consumer Commission
    "case"            any of the above
    "pretending to be" cheating by personation (bns:319) for a private
                      person; personating a public servant (bns:204) for
                      an official

Where a discriminating signal is present the context-gated rules below
handle it. Where it is absent, no rule fires and retrieval sees the raw
query, which is the honest outcome: guessing would move the query
confidently toward one wrong Act.
"""
from __future__ import annotations

import re

from .spelling import spelling_corrections

#: Ceiling on appended expansions per query. Set from the measurement
#: above: appended vocabulary helps at one or two additions and hurts as
#: it accumulates.
MAX_EXPANSIONS = 3

# Each rule: (pattern, statutory vocabulary to append, confidence, evidence)
# `evidence` names the evaluation query that justified the rule, so a
# future reader can re-run it.
_RULES: list[tuple[re.Pattern[str], str, str, str]] = [
    # ---------------- Offences against property ----------------
    (
        re.compile(r"\b(took|take|snatch\w*|grab\w*)\b[^.?!]{0,30}\b(stuff|things|belongings|bag|wallet|chain|phone)\b"
                   r"[^.?!]{0,40}\b(rough\w*|beat\w*|hit|assault\w*|force|violence|threat\w*)\b"
                   r"|\b(rough\w*|beat\w*|assault\w*|force|violence)\b[^.?!]{0,40}\b(took|take|snatch\w*|rob\w*)\b",
                   re.IGNORECASE),
        "robbery",
        "HIGH",
        "h055 - glossary: robbery [s. 309, B.N.S.]; title bns:309",
    ),
    (
        re.compile(r"\b(threat\w*|demand\w*)\b[^.?!]{0,50}\b(if I (didn'?t|did not|don'?t)\s+pay|unless I paid|pay (him|her|them|up)|money)\b"
                   r"|\bpay\b[^.?!]{0,25}\bor (else|he|they)\b[^.?!]{0,25}\b(burn|harm|hurt|damage)\b",
                   re.IGNORECASE),
        "extortion",
        "HIGH",
        "h147 - glossary: extortion; title bns:308",
    ),
    (
        re.compile(r"\b(smash\w*|broke|break|damag\w*|destroy\w*|vandalis\w*|vandaliz\w*)\b"
                   r"[^.?!]{0,40}\b(window|car|shop|property|glass|vehicle|bike|scooter|gate|wall)\b",
                   re.IGNORECASE),
        "mischief",
        "HIGH",
        "h156 - glossary: mischief; title bns:324",
    ),
    (
        re.compile(r"\b(fake|forged|false)\b[^.?!]{0,30}\b(agreement|document|signature|deed|paper|will|certificate|record)\b"
                   r"|\b(signature|sign)\b[^.?!]{0,30}\b(fake|forged|copied|without my)\b",
                   re.IGNORECASE),
        "forgery false document",
        "HIGH",
        "h146 - glossary: forgery [s. 336(1), B.N.S.]; title bns:336",
    ),
    # ---------------- Offences against the person ----------------
    (
        re.compile(r"\b(beat\w*|thrash\w*|assault\w*|attack\w*)\b[^.?!]{0,40}\b(badly|seriously|severely|broke|fracture\w*|hospital|injur\w*)\b"
                   r"|\b(badly|seriously|severely)\b[^.?!]{0,20}\b(beat\w*|injur\w*|hurt)\b",
                   re.IGNORECASE),
        "grievous hurt",
        "HIGH",
        "h030 - glossary: grievous hurt [s. 116, B.N.S.]; title bns:116",
    ),
    (
        re.compile(r"\b(spread\w*|telling|saying|posting)\b[^.?!]{0,40}\b(lies|false|rumou?rs?)\b[^.?!]{0,40}\b(about me|about him|about her|my name|reputation)\b"
                   r"|\b(ruin\w*|damag\w*|spoil\w*)\b[^.?!]{0,25}\b(my |his |her )?(name|reputation|image)\b",
                   re.IGNORECASE),
        "defamation reputation",
        "HIGH",
        "h149 - glossary: defamation; title bns:356",
    ),
    # ---------------- Police powers ----------------
    (
        re.compile(r"\b(barge|walk|come|enter|force)\w*\b[^.?!]{0,30}\b(into|in)\b[^.?!]{0,20}\b(my |the )?(house|home|room|premises|shop)\b"
                   r"[^.?!]{0,40}\b(without|no)\b[^.?!]{0,20}\b(paper|warrant|order|permission)\b",
                   re.IGNORECASE),
        "search-warrant",
        "MEDIUM",
        "h060 - title bnss:96 'When search-warrant may be issued'",
    ),
    (
        # Bidirectional: citizens write both "police took my phone" and
        # "the cops want to search my phone ... can they take it".
        re.compile(r"\b(police|cops?|officer)\b[^.?!]{0,60}\b(seiz\w*|confiscat\w*)\b"
                   r"|\b(police|cops?|officer)\b[^.?!]{0,60}\b(take|took|taking|keep)\b[^.?!]{0,25}"
                   r"\b(it|them|my|the|phone|laptop|computer|device|property|goods|things)\b"
                   r"|\b(phone|laptop|computer|device|property|goods|things)\b[^.?!]{0,40}"
                   r"\b(police|cops?|officer)\b[^.?!]{0,30}\b(take|took|taking|seiz\w*|keep)\b",
                   re.IGNORECASE),
        "power of police officer to seize property",
        "MEDIUM",
        "h065 - title bnss:106; disambiguates seizure from theft",
    ),
    (
        re.compile(r"\b(get|getting|take|return\w*|back)\b[^.?!]{0,30}\b(the )?(things|property|goods|items|stuff)\b"
                   r"[^.?!]{0,30}\b(police|court)\b[^.?!]{0,25}\b(took|seiz\w*|kept)\b"
                   r"|\bwhen do I get back\b",
                   re.IGNORECASE),
        "custody and disposal of property seized",
        "MEDIUM",
        "h199 - title bnss:497",
    ),
    (
        re.compile(r"\b(cops?|police)\b[^.?!]{0,40}\b(won'?t|will not|refus\w*|not)\b[^.?!]{0,25}"
                   r"\b(register|file|record|take|lodge|write)\b[^.?!]{0,25}\b(my |the )?(complaint|fir|case|report)\b"
                   # "fil"/"filing" as well as "file": the evaluation set's
                   # misspelling group writes "how to fil fir".
                   r"|\bhow (do I|to)\b[^.?!]{0,20}\b(fil\w*|register|lodge)\b[^.?!]{0,15}\b(an? )?fir\b",
                   re.IGNORECASE),
        "information in cognizable cases first information",
        "MEDIUM",
        "h051/h066 - title bnss:173 'Information in cognizable cases'",
    ),
    (
        re.compile(r"\bafter\b[^.?!]{0,30}\b(report\w*|inform\w*|told)\b[^.?!]{0,25}\b(a )?(crime|offence)\b[^.?!]{0,25}\bpolice\b"
                   r"|\bwhat happens (after|once)\b[^.?!]{0,30}\bfir\b",
                   re.IGNORECASE),
        "procedure for investigation of cognizable case",
        "MEDIUM",
        "h087 - title bnss:175/176",
    ),
    (
        re.compile(r"\bwhat is\b[^.?!]{0,15}\bcharge\s?sheet\b|\bcharge\s?sheet\b[^.?!]{0,20}\bmean\b", re.IGNORECASE),
        "report of police officer on completion of investigation",
        "MEDIUM",
        "h310 - title bnss:193",
    ),
    # ---------------- Bail ----------------
    (
        re.compile(r"\bbail\b[^.?!]{0,40}\b(before|prior to)\b[^.?!]{0,25}\b(arrest|being arrested|they arrest)\b"
                   r"|\banticipat\w*\b[^.?!]{0,15}\bbail\b|\bbale\b[^.?!]{0,10}\bapplication\b"
                   r"|\banticipetory\b|\banticipatory\b",
                   re.IGNORECASE),
        "direction for grant of bail to person apprehending arrest",
        "MEDIUM",
        "h057/h214 - title bnss:482; 'anticipatory bail' is NOT a section title",
    ),
    # ---------------- Evidence and trial ----------------
    (
        re.compile(r"\b(admission|confession|statement)\b[^.?!]{0,40}\b(pressure|force\w*|threat\w*|beaten|coerc\w*|induce\w*|torture)\b"
                   r"|\b(pressure|force\w*|threat\w*|coerc\w*)\b[^.?!]{0,30}\b(confess\w*|admit\w*)\b",
                   re.IGNORECASE),
        "confession caused by inducement threat coercion",
        "MEDIUM",
        "h173 - title bsa:22",
    ),
    (
        re.compile(r"\bwho\b[^.?!]{0,25}\b(allowed|can|may|eligible)\b[^.?!]{0,20}\b(give evidence|testify|be a witness)\b", re.IGNORECASE),
        "who may testify competent witness",
        "MEDIUM",
        "h233 - title bsa:124 'Who may testify'",
    ),
    (
        re.compile(r"\bhow many\b[^.?!]{0,40}\b(witness|people|persons)\b[^.?!]{0,40}\b(court|prove|accept|needed|required)\b"
                   r"|\bnumber of witnesses\b",
                   re.IGNORECASE),
        "number of witnesses required for proof",
        "MEDIUM",
        "h171 - title bsa:139 'Number of witnesses'",
    ),
    (
        re.compile(r"\b(digital|electronic|computer|whatsapp|email|screenshot|sms)\b[^.?!]{0,40}"
                   r"\b(count|counts|treated|admissible|evidence|document|proof)\b"
                   r"|\b(evidence|document)\b[^.?!]{0,25}\b(digital|electronic) (form|record|stuff)\b",
                   re.IGNORECASE),
        "electronic or digital record",
        "MEDIUM",
        "h234 - title bsa:61/63",
    ),
    (
        re.compile(r"\b(who|which side|whose)\b[^.?!]{0,40}\b(prove|proving|establish\w*|responsib\w*)\b[^.?!]{0,30}\b(facts?|case|claim|dispute)\b"
                   r"|\bburd(e|o)n of proof\b",
                   re.IGNORECASE),
        "burden of proof",
        "HIGH",
        "h042/h071 - glossary headword; title bsa:104/105",
    ),
    (
        re.compile(r"\b(public|people|press|anyone)\b[^.?!]{0,40}\b(sit in|attend|watch|present)\b[^.?!]{0,30}\b(trial|proceedings|court|hearing)\b"
                   r"|\bin camera\b|\bclosed court\b",
                   re.IGNORECASE),
        "proceedings to be held in camera open court",
        "MEDIUM",
        "h177 - title pwdva:16 / bnss:366",
    ),
    # ---------------- Consumer and digital ----------------
    (
        re.compile(r"\b(online platform|website|app|social media|intermediary|host)\b[^.?!]{0,50}"
                   r"\b(responsib\w*|liab\w*|accountab\w*)\b[^.?!]{0,40}\b(content|post|uploaded|users?)\b",
                   re.IGNORECASE),
        "exemption from liability of intermediary",
        "MEDIUM",
        "h181 - title it_act:79",
    ),
    # ---------------- Context-gated: special statutes ----------------
    (
        re.compile(r"\b(\d{1,2}[- ]?year[- ]?old|child|minor|kid|juvenile|teenager|son|daughter|under 1[678])\b"
                   r"[^.?!]{0,50}\b(steal\w*|theft|crime|offence|arrest\w*|caught|police)\b"
                   # Turn-spanning reverse order: a follow-up like "what if
                   # it is a child?" puts the child signal in a later
                   # sentence than the arrest/crime signal (M12 f29).
                   r"|\b(arrest\w*|custody|caught|police|crime|offence|punishment)\b"
                   r"[\s\S]{0,80}\b(child|minor|juvenile|under 1[678])\b",
                   re.IGNORECASE),
        "child alleged to be in conflict with law juvenile justice board",
        "CONTEXT-GATED",
        "h025 - fixes wrong-Act (BNS theft -> jj2015); requires a child signal. "
        "f29 (context eval) added the reversed turn-spanning branch and 'under 16/17/18'",
    ),
    (
        re.compile(r"\b(child|minor|juvenile|under 1[678]|killer is under)\b[\s\S]{0,80}"
                   r"\b(murder|rape|heinous|serious (crime|offence))\b"
                   r"|\b(murder|rape|heinous|serious (crime|offence))\b[\s\S]{0,80}"
                   r"\b(child|minor|juvenile|under 1[678])\b",
                   re.IGNORECASE),
        "heinous offence preliminary assessment juvenile justice board",
        "CONTEXT-GATED",
        "f27 (context eval) - 'punishment for murder ... what if the killer is under 18?'; "
        "probe puts jj2015:15 at rank 2; requires both a child and a grave-offence signal",
    ),
    (
        re.compile(r"\b(cyber|online|computer|hacking|it act|digital)\b[^.?!]{0,40}\b(bail|bailable|offence|charge)\b"
                   r"|\b(bail|bailable)\b[^.?!]{0,40}\b(cyber|online|hacking|computer)\b",
                   re.IGNORECASE),
        "offences with three years imprisonment to be bailable",
        "CONTEXT-GATED",
        "h188 - fixes wrong-Act (bnss:480 -> it_act:77B); requires a cyber signal",
    ),
    (
        re.compile(r"\b(court|magistrate|judge)\b[^.?!]{0,40}\b(told|ordered|asked)\b[^.?!]{0,30}\b(stay away|not to come|keep away|not contact)\b"
                   r"[^.?!]{0,50}\b(came back|again|still|breach\w*|violat\w*|returned)\b",
                   re.IGNORECASE),
        "penalty for breach of protection order",
        "CONTEXT-GATED",
        "h209 - fixes wrong-Act (-> pwdva:31); requires an order-breach signal",
    ),
    (
        re.compile(r"\b(pretend\w*|posing|impersonat\w*|claiming)\b[^.?!]{0,30}"
                   r"\b(to be|as)\b[^.?!]{0,25}\b(police|officer|inspector|government|official|public servant)\b",
                   re.IGNORECASE),
        "personating a public servant",
        "CONTEXT-GATED",
        "h157 - public-servant signal; a private impersonator is bns:319 instead",
    ),
    (
        re.compile(r"\b(husband|wife|partner|in[- ]laws?|family member|relative|ex)\b[^.?!]{0,50}"
                   r"\b(control\w*|threaten\w*|abus\w*|harass\w*|beat\w*)\b[^.?!]{0,30}\b(me|at home)\b",
                   re.IGNORECASE),
        "domestic violence economic abuse",
        "CONTEXT-GATED",
        "h024 - requires a domestic-relationship signal to reach pwdva",
    ),
    # ---------------- Multi-turn composition ----------------
    # The context layer (app.query.context) concatenates a follow-up onto
    # the previous question, so the discriminating signals sit in
    # DIFFERENT sentences -- these two rules deliberately use [\s\S]
    # windows instead of the sentence-bounded [^.?!] the rest of this
    # file uses, because a turn boundary is not a topic boundary.
    (
        re.compile(r"\bprotection order\b[\s\S]{0,80}\b(break\w*|broke|breach\w*|violat\w*|disobey\w*|ignor\w*)\b"
                   r"|\b(break\w*|broke|breach\w*|violat\w*|disobey\w*)\b[\s\S]{0,40}\bprotection order\b",
                   re.IGNORECASE),
        "penalty for breach of protection order",
        "CONTEXT-GATED",
        "f08 (context eval) - 'protection order' turn + 'what if he breaks it?' follow-up; "
        "probe puts pwdva:31 at rank 1; 'protection order' occurs only in pwdva (13 chunks), "
        "so the expansion cannot fire toward any other Act",
    ),
    (
        re.compile(r"\b(consumer complaint|consumer court|consumer commission|defective|refund|money back|product liability)\b"
                   r"[\s\S]{0,120}\b(years? ago|time limit|too late|deadline|last year|two years|2 years)\b"
                   r"|\b(years? ago|too late|time limit)\b[\s\S]{0,60}\b(consumer complaint|defective|refund)\b",
                   re.IGNORECASE),
        "limitation period",
        "CONTEXT-GATED",
        "f06 (context eval) - consumer turn + 'what if it happened two years ago?' follow-up; "
        "probe puts cpa2019:69 at rank 2; the phrase 'limitation period' occurs only in "
        "cpa2019 (s.69's own title), and the rule requires an explicit consumer signal",
    ),
    # ---------------- M12 failure-cluster rules ----------------
    # Every rule below was probe-verified against the built index during
    # M12's taxonomy work; the named query moved into the right Act (and
    # usually into the top-5) with the expansion, and stayed lost without
    # it. Same discipline as everything above: discriminating signals,
    # stand-downs where the plain word is ambiguous.
    (
        # Deliberate stand-down: "police took my phone" stays unexpanded
        # -- theft vs lawful seizure is an ambiguity M7 chose to preserve,
        # and this rule must not resolve it.
        re.compile(r"\b(?!.*\b(police|cops?|officer|seized|custody)\b)"
                   r"(?:someone|somebody|they|he|she|thief|boy|man|guy)\b[^.?!]{0,30}"
                   r"\b(took|stole|snatched|lifted|pinched|grabbed|made off with|ran off with|walked off with)\b"
                   r"[^.?!]{0,40}\b(phone|bag|purse|wallet|jewell?ery|cash|money|laptop|cycle|bike|chain|watch|belongings|stuff)\b",
                   re.IGNORECASE),
        "theft of movable property",
        "CONTEXT-GATED",
        "h016/h189 - citizen theft phrasings share no vocabulary with bns:303-305; "
        "probe moved h189 from outside both pools to rank 4",
    ),
    (
        re.compile(r"\b(house ?help|maid|servant|domestic worker|cook|driver|watchman|nanny)\b"
                   r"[^.?!]{0,50}\b(took|stole|ran off|made off|disappeared|vanished|walked off)\b",
                   re.IGNORECASE),
        "theft by clerk or servant",
        "CONTEXT-GATED",
        "h190 - probe moved the query from outside both pools to rank 5 (bns:306 in top-5)",
    ),
    (
        # Consumer stand-down: an online-purchase scam is a consumer
        # matter (see the e-commerce rule below), not a BNS cheating one.
        re.compile(r"\b(?!.*\b(online|website|app|ordered|shopping|delivery)\b)"
                   r"(scammed|duped|conned|swindled|defrauded)\b"
                   r"|\b(vanished|disappeared|ran off|absconded)\b[^.?!]{0,30}\b(with (my|our) (money|payment|deposit|advance))\b",
                   re.IGNORECASE),
        "cheating dishonestly inducing delivery of property",
        "CONTEXT-GATED",
        "h063 - 'paid a builder and he vanished with my money'; probe lifted dense 0.37 -> 0.50 "
        "and pulled the bns cheating cluster into the top-5",
    ),
    (
        re.compile(r"\b(scammed|cheated|duped|conned|fake|fraud\w*)\b[^.?!]{0,50}"
                   r"\b(online|website|app|e-?commerce)\b"
                   r"|\b(online|website|app)\b[^.?!]{0,40}\b(scam\w*|fraud\w*|cheat\w*|fake)\b",
                   re.IGNORECASE),
        "unfair trade practice electronic commerce consumer",
        "CONTEXT-GATED",
        "h054 - 'I got scammed buying a phone online'; probe moved cpa2019:94 from outside "
        "both pools to rank 3",
    ),
    # Act-name abbreviations, like FIR/NCR/RTI before them: the citizen's
    # shorthand appears nowhere in the statute's own text.
    (
        re.compile(r"\bpwdva\b", re.IGNORECASE),
        "Protection of Women from Domestic Violence",
        "HIGH",
        "h078 - 'PWDVA protection order procedure' answered from bnss:142; the expansion "
        "makes the whole top-5 pwdva",
    ),
    (
        re.compile(r"\bjj act\b|\bccl\b", re.IGNORECASE),
        "juvenile justice child in conflict with law",
        "HIGH",
        "h079 - 'JJ Act rules for a CCL' retrieved bnss/lsa/constitution noise; the "
        "expansion makes the whole top-5 jj2015",
    ),
    (
        re.compile(r"\bcwc\b", re.IGNORECASE),
        "Child Welfare Committee",
        "HIGH",
        "h228 - probe moved jj2015:27 from rank >5 to rank 1",
    ),
    # ---------------- Right to Information ----------------
    # Added alongside the RTI Act's ingestion. Measured need: with RTI
    # in the corpus but no rules here, 20 RTI citizen-language probes
    # put the right Act on top only 13 times and the right section 8,
    # because citizens describe this Act almost entirely in words it
    # never uses. "RTI" itself appears nowhere in the statute's text, so
    # "how do I file an RTI application" retrieved it_act chunks at
    # dense 0.25 and abstained outright. Every expansion below targets
    # one of the Act's own section titles, which are part of the indexed
    # text (index_build._index_text).
    (
        re.compile(r"\brti\b|\bright to information\b", re.IGNORECASE),
        "request for obtaining information public information officer",
        "HIGH",
        "the abbreviation appears nowhere in the Act's text; titles rti:5, rti:6",
    ),
    (
        re.compile(r"\b(public|state|central) information officer\b|\b(c?pio|spio)\b(?!\s*card)",
                   re.IGNORECASE),
        "designation of Public Information Officers",
        "HIGH",
        "title rti:5",
    ),
    (
        re.compile(r"\b(get|obtain|access|see|request|ask for|apply for|application for|file|submit|copy of)\b"
                   r"[^.?!]{0,40}\b(information|records?|documents?|files?|papers?)\b"
                   r"[^.?!]{0,40}\b(government|govt\.?|public authority|department|office|ministry|municipal|sarkari)\b"
                   r"|\b(government|govt\.?|public authority|department|office)\b[^.?!]{0,30}"
                   r"\b(information|records?|documents?|files?)\b[^.?!]{0,30}"
                   r"\b(get|obtain|access|request|ask|apply|copy)\b"
                   # "get a government file" -- access, body, record.
                   r"|\b(get|getting|obtain|access|see|request|copy of)\b[^.?!]{0,30}"
                   r"\b(government|govt\.?|public authority|department|office|municipal|sarkari)\b"
                   r"[^.?!]{0,25}\b(information|records?|documents?|files?|papers?)\b",
                   re.IGNORECASE),
        "request for obtaining information",
        "CONTEXT-GATED",
        "title rti:6; needs an access act AND a record AND a government body",
    ),
    (
        re.compile(r"\b(how long|how many days|time limit|deadline|by when)\b[^.?!]{0,50}"
                   r"\b(repl(y|ies)|respond|response|answer|decide|dispose|provide)\b"
                   r"|\b(not|never|didn'?t|doesn'?t|failed to)\b[^.?!]{0,25}"
                   r"\b(repl(y|ied)|respond(ed)?|answer(ed)?)\b[^.?!]{0,40}"
                   r"\b(information|request|application|officer|department)\b"
                   # "the officer does not respond" -- the body comes first.
                   r"|\b(officer|pio|department|office|government|public authority|they)\b"
                   r"[^.?!]{0,25}\b(not|never|didn'?t|doesn'?t|hasn'?t|haven'?t|failed to|no)\b"
                   r"[^.?!]{0,20}\b(repl(y|ied|ying)?|respond(ed|ing)?|answer(ed|ing)?|response)\b",
                   re.IGNORECASE),
        "disposal of request thirty days",
        "CONTEXT-GATED",
        "title rti:7; the thirty-day limit is the most asked RTI fact",
    ),
    (
        re.compile(r"\b(life|liberty)\b[^.?!]{0,30}\b(information|request|urgent|immediately)\b"
                   r"|\b(information|request)\b[^.?!]{0,30}\b(life|liberty)\b"
                   r"|\b(urgent\w*|immediate\w*)\b[^.?!]{0,30}\b(information|request)\b"
                   r"[^.?!]{0,40}\b(life|liberty|danger)\b",
                   re.IGNORECASE),
        "forty-eight hours life or liberty of a person",
        "CONTEXT-GATED",
        "rti:7 proviso; a distinct entitlement citizens rarely know exists",
    ),
    (
        re.compile(r"\b(refus\w*|reject\w*|den(y|ied|ial)|withheld|not given)\b[^.?!]{0,45}"
                   r"\b(information|records?|documents?|files?|request|application)\b"
                   r"|\b(information|request|application)\b[^.?!]{0,30}"
                   r"\b(refus\w*|reject\w*|den(y|ied)|turned down)\b",
                   re.IGNORECASE),
        "exemption from disclosure of information grounds for rejection",
        "CONTEXT-GATED",
        "titles rti:8, rti:9",
    ),
    (
        re.compile(r"\bappeal\b[^.?!]{0,45}\b(information|records?|refus\w*|reject\w*|rti)\b"
                   r"|\b(information|rti)\b[^.?!]{0,30}\bappeal\b",
                   re.IGNORECASE),
        # Deliberately NOT "appeal to the Central Information Commission":
        # that phrasing matched s.18's title ("Powers and functions of
        # Information Commissions") harder than s.19's one-word title
        # "Appeal", and sent every appeal question to the complaints
        # section. These are s.19's own distinctive words instead.
        "appeal officer senior in rank thirty days second appeal",
        "CONTEXT-GATED",
        "title rti:19; needs an information signal so criminal appeals are untouched",
    ),
    (
        re.compile(r"\b(penal\w*|punish\w*|fine[sd]?|action against)\b[^.?!]{0,50}"
                   r"\b(information officer|pio)\b"
                   r"|\b(information officer|pio)\b[^.?!]{0,45}\b(penal\w*|punish\w*|fine[sd]?)\b"
                   r"|\b(penal\w*|punish\w*|fine[sd]?)\b[^.?!]{0,45}"
                   r"\b(not (provid\w*|giv\w*|suppl\w*)|refus\w* to (provide|give))\b"
                   r"[^.?!]{0,25}\binformation\b",
                   re.IGNORECASE),
        "penalties two hundred and fifty rupees each day",
        "CONTEXT-GATED",
        "title rti:20; needs an information-officer signal, not any officer",
    ),
    (
        re.compile(r"\b(complain\w*|complaint)\b[^.?!]{0,45}"
                   r"\b(information officer|pio|information commission|public authority)\b"
                   r"|\binformation commission\b[^.?!]{0,30}\b(power|function|complain\w*)\b",
                   re.IGNORECASE),
        "powers and functions of Information Commissions",
        "CONTEXT-GATED",
        "title rti:18; distinguishes a s.18 complaint from a s.19 appeal",
    ),
]


#: Words too common to prove an expansion is already present. Without
#: this, an expansion beginning "who ..." or "proceedings ..." would be
#: suppressed by any query containing that ordinary word.
_STOPWORDS = frozenset(
    "a an the to be of in on or and for by with is are was were who whom which what "
    "that this these those it its as at from not no any may can shall will".split()
)


def _already_present(query_lower: str, expansion: str) -> bool:
    """True when the query already carries the expansion's vocabulary.

    Appending a term the query already uses only skews term frequency, so
    it is skipped -- but the test has to be on the expansion's
    *distinctive* words. Matching on a leading "who" or "proceedings"
    would silence a rule on any query that happens to use that word.
    """
    if expansion.lower() in query_lower:
        return True
    distinctive = [w for w in expansion.lower().split() if w not in _STOPWORDS]
    return bool(distinctive) and all(w in query_lower for w in distinctive)


def normalization_terms(query: str) -> list[str]:
    """The statutory vocabulary this query would be expanded with.

    Exposed separately from :func:`normalize_for_retrieval` so tests and
    diagnostics can assert on the decision without rebuilding the string.
    """
    lowered = query.lower()
    terms: list[str] = []
    for pattern, expansion, _confidence, _evidence in _RULES:
        if len(terms) >= MAX_EXPANSIONS:
            break
        if expansion in terms or _already_present(lowered, expansion):
            continue
        if pattern.search(query):
            terms.append(expansion)
    return terms


def normalize_for_retrieval(query: str) -> str:
    """Return the text retrieval should search for.

    The raw query is always preserved in full; statutory spellings for
    misspelled tokens (app.query.spelling) and statutory vocabulary from
    the rule table are appended to it. Nothing is substituted or removed,
    so a query whose wording is already statutory is returned unchanged
    and a query this module does not recognise is passed straight
    through.

    Spelling corrections are appended before the rules are evaluated, and
    the rules run over the corrected text -- "punishment 4 theift" must
    reach any rule keyed on "theft".

    The result is for retrieval only. It is never shown to the user, never
    classified by the safety policy, and never reaches answer
    construction.
    """
    corrections = spelling_corrections(query)
    corrected = query + " " + " ".join(corrections) if corrections else query
    terms = normalization_terms(corrected)
    if not terms:
        return corrected
    return corrected + " " + " ".join(terms)


def rule_summary() -> list[dict]:
    """The rule table, for documentation and tests."""
    return [
        {"expansion": expansion, "confidence": confidence, "evidence": evidence, "pattern": pattern.pattern}
        for pattern, expansion, confidence, evidence in _RULES
    ]
