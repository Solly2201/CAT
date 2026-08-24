"""Deterministic query-safety policy for the legal-answer pipeline.

Runs BEFORE retrieval (see ``app.generation.pipeline.handle_legal_query``).
Rule-based only, by design -- no ML classifier, and the legal-answer
pipeline never uses a generative LLM at all (standing project decision,
see docs/PROJECT_STATE.md). Contact routes below are fixed configuration
data, not model-generated text, matching docs/LEGAL_SOURCES.md's
"Safety redirect sources" table.

Why this is not a keyword blacklist
-----------------------------------
The first version of this module was a flat list of phrases, and it
failed in both directions. It answered "How can I hide evidence from the
police?" as an ordinary legal question (no phrase covered it), while it
hard-stopped "Explain what the law says about domestic violence" with an
emergency redirect, because the bare phrase "domestic violence" was on
the list. Both failures have the same cause: a phrase says what a query
is *about*, and says nothing about what the person is *asking for*.
"Domestic violence" is simultaneously the name of a chapter of law a
citizen is entitled to learn about and the description of a situation
someone may be living through right now.

So this module reads three independent signals and combines them, rather
than matching one list:

``SUBJECT``
    What the query concerns, tiered by how much harm a wrong response
    could do: life-threatening subjects (threats to life, ongoing
    violence, self-harm, child endangerment, medical emergency) and
    serious-legal subjects (a live accusation, an interrogation, an
    imminent arrest, sexual violence). A subject alone never decides
    anything.

``FRAME``
    How the person is asking. *Informational* ("what does the law say
    about...", "what is the difference between...", "under which
    section...") means they are studying a topic. *Instructional* ("how
    do I...", "what should I say...", "help me...") means they want to be
    told what to do. *Personal* ("I was...", "my husband...", "they are
    questioning me") means they are describing their own situation.

``IMMEDIACY``
    Whether the situation is presented as live ("right now", "is
    happening", "about to", "tonight").

The combination decides the severity, and the decision table lives in one
place (:func:`assess_query`) so it can be read and tested as a policy
rather than reverse-engineered from a regex list.

Harmful-assistance requests are handled separately and first, because
they are the one case where the request itself decides the outcome:
asking to be shown *how* to destroy evidence, fabricate an alibi,
interfere with a witness or evade a police search is refused whatever the
framing. The detector still requires an instructional frame, so the
educational counterpart ("what is the punishment for destroying
evidence?", which BNS s.238 genuinely answers) goes to retrieval
untouched.

This is a deterministic v1 policy, not an exhaustive safety classifier.
It is conservative where the cost of a miss is physical harm, and
permissive where the cost of a false positive is blocking ordinary legal
education. Anything it does not recognise falls through to the existing
topic-relevance guard, corpus-coverage guard, retrieval and confidence
gate exactly as before.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# --- Severity levels ---------------------------------------------------
# Named constants so the pipeline, the API response model and the tests
# all refer to the same four states.
SEVERITY_EMERGENCY = "emergency"
SEVERITY_HARMFUL_REQUEST = "harmful_request"
SEVERITY_SERIOUS = "serious"
SEVERITY_NORMAL = "normal"

#: Every severity the policy can return, least to most restrictive.
SEVERITIES = (SEVERITY_NORMAL, SEVERITY_SERIOUS, SEVERITY_EMERGENCY, SEVERITY_HARMFUL_REQUEST)


def _compile(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def _any(compiled: list[re.Pattern[str]], text: str) -> bool:
    return any(p.search(text) for p in compiled)


# --- Signal 1: harmful assistance requests -----------------------------
# An "act" here is something the law itself treats as obstruction:
# destroying or concealing evidence, fabricating evidence or an alibi,
# interfering with a witness, absconding, or defeating a lawful search.
# Matched only together with an instructional frame (below), so the
# educational phrasing of the same subject is untouched.
_HARMFUL_ACTS = _compile([
    # Evidence destruction / concealment
    r"\b(hide|hiding|destroy|destroying|get rid of|dispose of|burn|delete|deleting|wipe|erase|erasing)\b"
    r"[^.?!]{0,40}\b(evidence|proof|weapon|body|documents?|records?|cctv|footage|messages?|chats?)\b",
    r"\b(evidence|proof|cctv footage|the weapon|the body)\b[^.?!]{0,25}\b(disappear|vanish|untraceable)\b",
    r"\bhide\b[^.?!]{0,25}\b(the )?(body|weapon|gun|knife|drugs?)\b",
    # Fabrication
    r"\b(fake|false|forged?|fabricat\w*|made[- ]up)\b[^.?!]{0,30}"
    r"\b(alibi|statement|affidavit|witness|receipt|document|evidence|fir|complaint|signature)\b",
    r"\b(create|creating|make|making|invent|manufacture|cook up|set up|build)\b[^.?!]{0,25}\b(an? )?alibi\b",
    r"\b(forge|forging)\b[^.?!]{0,25}\b(a |an |the )?(signature|document|certificate|id)\b",
    # Witness / complainant interference
    r"\b(threaten|threatening|bribe|bribing|silence|silencing|pressure|pressuring|intimidat\w*"
    r"|buy off|pay off)\b[^.?!]{0,30}"
    r"\b(witness(es)?|complainant|victim|informant|judge|magistrate|investigating officer)\b",
    r"\b(witness(es)?|complainant|victim)\b[^.?!]{0,25}\b(change|withdraw|retract)\b[^.?!]{0,25}\bstatement\b",
    r"\bmake\b[^.?!]{0,20}\bwitness\b[^.?!]{0,20}\b(lie|not testify|stay quiet)\b",
    # Evading law enforcement / absconding
    r"\b(avoid|avoiding|evade|evading|escape|escaping|dodge|dodging|run from|running from|abscond\w*"
    r"|stay away from|hide from)\b"
    r"[^.?!]{0,30}\b(police|arrest|the law|law enforcement|custody|summons|warrant|investigation)\b",
    r"\b(not get caught|never get caught|avoid getting caught|get away with (it|a crime|murder|theft|fraud))\b",
    r"\b(defeat|beat|trick|fool|get past|get around)\b[^.?!]{0,25}"
    r"\b(a |the )?(search|raid|police check|lie detector|polygraph|investigation)\b",
    # Lying to authorities
    r"\b(lie|lying)\b[^.?!]{0,25}\b(to the police|to the court|under oath|in my statement|to the magistrate)\b",
    r"\bfil(e|ing)\b[^.?!]{0,20}\b(a )?(false|fake) (fir|complaint|case|report)\b",
    # Instructions for committing serious harm
    r"\b(make|build|making|building)\b[^.?!]{0,20}\b(a )?(bomb|explosive|ied)\b",
    r"\b(hack|hacking|break)\b[^.?!]{0,25}\b(into )?(someone'?s?|another person'?s?|an?) "
    r"(account|phone|email|system|wifi|database)\b",
    r"\b(untraceable|without getting traced|without leaving (any )?evidence)\b",
])

# "Tell me how to do this", in the various ways citizens actually phrase
# it. Deliberately excludes "what is the punishment for" and "what does
# the law say about", which are the educational counterparts.
_INSTRUCTIONAL_FRAME = _compile([
    r"\bhow (do|can|could|should|would|might|to)\b",
    r"\bwhat('s| is) the (best|easiest|safest|quickest) way\b",
    r"\b(help|show|teach|tell|guide) me\b",
    r"\bany (way|ways|tips|tricks|advice) (to|for|on)\b",
    r"\bis there a way (to|i can)\b",
    r"\bwhat should (i|we|he|she|they) (do|say|tell)\b",
    r"\bi (want|need) to know how\b",
    r"\bgive me (a |the )?(steps|instructions|script|advice)\b",
    r"\bways? to\b",
])

# --- Signal 2: subject matter ------------------------------------------
# Tier A: a wrong or slow response risks physical harm to a person. Kept
# as named sub-groups rather than one flat list, because which official
# helpline the emergency response names depends on which group matched.
_SELF_HARM_SUBJECTS = _compile([
    r"\b(kill myself|end my life|want to die|take my own life|ending it all)\b",
    r"\bsuicid\w*\b",
    r"\b(hurt|harm|cutting) myself\b",
    r"\bself[- ]harm\b",
])

_MEDICAL_EMERGENCY_SUBJECTS = _compile([
    r"\b(heart attack|not breathing|stopped breathing|overdose|severe bleeding"
    r"|bleeding heavily|medical emergency|unconscious|collapsed)\b",
])

_CHILD_SAFETY_SUBJECTS = _compile([
    r"\b(child|minor|daughter|son|kid|baby)\b[^.?!]{0,30}"
    r"\b(is being|are being|being|is|was|were) (abused|beaten|molested|trafficked|hurt|starved|harmed)\b",
    r"\bchild (in danger|traffick\w*|abuse is happening)\b",
    r"\b(abus\w*|molest\w*|hurting|beating)\b[^.?!]{0,20}\b(my|a|the) (child|daughter|son|baby|minor)\b",
    # A child taken by another person, or missing. "my daughter has been
    # kidnapped" already reached the emergency tier through
    # _THREAT_TO_LIFE_SUBJECTS, but only because it used the word
    # "kidnapped" -- the far more likely phrasings a frightened parent
    # actually types ("someone took my child", "my son did not come back
    # from school and a stranger took him", "my child went missing") all
    # graded normal. Routed here rather than to threat_to_life so the
    # response names Childline 1098 alongside 112.
    #
    # Scoped to the speaker's own child ("my"/"our"), which is what keeps
    # "what does the law say about missing children?" out: it has no
    # possessive, and the educational gate in assess_query stands as a
    # second layer behind that.
    r"\b(someone|somebody|a man|a woman|a guy|a stranger|he|she|they)\b[^.?!]{0,30}"
    r"\b(took|taken|grabbed|snatched|picked up|drove off with|walked off with|lured)\b"
    r"[^.?!]{0,25}\b((my|our) (child|daughter|son|kid|baby|boy|girl)|him|her)\b",
    r"\b(my|our) (child|daughter|son|kid|baby)\b[^.?!]{0,45}"
    r"\b(went missing|is missing|has gone missing|never came home|"
    r"(did|does) ?n[o']?t come (home|back)|has ?n[o']?t come home|"
    r"did ?n[o']?t come back|has ?n[o']?t returned|never returned)\b",
    # Passive voice, with no actor named: "my child was taken". The
    # active patterns above all require someone to be the subject, so
    # the plainest phrasing a panicking parent uses was missed. The
    # trailing exclusion keeps ordinary, non-abduction uses out --
    # "my child was taken to hospital" is a medical or accident
    # question, and answering it with Childline would be useless.
    # "picked up" is deliberately NOT in this list. On its own it is
    # ordinary ("my child was picked up from school"), and the colloquial
    # "my kid got picked up by the cops" is a question about a lawful
    # apprehension under the Juvenile Justice Act, not an abduction --
    # routing that to Childline both alarms the parent and withholds the
    # law they asked for. An explicitly-named taker is still covered by
    # the active patterns above.
    r"\b(my|our) (child|daughter|son|kid|baby|boy|girl)\b[^.?!]{0,20}"
    r"\b(was|were|has been|have been|got) "
    r"(taken|grabbed|snatched|abducted|lured|carried off)\b"
    # Not an abduction when the taker or the destination is a lawful one.
    r"(?![^.?!]{0,25}\b(to (the |a )?(hospital|doctor|clinic|school|"
    r"police station|shelter|relative)|by (the )?(police|cops|cbi|"
    r"authorities|school|hospital|ambulance))\b)",
])

# Being followed or watched. Never sufficient on its own -- see
# _stalking_emergency for the second signal it requires and why.
_STALKING_SUBJECTS = _compile([
    r"\b(following|follows|followed|stalking|stalks|stalked|watching|"
    r"tailing|trailing)\b[^.?!]{0,20}\b(me|us)\b",
    r"\b(someone|somebody|a man|a woman|a guy|a stranger|he|she|they)\b"
    r"[^.?!]{0,25}\b(keeps?|kept|has been|have been|is|are|been|was)\b"
    r"[^.?!]{0,15}\b(following|stalking|watching|tailing|trailing)\b",
])

# The second signal stalking requires: expressed fear, or a pattern of
# repetition, or the person's home. One of these is what separates a
# person in danger from a person describing a social-media follower.
_FEAR_OR_PERSISTENCE = _compile([
    r"\b(scared|afraid|frightened|terrified|petrified|unsafe|"
    r"not safe|in danger|threatened|worried for my safety)\b",
    r"\b(keeps?|kept|constantly|repeatedly|again and again|all the time|"
    r"every ?day|each day|daily|for (days|weeks|months)|since (last|\w+ ?day))\b",
    # "every evening", "every night", "every morning", "every week".
    # A recurring time of day is the same repetition signal as "every
    # day" -- "a man follows me to the bus stop every evening" was
    # graded normal because only the literal "every day" was matched.
    r"\bevery (evening|night|morning|afternoon|week|time)\b",
    r"\bfollow\w*\b[^.?!]{0,15}\b(me )?(home|to my (house|home|office|work))\b",
])

# "Following me" is also how people describe social media. A stalking
# emergency must not fire on "someone is following me on Instagram".
_ONLINE_FOLLOW_CONTEXT = _compile([
    r"\b(instagram|insta|facebook|fb|twitter|x\.com|snapchat|tiktok|"
    r"youtube|linkedin|whatsapp|telegram|threads|account|profile|"
    r"page|handle|online|social media)\b",
])

_THREAT_TO_LIFE_SUBJECTS = _compile([
    # Threats to life and ongoing violence
    r"\bthreaten\w*\b[^.?!]{0,30}\b(to kill|to murder|to hurt|to harm|my life|with a (knife|gun|weapon))\b",
    r"\b(going to|about to|will|gonna) (kill|murder|stab|shoot|attack|hurt) (me|us|my|him|her|them)\b",
    r"\b(is|are|am|being) (attacking|attacked|beating|stabbing|strangling|chasing) (me|us|her|him|them)\b",
    r"\b(is|are) (breaking into|forcing (his|her|their) way into)\b",
    r"\b(my life|our lives|her life|his life) (is|are) in danger\b",
    r"\bafraid (for my life|he will kill|she will kill|they will kill)\b",
    r"\b(death threat|threat to (my |her |his )?life)\b",
    # Kidnapping / wrongful confinement
    r"\b(kidnap\w*|abduct\w*)\b[^.?!]{0,30}\b(my|me|him|her|them|our|is missing|right now)\b",
    r"\b(locked|held|trapped|confined) (me|us|her|him|them)\b",
    r"\b(has|have|is|was) (been )?(kidnapped|abducted|taken away)\b",
    # First-person passive victimisation: "I am being kidnapped", "we are
    # being attacked", "I'm being held hostage". Every active pattern
    # above requires the attacker to be the grammatical subject, so the
    # plainest phrasing a victim uses -- themselves as subject, the crime
    # in the present progressive -- graded normal (measured on "I am
    # being kidnapped", which went to ordinary retrieval and returned BNS
    # s.142 on concealing a kidnapped person).
    r"\b(i am|i'm|we are|we're) being (kidnapped|abducted|attacked|assaulted|beaten|"
    r"stabbed|shot( at)?|strangled|choked|chased|robbed|raped|molested|"
    r"held hostage|held captive|held against (my|our) will|taken against (my|our) will)\b",
    # Hostage / captivity, whoever the subject is.
    r"\b(held|taken|being held|holding (me|us|him|her|them)) hostage\b",
    r"\b(i am|i'm|we are|we're) (a )?(hostage|captive)\b",
    r"\btaken against (my|our|his|her|their) will\b",
    r"\b(they|he|she) (won'?t|will not|refuses? to) let (me|us) (leave|go|out)\b",
    r"\b(i|we) can('t|not) (get away|get out|escape|leave)\b",
    # Self-declared immediate danger: "I am in immediate danger", "we are
    # not safe". "Trapped" alone is excluded when it describes a
    # contract, debt or job -- a figurative trap is a legal question,
    # not a 112 call.
    r"\b(i am|i'm|we are|we're) (in (immediate |grave |serious )?danger|not safe|unsafe)\b",
    r"\b(i am|i'm|we are|we're) trapped\b"
    r"(?![^.?!]{0,20}\b(contract|loan|debt|lease|job|scheme|agreement|marriage|deal)\b)",
    # An armed person and hostility directed at the speaker: "someone has
    # a gun and is threatening me". The trailing clause is required so
    # "is it legal to carry a knife" and "he has a licensed gun" stay
    # ordinary legal questions.
    r"\b(someone|somebody|a man|a woman|a guy|a stranger|an intruder|he|she|they)\b[^.?!]{0,25}"
    r"\b(has|have|got|holding|carrying|pulled out|waving|pointing|brandishing) a?n? ?"
    r"(gun|knife|weapon|pistol|revolver|firearm|blade|axe|acid)\b"
    r"[^.?!]{0,45}\b(threat\w*|attack\w*|kill\w*|hurt\w*|stab\w*|shoot\w*|chas\w*|at (me|us)\b)",
    # A bare threat from an unnamed person: "someone is threatening me
    # right now", "they are threatening us". Scoped to unnamed subjects
    # (a named relation like a landlord or employer signals a dispute,
    # not an ambush) and stood down when the threat is a legal one --
    # "he is threatening me with a defamation case" is a question about
    # a dispute, not a call for help.
    r"\b(someone|somebody|a man|a woman|a guy|a stranger|he|she|they)\b[^.?!]{0,20}"
    r"\b(is|are|keeps?) threatening (me|us)\b"
    r"(?![^.?!]{0,35}\b(case|court|lawsuit|suit|legal action|defamation|complaint|fir|notice|"
    r"eviction|divorce)\b)",
    r"\b(i am|i'm|we are|we're) being threatened\b"
    r"(?![^.?!]{0,35}\b(case|court|lawsuit|suit|legal action|defamation|complaint|fir|notice|"
    r"eviction|divorce)\b)",
])

# A stranger inside or breaking into the speaker's home, described as
# present. This group did not exist before, and its absence was measured
# directly: "there is a thief in my house" retrieved BNSS s.129 on
# habitual offenders, and "there is a thief in my house right now"
# retrieved BNS s.331 on house-breaking -- semantically related law,
# uselessly and dangerously beside the point for someone hiding from an
# intruder.
#
# Present tense only, by construction: "there IS a thief in my house"
# routes to 112, while "there WAS a thief in my house yesterday" is a
# burglary report -- a legitimate legal question about a past crime --
# and falls through to ordinary retrieval. "My neighbour is a thief"
# carries no in-my-home clause and stays untouched.
_HOME_INTRUSION_SUBJECTS = _compile([
    # "there is a thief in my house", "there's an intruder inside our flat"
    r"\b(there('s| is| are)|someone('s| is)|somebody('s| is))\b[^.?!]{0,30}"
    r"\b(thief|thieves|intruder|burglar|robber|stranger|armed (man|men|person|people))\b"
    r"[^.?!]{0,25}\b(in|inside|entering) (my|our|the) (house|home|flat|apartment|room|"
    r"compound|shop|office|building)\b",
    # "someone is in my house", "an intruder is inside our home"
    r"\b(someone|somebody|an? (intruder|thief|burglar|robber|stranger)) (is|are)\b"
    r"[^.?!]{0,15}\b(in|inside) (my|our) (house|home|flat|apartment|room)\b",
    # "someone broke into my house", "a burglar is breaking into our home".
    # The past form is deliberately included: a break-in is reported
    # minutes, not months, after it happens, and the asymmetric-cost rule
    # (see _is_historical) puts the ambiguity on the emergency side. An
    # explicit historical marker still stands it down via assess_query.
    r"\b(broke|has broken|have broken|is breaking|are breaking|breaking) into\b[^.?!]{0,20}"
    r"\b(my|our) (house|home|flat|apartment|room|shop|office)\b",
    r"\bhome invasion\b",
    r"\bbreak[- ]?in\b[^.?!]{0,20}\b(happening|in progress|going on|right now)\b",
])

# Ongoing violence by someone the speaker does not name a relationship
# for. _DOMESTIC_ABUSE_SUBJECTS requires a relationship noun (husband,
# in-laws, ...), so the policy graded "my husband beats me" as an
# emergency and the identical "he beats me" as normal -- an asymmetry
# that penalised people for the pronoun they happened to use, in the
# highest-stakes category there is. The present-progressive form ("he is
# beating me") was already caught below; the simple present was not.
#
# Routed to threat_to_life rather than domestic_violence on purpose: no
# relationship is stated, so the response should not assume a home
# setting the way the domestic-violence message does. The violence must
# be directed at the speaker -- "the police beat him" and "what is the
# punishment for beating someone" carry no "me"/"us" and stay untouched.
_UNNAMED_ABUSER_SUBJECTS = _compile([
    r"\b(he|she|they|my (partner|ex|boyfriend|girlfriend|abuser|roommate|flatmate))\b"
    r"[^.?!]{0,25}"
    r"\b(beats?|beating|hits?|hitting|slaps?|slapping|kicks?|kicking|punch\w*|"
    r"chok\w+|strangl\w+|burns?|burning|tortur\w+|abus\w+|threaten\w*)\b"
    r"[^.?!]{0,15}\b(me|us)\b",
])

_ACTIVE_CRIME_SUBJECTS = _compile([
    r"\b(witness(ing)?|watching|seeing) a (crime|robbery|murder|assault|stabbing|shooting)\b",
    r"\b(robbery|assault|shooting|stabbing|murder|riot|attack|break[- ]in) (is )?(happening|in progress|going on)\b",
    r"\bsomeone is (robbing|looting|vandalising|vandalizing|setting fire)\b",
])

_LIFE_THREATENING_SUBJECTS = (
    _SELF_HARM_SUBJECTS
    + _MEDICAL_EMERGENCY_SUBJECTS
    + _CHILD_SAFETY_SUBJECTS
    + _THREAT_TO_LIFE_SUBJECTS
    + _UNNAMED_ABUSER_SUBJECTS
    + _ACTIVE_CRIME_SUBJECTS
    + _HOME_INTRUSION_SUBJECTS
)

# Tier B: a real legal matter where personalised procedural coaching would
# be inappropriate, but nothing indicates immediate physical danger.
_SERIOUS_LEGAL_SUBJECTS = _compile([
    # Live accusation / charge / investigation
    r"\b(been|being) (accused|charged|booked|chargesheeted|framed|prosecuted)\b",
    r"\b(accused|charged|booked|framed) (me|us|my \w+)\b",
    r"\bcase (has been )?(filed|registered|lodged) against (me|us|my)\b",
    # Allows words between the noun and "against me": at HEAD this
    # required them adjacent, so "an FIR has been filed against me"
    # graded normal while "an FIR against me" graded serious.
    r"\b(fir|complaint|case|chargesheet|charges?)\b[^.?!]{0,30}\bagainst (me|us|my \w+)\b",
    r"\b(i am|i'm|we are|we're) (under investigation|being investigated)\b",
    # Interrogation / custody / imminent arrest
    r"\b(police|cbi|officers?|investigating officer)\b[^.?!]{0,40}"
    r"\b(questioning|interrogating|summoned|detained|picked up|called) (me|us|him|her|my \w+)\b",
    r"\b(being|am|is|are) (questioned|interrogated|detained) by (the )?police\b",
    r"\b(at|in) the (police station|lock[- ]?up) (right )?now\b",
    r"\b(police are|police is|they are) (going to|about to|coming to) arrest\b",
    r"\b(about to be|going to be|will be) arrested\b",
    r"\bin (police |judicial )?custody\b",
    r"\b(raid|raided|searched)\b[^.?!]{0,25}\b(my|our) (house|home|office|shop)\b",
    # Sexual violence disclosed as a personal situation
    r"\b(i|she|he|they|my \w+) (was|were|has been|have been|got) (raped|sexually assaulted|molested)\b",
    r"\b(raped|sexually assaulted|molested) (me|her|him|them|my \w+)\b",
    # Serious personal criminal exposure
    r"\b(will|would|could|am|can) i (go to|be sent to) (jail|prison)\b",
    r"\bam i going to (jail|prison)\b",
    r"\bshould i (plead guilty|confess|surrender|sign|admit|say anything)\b",
    r"\bwhat (exactly )?should (i|we|he|she|they) (say|tell|answer)\b",
    r"\b(i|we) (was|were|got|have been|had been) arrested\b",
    r"\bpolice arrested (me|us|my \w+)\b",
])

# A serious incident the person experienced, described as over: a past
# burglary, a past robbery or assault, stolen property. Not an
# emergency -- nothing is happening now -- but not an ordinary
# educational query either: the person is describing their own matter,
# and the right response is the serious-tier one (the caution and the
# legal-aid route lead, the general law follows behind the confidence
# gate), not a plain legal answer. Measured motivating case: "there was
# a thief in my house yesterday" graded normal and went straight to
# ordinary retrieval.
#
# First-person and own-property phrasings only. A third-party report
# ("my friend was assaulted") or a hypothetical ("what should I do if
# someone committed theft") stays on the normal path.
_PAST_PERSONAL_INCIDENT_SUBJECTS = _compile([
    # The past-tense mirror of _HOME_INTRUSION_SUBJECTS: "there WAS a
    # thief in my house" is a burglary report, not a live intrusion.
    r"\bthere (was|were|had been)\b[^.?!]{0,30}"
    r"\b(thief|thieves|intruder|burglar|robber|stranger)\b"
    r"[^.?!]{0,25}\b(in|inside) (my|our) (house|home|flat|apartment|room|"
    r"compound|shop|office)\b",
    r"\b(my|our) (house|home|flat|apartment|room|shop|office)\b[^.?!]{0,15}"
    r"\b(was|were|got|has been|had been) "
    r"(burgled|burglarised|burglarized|robbed|broken into|ransacked|looted)\b",
    # The speaker as past victim: "I was robbed last month", "we were
    # attacked". The present-progressive forms of the same verbs are
    # emergencies and are caught first, above.
    r"\b(i|we) (was|were|got|have been|had been) "
    r"(robbed|burgled|mugged|attacked|assaulted|beaten( up)?|stabbed|"
    r"held at (knife|gun) ?point)\b",
    # Personal property stolen: past theft affecting the person directly.
    r"\b(my|our) (phone|mobile|car|bike|scooter|motorcycle|vehicle|wallet|"
    r"purse|bag|laptop|jewellery|jewelry|gold|money) "
    r"(was|were|got|has been|had been) (stolen|snatched|robbed|taken)\b",
])

# A possessive reference to one's own legal matter, split out of
# _SERIOUS_LEGAL_SUBJECTS above because it behaves differently from
# every other member of that group.
#
# The other patterns describe jeopardy outright ("been accused", "about
# to be arrested", "should I plead guilty"). This one describes only
# *possession* of a legal matter, which is a much weaker signal -- and
# because "my case" is inherently personal, `_is_purely_educational`
# can never be true for it, so as an ordinary member of the group it
# fired unconditionally. Measured consequences: "must the police tell me
# the grounds of my arrest" and "can I get a copy of the police report
# before my trial" were both graded `serious` and redirected to a
# lawyer, although each asks only what the law entitles the person to.
#
# "complaint" is deliberately no longer in this list. A complaint the
# person *filed* is not jeopardy -- it made "the municipality is
# ignoring my complaint about a broken road" a serious legal matter. A
# complaint *against* them is still caught, by the
# "(fir|complaint|case|chargesheet) against (me|us|my ...)" pattern
# above, which is the phrasing that actually indicates exposure.
_OWN_LEGAL_MATTER = _compile([
    r"\bmy (fir|case|bail|trial|hearing|chargesheet|arrest|conviction|sentence)\b",
])

# Asking what the law entitles you to *within* your own matter is an
# informational question, not a request for personalised coaching. Kept
# separate from _INFORMATIONAL_FRAME on purpose: that group also gates
# the emergency tier, and widening it there could let a live emergency
# read as educational. This group only ever stands down the weak
# possessive signal above.
_ENTITLEMENT_FRAME = _compile([
    r"\b(am i|are we) entitled\b",
    r"\bdo(es)? (i|we) have (a|the|any) right\b",
    r"\bwhat (is|are) my rights?\b",
    r"\b(can|may|must|should|do|does|will) (the )?"
    r"(police|court|magistrate|judge|officer|state|government|prosecution|jail|prison)\b",
    r"\b(can|may|am i able to) (i )?(get|obtain|see|inspect|receive|ask for|request)\b"
    r"[^.?!]{0,30}\b(copy|copies|document|record|records|information|file|papers)\b",
    r"\bhow (do|can|would) (i|we) (get|obtain|see|inspect|receive|request|ask for|apply for)\b"
    r"[^.?!]{0,30}\b(copy|copies|document|record|records|information|file|papers)\b",
    r"\bhow long (can|may|does|do|is|are)\b",
    r"\b(entitled to|right to) (a |an |the )?(copy|copies|information|records?|lawyer|bail)\b",
])

# Being solicited for a bribe is not personal jeopardy either: the
# person is the one being asked, not the one accused. "The police
# officer wants money to register my FIR" carries "my FIR" but reports
# extortion by an official, and must grade the same as "a government
# officer is demanding a bribe to process my file", which carries no
# possessive at all. That inconsistency -- serious for one phrasing,
# normal for the other, for the same conduct -- was a measured Stage 2
# defect. Both now grade normal, and the corpus-coverage guard abstains
# honestly on both because the Prevention of Corruption Act 1988 is not
# ingested.
_BRIBE_SOLICITATION = _compile([
    r"\b(bribe[sd]?|bribery|bribing|rishwat|ghoos|ghus|kickbacks?|"
    r"speed money|chai[- ]?paani|hafta)\b",
    r"\b(demand(s|ed|ing)?|want(s|ed|ing)?|ask(s|ed|ing)?|expect(s|ed|ing)?)\b"
    r"[^.?!]{0,32}\b(money|cash|bribe|payment)\b",
])

# Domestic abuse and cyber fraud sit between the tiers: they need their
# own route (a specific helpline, a specific portal) rather than the
# generic serious-matter message, but only when the person describes it
# as their own situation.
_DOMESTIC_ABUSE_SUBJECTS = _compile([
    r"\b(husband|wife|partner|spouse|in[- ]laws?|father|mother|brother|boyfriend|girlfriend)\b"
    r"[^.?!]{0,30}\b(hits?|hitting|beats?|beating|abus\w*|threaten\w*|starv\w*|burn\w*|assault\w*)\b"
    r"[^.?!]{0,15}\b(me|us|her|him)\b",
    r"\b(being|getting) (abused|beaten|hit|tortured)\b[^.?!]{0,25}\b(at home|by my|at my (house|home))\b",
    r"\b(i am|i'm|she is|he is) (a )?(victim of|facing|suffering|experiencing) domestic violence\b",
    r"\bdomestic violence (against|towards) (me|her|him|my)\b",
    r"\bmy (husband|wife|partner|in[- ]laws?) (is|are) (violent|abusive|beating me|hitting me)\b",
])

_CYBER_FRAUD_SUBJECTS = _compile([
    r"\b(my|our) (bank|upi|paytm|wallet) (account )?(was|has been|got|is) (hacked|compromised|emptied)\b",
    r"\b(i|we) (lost|was cheated of|were cheated of|got scammed out of) (money|rs\.?|inr|\d)",
    r"\b(someone|somebody|they|a scammer|a caller) (stole|took|withdrew|transferred|siphoned) money from (my|our)\b",
    r"\b(i|we) (was|were|got|have been) (scammed|defrauded|cheated) (online|on upi|by a caller|on a website)\b",
    r"\bfell for (an? )?(otp|upi|phishing|lottery|job) (scam|fraud)\b",
    r"\bmoney (was|has been|got) (debited|withdrawn|taken) from my (account|card|wallet)\b",
    r"\b(my|our) (photos?|videos?|account|profile) (was|were|has been|have been) (leaked|morphed|misused|hacked)\b",
])

# --- Signal 3: framing --------------------------------------------------
# The person is studying a topic rather than reporting a situation.
_INFORMATIONAL_FRAME = _compile([
    r"\bwhat (does|do|did) (the |indian |a |an )?(law|act|section|article|constitution|bns|bnss|bsa|code)\b",
    r"\bwhat (is|are|was|were) (a |an |the )?\w+",
    r"\bwhat counts as\b",
    r"\bexplain\b",
    r"\b(define|definition of|meaning of)\b",
    r"\b(difference|differences) between\b",
    r"\bunder (which|what) (section|article|act)\b",
    r"\bwhich (section|article|act|law)\b",
    r"\bwhat (rights|protections|remedies|provisions|punishment|penalty|penalties|procedure|happens)\b",
    r"\btell me about\b",
    r"\b(in general|generally speaking|in law|legally speaking)\b",
    r"\bhow does\b[^.?!]{0,30}\bwork\b",
    r"\bcan the police\b",
    r"\bis it (legal|illegal|an offence)\b",
])

# The person is describing their own (or a named relative's) situation.
_PERSONAL_FRAME = _compile([
    r"\b(i|we)\b[^.?!]{0,25}\b(was|were|am|are|have|has|had|got|need|want|face|facing|think|feel"
    r"|did|do|don't|can't|cannot)\b",
    r"\bmy (husband|wife|partner|son|daughter|child|kid|baby|father|mother|brother|sister|friend"
    r"|neighbour|neighbor|landlord|employer|boss|case|fir|complaint|account|house|home|family"
    r"|in[- ]laws?|phone|money|card|wallet|shop|office)\b",
    r"\b(happened to me|happening to me|done to me|against me|told me|arrested me|beat me|hit me"
    r"|threatened me|questioning me|following me)\b",
    r"\b(someone|somebody|a man|a woman|they|he|she) (is|has|was|just|are|have|were)\b",
    r"\bthey (are|were) \w+ing (me|us|my)\b",
    r"\b(help|save) (me|us)\b",
    r"\bwill i\b",
    r"\bam i\b",
])

# The situation is presented as live.
_IMMEDIACY = _compile([
    r"\bright now\b",
    r"\bat (the|this) moment\b",
    r"\bcurrently\b",
    r"\bas (i|we) (write|speak|type)\b",
    r"\b(is|are) happening\b",
    r"\bhappening (now|right now)\b",
    r"\b(about to|going to|coming to) (kill|hurt|attack|arrest|break in|come here)\b",
    r"\b(tonight|today|just now|a few minutes ago|minutes ago|moments ago)\b",
    r"\b(he|she|they)('s| is| are|'re) (here|outside|at the door|coming|banging)\b",
    r"\b(i'm|i am|we're|we are) (scared|terrified|in danger|hiding|trapped|bleeding)\b",
    r"\bplease help\b",
    r"\b(urgent|urgently|emergency)\b",
])


@dataclass(frozen=True)
class SafetyAssessment:
    """The outcome of the pre-retrieval safety policy.

    ``severity`` is one of the four ``SEVERITY_*`` constants. ``category``
    names the specific route taken -- it becomes the pipeline's ``reason``
    field and picks the helpline -- and is None only at normal severity.
    ``message`` is the fixed text to return, and is None at normal
    severity because a normal query is answered from retrieved law, not
    from a template.
    """

    severity: str
    category: str | None = None
    message: str | None = None
    #: Whether the response points at an authority, helpline or legal-aid
    #: service rather than at legal text alone.
    authority_guidance: bool = False

    @property
    def blocks_retrieval(self) -> bool:
        """True when no retrieval should happen at all.

        Emergencies and harmful-assistance requests hard-stop. Serious
        matters do not: showing someone the verbatim text of the law that
        governs their situation, behind the same confidence gate as any
        other query, is safe and useful. What is withheld from a serious
        matter is personalised procedural coaching, not the law itself.
        """
        return self.severity in (SEVERITY_EMERGENCY, SEVERITY_HARMFUL_REQUEST)


NORMAL_ASSESSMENT = SafetyAssessment(severity=SEVERITY_NORMAL)


# --- Fixed response text -----------------------------------------------
# Configuration data, not generated text. Only 112 (the national
# all-in-one emergency number), 181 (Women's Helpline), 1098 (Childline)
# and 1930 (Cyber Fraud Helpline) are named -- each an official national
# number listed in docs/LEGAL_SOURCES.md. No number is invented, and no
# local number is guessed.
EMERGENCY_CONTACTS: dict[str, str] = {
    "self_harm": (
        "This sounds like it may be a personal safety concern, not a legal "
        "information question, so I can't continue as a legal information "
        "chatbot for this message. If you are in danger or thinking about "
        "harming yourself, please contact 112 (Emergency) right away, or "
        "reach out to someone you trust immediately."
    ),
    "child_safety": (
        "This describes a possible child-safety emergency, not a legal "
        "information question. Please contact 112 (Emergency) or Childline "
        "at 1098 immediately. If a child is with you and in danger, get "
        "them somewhere safe first."
    ),
    "threat_to_life": (
        "This appears to describe an immediate threat to someone's safety, "
        "not a general legal information question. Please contact 112 "
        "(Emergency) or your local police right away, and move to a safe "
        "place if you can. Once you are safe, a lawyer or a legal services "
        "authority can help with the legal side."
    ),
    "domestic_violence": (
        "This describes a possible safety emergency at home, not a general "
        "legal information question. Please contact 112 (Emergency) or the "
        "Women's Helpline at 181 right away, and move somewhere safe if you "
        "can. A Protection Officer or a legal services authority can help "
        "with protection and residence orders once you are safe."
    ),
    "medical_emergency": (
        "This sounds like a medical emergency, not a legal information "
        "question. Please call 112 (Emergency) immediately."
    ),
    "active_crime": (
        "This appears to describe a crime in progress or someone in "
        "immediate danger, not a general legal information question. Please "
        "contact 112 (Emergency) or your local police right away, and get "
        "to a safe place if you can."
    ),
    "cyber_fraud": (
        "This describes a possible cybercrime or financial fraud. Please "
        "call 1930 (Cyber Fraud Helpline) or report it at the National "
        "Cyber Crime Reporting Portal (cybercrime.gov.in) as soon as you "
        "can -- reporting quickly matters for any chance of recovering "
        "money."
    ),
}

HARMFUL_REQUEST_MESSAGE = (
    "I can't help with this. Hiding or destroying evidence, fabricating "
    "statements or alibis, interfering with a witness, and evading a "
    "lawful investigation are themselves offences under Indian law, and "
    "they usually make a person's position much worse. If you are facing "
    "an investigation or an accusation, that is exactly the situation a "
    "defence lawyer exists for -- contact one, or India's free legal aid "
    "services (Tele-Law, Nyaya Bandhu, or your District Legal Services "
    "Authority), and ask what your options actually are."
)

SERIOUS_MATTER_MESSAGE = (
    "This appears to involve a serious legal matter affecting you "
    "directly. I can show you the general law on the topic, but I can't "
    "safely advise you on the specific steps to take in your case -- that "
    "depends on facts only a lawyer who hears your full account can weigh. "
    "Please contact a qualified lawyer, your District Legal Services "
    "Authority (free legal aid, under the Legal Services Authorities Act, "
    "1987), or the appropriate authority for case-specific assistance."
)

PERSONALIZED_ADVICE_MESSAGE = (
    "This looks like it's about your own specific situation rather than "
    "general legal information, and I'm not able to give personal legal "
    "advice or predict what will happen in your case. Please contact a "
    "qualified legal adviser, or India's free legal aid services -- "
    "Tele-Law or Nyaya Bandhu -- for guidance on your situation."
)


# --- Signal helpers ----------------------------------------------------

def _is_instructional(text: str) -> bool:
    return _any(_INSTRUCTIONAL_FRAME, text)


def _is_informational(text: str) -> bool:
    return _any(_INFORMATIONAL_FRAME, text)


def _is_personal(text: str) -> bool:
    return _any(_PERSONAL_FRAME, text)


def _is_immediate(text: str) -> bool:
    return _any(_IMMEDIACY, text)


def _life_threatening_subject(text: str) -> bool:
    return _any(_LIFE_THREATENING_SUBJECTS, text) or _stalking_emergency(text)


def _serious_legal_subject(text: str) -> bool:
    """True when the query describes a serious personal legal matter.

    An outright jeopardy phrasing is enough on its own. A bare
    possessive reference to one's own matter ("my trial") is not: it
    counts only when the question is not asking what the law entitles
    the person to, and is not reporting a bribe solicitation. See
    _OWN_LEGAL_MATTER for the measured failures that distinction fixes.
    """
    if _any(_SERIOUS_LEGAL_SUBJECTS, text):
        return True
    if _any(_PAST_PERSONAL_INCIDENT_SUBJECTS, text):
        return True
    if not _any(_OWN_LEGAL_MATTER, text):
        return False
    return not (_any(_ENTITLEMENT_FRAME, text) or _any(_BRIBE_SOLICITATION, text))


def _requests_harmful_assistance(text: str) -> bool:
    """A harmful act *and* a request to be shown how to do it.

    Both halves are required. "What is the punishment for destroying
    evidence?" names the act but asks for the law, so it goes to
    retrieval; "How do I destroy evidence?" names the act and asks for
    instructions, so it is refused.
    """
    return _any(_HARMFUL_ACTS, text) and _is_instructional(text)


# The situation is described as over. Until this existed the emergency
# tier had no notion of tense at all, and that hurt exactly the people
# it was meant to protect: "my husband used to beat me years ago, what
# are my options" was answered with a helpline redirect instead of the
# law on protection and residence orders, and "my child was kidnapped in
# 2019 and the case is still going on" was treated as a live abduction.
# Both are people seeking legal information about something that already
# happened, and an emergency redirect denies it to them.
_HISTORICAL_FRAME = _compile([
    r"\b(used to|no longer|not any ?more|since then|back then|back in)\b",
    r"\b(years?|months?|weeks?|decades?) ago\b",
    # "he hit me last year, what are my options" was graded an emergency
    # because only the "... ago" phrasing counted as past (M12). "last
    # week" is deliberately NOT here: a week-old assault with the abuser
    # still around is close enough to live risk that the asymmetric-cost
    # rule keeps it on the emergency side.
    r"\blast (year|month)\b",
    r"\b(a|one) (year|month) (back|earlier)\b",
    r"\bin (19|20)\d{2}\b",
    r"\b(at that time|at the time|in those days|those days)\b",
    r"\bwhen (i|he|she|they) (was|were) (a )?(child|kid|young|small|minor)\b",
    r"\b(case|matter|trial|appeal|complaint|fir) (is|has been) "
    r"(still )?(going on|ongoing|pending|in court|filed)\b",
    r"\b(it|that|this) (happened|was) (a )?(long time ago|years ago|in the past)\b",
])


def _is_historical(text: str) -> bool:
    """True when the person is describing something that is over.

    Immediacy always wins. "He beat me for years and he is outside right
    now" is not a historical account whatever else it contains, so an
    immediacy marker disables this entirely rather than being weighed
    against it. That ordering is the whole safety property here: the
    cost of reading a live emergency as history is far higher than the
    cost of reading history as an emergency.
    """
    if _any(_IMMEDIACY, text):
        return False
    return _any(_HISTORICAL_FRAME, text)


def _stalking_emergency(text: str) -> bool:
    """True when the query describes being followed AND something that
    makes it dangerous rather than merely observed.

    Deliberately a composition, not a subject list. "Following" is one of
    the most overloaded words a citizen can use -- it is stalking, it is
    what an Instagram account does, and it is what a car behind you in
    traffic does. Requiring a second signal (expressed fear, a pattern of
    repetition, or the person's home) is what makes the emergency route
    safe to take, and standing down on social-media context removes the
    largest remaining false positive.

    "What is stalking?" cannot reach here: it has no target pronoun, no
    fear and no repetition, and assess_query's educational gate sits
    behind this as a second layer.
    """
    if _any(_ONLINE_FOLLOW_CONTEXT, text):
        return False
    return _any(_STALKING_SUBJECTS, text) and _any(_FEAR_OR_PERSISTENCE, text)


def _emergency_category(text: str) -> str | None:
    """Which emergency route a life-threatening query takes, if any.

    Checked most-specific first, so a query mentioning both a child and a
    general threat still gets the child-safety helpline.
    """
    if _any(_SELF_HARM_SUBJECTS, text):
        return "self_harm"
    if _any(_MEDICAL_EMERGENCY_SUBJECTS, text):
        return "medical_emergency"
    if _any(_CHILD_SAFETY_SUBJECTS, text):
        return "child_safety"
    # Checked before the generic threat route so that "my husband is
    # beating me" gets the Women's Helpline rather than the general
    # threat-to-life message -- both point at 112, but the specific
    # service is the more useful one to name first.
    if _any(_DOMESTIC_ABUSE_SUBJECTS, text):
        return "domestic_violence"
    if _any(_THREAT_TO_LIFE_SUBJECTS, text) or _any(_UNNAMED_ABUSER_SUBJECTS, text):
        return "threat_to_life"
    if _any(_ACTIVE_CRIME_SUBJECTS, text):
        return "active_crime"
    # An intruder in the home is a crime in progress: the active_crime
    # message names 112 and tells the person to get somewhere safe,
    # which is the right response whether or not anything is stolen.
    if _any(_HOME_INTRUSION_SUBJECTS, text):
        return "active_crime"
    # Stalking routes to active_crime: its message names 112, tells the
    # person to get somewhere safe, and does not assume a home setting
    # the way the domestic-violence message does.
    if _stalking_emergency(text):
        return "active_crime"
    return None


def _is_purely_educational(text: str) -> bool:
    """The query reads as study, not as a report of a real situation.

    This is the guard that keeps ordinary legal education out of the
    emergency path: "Explain what the law says about domestic violence"
    is informational, impersonal and not urgent, so whatever heavy
    subject it names, it is a question about the law. Adding any personal
    or immediacy marker flips it back.
    """
    return _is_informational(text) and not _is_personal(text) and not _is_immediate(text)


# --- The policy --------------------------------------------------------

def assess_query(text: str) -> SafetyAssessment:
    """Classify a query's safety severity before any retrieval happens.

    The order below *is* the policy, and it matters:

    1. **Harmful assistance** -- refused regardless of anything else, so a
       request for obstruction techniques cannot be smuggled in under an
       emergency or educational framing.
    2. **Life-threatening subject, not purely educational** -- emergency
       redirect. A question about the same subject that is informational,
       impersonal and not urgent stays educational.
    3. **Domestic abuse / cyber fraud, presented as the person's own** --
       their own helpline routes, for the same reason: these need a
       specific service, not the generic message.
    4. **Serious legal subject, presented as personal** -- cautious
       response plus authority guidance. Retrieval still runs so the
       relevant law can be cited alongside the caution.
    5. Everything else -- normal, straight through to the existing
       topic-relevance guard, coverage guard, retrieval and confidence
       gate.
    """
    if _requests_harmful_assistance(text):
        return SafetyAssessment(
            severity=SEVERITY_HARMFUL_REQUEST,
            category="obstruction_or_fabrication",
            message=HARMFUL_REQUEST_MESSAGE,
            authority_guidance=True,
        )

    educational = _is_purely_educational(text)
    # A settled account of something that is over routes like an
    # ordinary legal question, so the person actually gets the law they
    # came for. Immediacy defeats it (see _is_historical).
    historical = _is_historical(text)

    if (_life_threatening_subject(text) or _any(_DOMESTIC_ABUSE_SUBJECTS, text)) and not (
        educational or historical
    ):
        category = _emergency_category(text) or "active_crime"
        return SafetyAssessment(
            severity=SEVERITY_EMERGENCY,
            category=category,
            message=EMERGENCY_CONTACTS[category],
            authority_guidance=True,
        )

    if _any(_CYBER_FRAUD_SUBJECTS, text) and not (educational or historical):
        return SafetyAssessment(
            severity=SEVERITY_EMERGENCY,
            category="cyber_fraud",
            message=EMERGENCY_CONTACTS["cyber_fraud"],
            authority_guidance=True,
        )

    # An emergency-tier subject stood down ONLY by the historical frame
    # is still the asker's own serious matter. "My husband used to beat
    # me years ago" is rightly not an emergency, but routing it to plain
    # retrieval treated it as a textbook question -- the person gets the
    # serious-tier response instead: the caution and the legal-aid route
    # lead, and the law on the topic follows behind the same gate.
    # Immediacy already defeated the historical reading above, so
    # nothing live can reach this branch.
    if (
        historical
        and not educational
        and (_life_threatening_subject(text) or _any(_DOMESTIC_ABUSE_SUBJECTS, text))
    ):
        return SafetyAssessment(
            severity=SEVERITY_SERIOUS,
            category="serious_legal_matter",
            message=SERIOUS_MATTER_MESSAGE,
            authority_guidance=True,
        )

    if _serious_legal_subject(text) and not educational:
        return SafetyAssessment(
            severity=SEVERITY_SERIOUS,
            category="serious_legal_matter",
            message=SERIOUS_MATTER_MESSAGE,
            authority_guidance=True,
        )

    return NORMAL_ASSESSMENT


def classify_risk(text: str) -> str | None:
    """Backwards-compatible view of :func:`assess_query`.

    Returns the matched risk category, or None when the text reads as a
    general informational legal question.
    """
    return assess_query(text).category


#: Categories that hard-stop with an emergency/official-contact redirect.
EMERGENCY_CATEGORIES = set(EMERGENCY_CONTACTS)
