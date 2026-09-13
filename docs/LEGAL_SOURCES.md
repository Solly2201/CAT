# Legal-source inventory (final)

> **Final, updated by the ICCSDI 2026 revision.** This inventory
> describes the corpus after the revision's curated section-split
> repairs: **10 ingested Acts, 1,832 chunks.** The five chunks added
> over the frozen commit `c24eda2` (1,827) are BNS 217/255, JJ Act
> 61/86 and RTI s.14 — the previously documented extraction defects,
> now fixed (see "Curated section-split repairs" below). The per-source
> counts in "Ingestion status" below are verified against
> `services/ai/data/index/chunk_manifest.jsonl`.

CAT accepts legal RAG evidence only from an Admin-approved official-source allow-list. Every imported document must retain its official URL, publisher, document version or “as on” date, import date, checksum, and extraction status.

## Approved sources

| Source | Official record | Initial use |
| --- | --- | --- |
| Constitution of India | [India Code PDF](https://www.indiacode.nic.in/bitstream/123456789/16124/1/the_constitution_of_india.pdf) | Fundamental rights and constitutional context |
| Bharatiya Nyaya Sanhita, 2023 (Act No. 45 of 2023) | [India Code PDF](https://www.indiacode.nic.in/bitstream/123456789/20062/1/a202345.pdf) | Offences and classifications |
| Bharatiya Nagarik Suraksha Sanhita, 2023 (Act No. 46 of 2023) | [India Code PDF](https://www.indiacode.nic.in/bitstream/123456789/20099/1/A202346.pdf) | Criminal procedure, arrest, FIR/NCR, bail and warrants |
| Bharatiya Sakshya Adhiniyam, 2023 (Act No. 47 of 2023) | [India Code PDF](https://www.indiacode.nic.in/bitstream/123456789/20063/1/aa202347.pdf) | Basic evidence-law awareness |
| Information Technology Act, 2000 (Act No. 21 of 2000) | [India Code](https://www.indiacode.nic.in/handle/123456789/1999) | Cyber offences, digital signatures, electronic governance |
| Protection of Women from Domestic Violence Act, 2005 (Act No. 43 of 2005) | [India Code](https://www.indiacode.nic.in/handle/123456789/2021) | Domestic violence definitions and protection orders |
| Legal Services Authorities Act, 1987 (Act No. 39 of 1987) | [India Code](https://www.indiacode.nic.in/handle/123456789/1925) | Free legal aid entitlement, Lok Adalats |
| Consumer Protection Act, 2019 (Act No. 35 of 2019) | [India Code](https://www.indiacode.nic.in/handle/123456789/18964) | Consumer complaints, District/State/National Commissions |
| Juvenile Justice (Care and Protection of Children) Act, 2015 (Act No. 2 of 2016) | [India Code](https://www.indiacode.nic.in/handle/123456789/2148) | Children in conflict with law, children in need of care and protection |
| Right to Information Act, 2005 (Act No. 22 of 2005) | [Central Information Commission PDF](https://cic.gov.in/sites/default/files/RTI-Act_English.pdf) | Access to information held by public authorities, response time limits, exemptions, appeals and penalties |
| India Code | [Official catalogue](https://www.indiacode.nic.in/) | Later approved Acts and official amendments |
| Supreme Court of India | [Official site](https://www.sci.gov.in/) | Official judgments when explicitly approved and versioned |

The corpus is deliberately limited, and it stayed limited. **CAT does not claim to cover all Indian law**, and does not claim complete coverage of the Acts it does ingest — see "Deferred and unsupported domains" and the per-source coverage notes below. The last two rows of the table above (India Code, Supreme Court of India) are the approved *catalogues* for future additions; **no judgment and no Act beyond the ten listed below has been ingested.**

> **Correction (Increment 2):** the BNSS PDF originally supplied for ingestion was *"AS INTRODUCED IN LOK SABHA"* (Bill No. 122 of 2023) — a superseded draft, not the enacted Sanhita. Section numbering and text differ from the enacted Act No. 46 of 2023. It has been replaced with the official India Code text above. The BNS and Constitution PDFs supplied were verified as the actual enacted/official text and did not need replacing.

## Ingestion status (final — 10 sources, 1,832 chunks)

Run `python services/ai/scripts/ingest_corpus.py` to regenerate the index
from source. The counts below are the **final** ones and match
`data/index/index_manifest.json` (`chunk_count: 1832`) and a per-source
count over `chunk_manifest.jsonl`. The narrative in each row records how
that source reached its final state, so some of it reads historically;
the numbers do not.

| Source | Chunks ingested | Coverage |
| --- | --- | --- |
| Constitution | 366 articles | Full text supplied. Marginal-note article titles are not reliably extracted for most articles (two-column PDF layout, see below); a small hand-verified table recovers titles for Part III (Fundamental Rights, Articles 12-22). Article numbers and body text are exact throughout. |
| Bharatiya Nagarik Suraksha Sanhita | 531 sections | **Full**, including Ch. XIII investigation/FIR (ss.173-196) and Ch. XXXV bail and bonds (ss.478-496). Replaced with a single-column "bare Act" India Code PDF (see "New single-column PDFs" below); section titles are inline in the source text and recovered for all 531 sections (100%). |
| Bharatiya Nyaya Sanhita | 358 sections | **Full**, single-column source, titles recovered for all 358 sections. Two sections (217, 255) whose header titles wrap across a line break are split out by a curated, asserted repair — see "Curated section-split repairs" below. |
| Bharatiya Sakshya Adhiniyam | 170 sections | **Full**, single-column source, titles recovered for all 170 sections (100%). |
| Information Technology Act, 2000 | 92 sections | Full text as supplied. |
| Protection of Women from Domestic Violence Act, 2005 | 37 sections | Full text as supplied. |
| Legal Services Authorities Act, 1987 | 32 sections | Full text as supplied. |
| Consumer Protection Act, 2019 | 107 sections | **Full**, single-column source, titles recovered for all 107 sections (100%). |
| Juvenile Justice (Care and Protection of Children) Act, 2015 | 112 sections | **Full**, single-column source, titles recovered for all 112 sections. Two amendment-substituted sections (61, 86) whose headers open with a footnote bracket are split out by a curated, asserted repair — see "Curated section-split repairs" below. |
| Right to Information Act, 2005 | 27 sections | Chapters I–VI from the Central Information Commission's published copy, excluding the Schedules. Four sections are deliberately excluded: **ss.13, 16 and 27**, which the RTI (Amendment) Act 2019 replaced and which this pre-2019 copy still states in superseded form, and **s.25** (Monitoring and reporting), dropped for measured retrieval harm — see below. s.14 (unamended by the 2019 Act) is recovered by a curated split repair — the source omits the full stop before the em-dash the header pattern needs, and its text previously vanished inside the excluded s.13's chunk; its "(1)" marker OCRs as "CO" and is left as extracted. |
| **Total** | **1,832 chunks** | 10 ingested Acts. Verified against `data/index/chunk_manifest.jsonl`: bnss 531, constitution 366, bns 358, bsa 170, jj2015 112, cpa2019 107, it_act 92, pwdva 37, lsa 32, rti 27. |

### Deferred and unsupported domains

Named here rather than left as a silent absence. **Two different
mechanisms keep these from being answered, and the distinction is
deliberate.**

**(a) Named by the corpus-coverage guard.** These are the subjects where
the 313-query citizen evaluation *demonstrated* a confident wrong-Act
answer: the query is a real legal question in this service's subject
area, shares vocabulary with ingested statutes, and therefore cleared the
confidence floor from the wrong Act. `app/safety/corpus_coverage.py`
matches them by name **before retrieval runs** and returns a "not in this
corpus" message pointing at a more appropriate route.

| Domain | Guard category | Why it is not covered |
| --- | --- | --- |
| Sexual offences against children | `pocso` | Governed principally by POCSO, which is not ingested. |
| Motor vehicles / driving | `motor_vehicles` | Not ingested. |
| Matrimonial law (divorce and related) | `matrimonial` | Not ingested. |
| SC/ST (Prevention of Atrocities) | `sc_st_atrocities` | Not ingested; "atrocities" occurs nowhere in the corpus. |
| Court fees and civil procedure (CPC) | `court_fees_civil_procedure` | Not ingested. |
| Information Commissioners' terms of service | `rti_amended_service_provisions` | ss.13/16/27, which this pre-2019 RTI copy states in superseded form and which are therefore excluded at ingestion. Returns a distinct "deliberately excluded provision" message. |

**(b) Not ingested, and deliberately left to the confidence gate.** The
guard is emphatically **not** a list of every Indian Act. It carries one
entry per demonstrated failure and nothing else. For the subjects below,
a probe confirmed the confidence gate already abstains correctly with no
guard at all — all seven labour and civic-service questions in it
abstained — so adding patterns would have been speculative rather than
evidence-driven. The Learn module additionally states each of these as a
`deferredTopics` entry on the relevant category, so a citizen browsing is
told the gap exists rather than left to infer it.

| Domain | Why it is not covered |
| --- | --- |
| Workplace and labour rights (notice periods and other terms) | No labour legislation is ingested. Minimum-wage questions moved to the coverage guard (`minimum_wages`) after the ICCSDI revision's repeated-seed experiment showed the gate margin is not seed-robust: one of five retrained seeds answered a minimum-wage query from `bns:146` over the floor. |
| Tenancy and rent control | Governed by State legislation outside the ingested corpus. |
| Data protection | India's dedicated data-protection legislation is not ingested, and ss.43 and 43A are missing from the ingested IT Act PDF. |
| Stamp duty, arbitration, municipal services | Not ingested. |
| RTI fee amounts | The Act says only "such fee as may be prescribed"; the figures live in rules made under it, which are not ingested. No fee amount is stated anywhere in the product. |
| Case law of any kind | No judgment is ingested. CAT answers from statute only. |

If a future confidence-threshold change turns any group (b) subject into
a confident wrong answer, the rule to add is that specific one — the same
"curated, extend only when evaluation names a case" discipline the guard
was built under.

Coverage gaps are also surfaced live via each source's `coverage_note` field on `/corpus/sources` and on every search/section result, so the UI never implies more coverage than actually exists.

### New single-column PDFs (BNS, BNSS, BSA, CPA2019, JJ Act)

The original PDFs supplied for these five sources used the two-column
India Code gazette layout described below, which required a
purpose-built `pdfplumber`-based extractor and only recovered section
titles for 40-57% of sections per source. All five were replaced this
session with the plain single-column "bare Act" India Code PDFs
(consolidated "as on 6th October, 2025", i.e. incorporating amendments
made since original enactment, not just the as-passed 2023 text) —
the same clean, directly-`pypdf`-extractable format already used for
`it_act`/`pwdva`/`lsa`. Section headers in this format are inline
(`"43. Arrest how made.—(1) In making an arrest..."`), so the existing
`chunk_sanhita` chunker (`app/ingestion/chunk.py`) now handles all
five, and every source in the corpus that isn't the Constitution uses
the same extraction+chunking path.

This raised section-title recovery from 40-57% to 98-100% across all
five sources and, verified against the earlier two-column extraction's
known residual defect, fixed BNSS's stray "337 mislabeled as duplicate
338" artifact outright (the new source has no such duplicate — its
531 sections match the official count with no gaps or collisions).

Two small chunker regexes were widened to match this format's real
layout variations, found by direct inspection rather than guessed:
`clean.py`'s `_SOFT_LINEBREAK` now tolerates a few spaces of leading
indentation before a section-opening line (some pages indent a
section's first line), and `chunk.py`'s `_SANHITA_HEADER` now tolerates
an em-dash appearing immediately after the section number with no
space (a real, if less common, formatting variant in this source).
Both changes were verified to produce byte-identical chunk counts for
the four already-ingested sources that share this chunker
(`it_act`/`pwdva`/`lsa`/`constitution`) before and after.

### Curated section-split repairs (ICCSDI 2026 revision)

The four sections the paragraph above's earlier version recorded as a
"known residual limitation" -- BNS 217 and 255 (header titles wrapped
across a line break, no full stop before the em-dash), JJ Act 61 and 86
(the 2021 amendment substituted both, so the source opens them with a
footnote bracket, e.g. `"1[86 Classification of offences..."`, s.86's
even lacking the dot after its number) -- plus RTI s.14 (OCR omits the
full stop before the em-dash; its text previously sat inside the
excluded s.13's chunk and was therefore dropped from the corpus
entirely) are now **fixed by curated, per-source split repairs**
(`SourceMeta.section_splits`, applied by
`app/ingestion/chunk.py::apply_section_splits`).

Each repair names the host chunk, the new unit, the section's full
literal header text as a pattern, and the title, and every failure mode
raises at ingestion rather than degrading: a missing host, an
already-produced unit, or a pattern that doesn't match exactly once
means the source changed and the repair is stale. The only text removed
from a body is the header itself (number + title) -- exactly what
`chunk_sanhita` strips for every regularly-parsed section -- so body
text stays verbatim. This is deliberately NOT a relaxation of the
general `_SANHITA_HEADER` pattern: two narrower regex relaxations were
tried in an earlier session and reverted after they introduced
false-positive header matches elsewhere in the corpus, and a curated,
asserted, per-defect repair (the same idiom as `title_overrides` and
`exclude_units`) cannot regress any other source. Regression tests:
`tests/test_section_splits.py`.

### Two-column gazette PDFs (historical; Constitution only, going forward)

The official India Code PDFs originally supplied for BNS, BNSS, BSA,
the Consumer Protection Act 2019, and the Juvenile Justice Act 2015 (and
still the PDF used for the Constitution, which has not been replaced)
share a two-column typesetting layout: a narrow marginal-note column
(the section's official title) beside the body column, plus a
printer's line-count ruler in the body column's right margin, mirrored
left/right by page the way a bound gazette's running heads typically
are. `pypdf`'s reading-order text extraction interleaves the note
column into the body text out of order, and BNS/BSA specifically also
routed their page content through a PDF Form XObject that broke
`pypdf`'s position-aware "layout" mode extraction entirely (returned
empty text); BNS/BSA additionally had no real space character in their
embedded font (word spacing was a small positioning gap, not a space
glyph), which separately broke naive word segmentation.

`app/ingestion/extract.py`'s `extract_gazette_body_text()` resolves
all of this using `pdfplumber`'s real per-character page coordinates
(not `pypdf`, which can't see this layout's Form-XObject-wrapped
content at all): it locates the note-column/body-column gap and the
body-column/ruler gap independently per page (both can shift slightly
page to page), keeps only body-column words with a tightened
`x_tolerance` (fixes the missing-space-glyph issue), reassembles rows
by real vertical position rather than a fixed grid (avoids scrambling
word order), and drops repeating page-header/footer boilerplate by
content. The result feeds the existing `chunk_constitution`
numeric-boundary chunker (start marker `"BE it enacted"`) -- still
exactly how the Constitution is ingested today. This code path is kept
for the Constitution and as a fallback for any future two-column
source; it's no longer in use for BNS/BNSS/BSA/CPA2019/JJ Act now that
cleaner single-column source PDFs exist for them (see above).

- **Section titles are best-effort recovered, not guaranteed, on this
  path.** `extract_gazette_titles()` is a second, entirely independent
  pass (it never touches `lines_out`/body text, so a bad title
  association can at worst produce a wrong or missing title, never
  corrupt a chunk's verbatim body) that re-detects the same column
  gaps, row-clusters the *note* column the same way it row-clusters
  the body column, and attributes each note to whichever section
  boundary was most recently seen. On the Constitution (the only
  source still using this path) titles are not attempted generally for
  this reason; a small hand-verified table covers Part III instead
  (see `docs/PROJECT_STATE.md`).
- Recorded in each affected source's `coverage_note` and surfaced live
  via `/corpus/sources`, not just in this doc.

### Right to Information Act, 2005 — known limitations of the ingested copy

The RTI Act is ingested from the Central Information Commission's own
published copy, which is the file in the corpus folder. **27 sections are
in the corpus; four are deliberately excluded** (s.14, previously lost
inside the excluded s.13's chunk, is recovered by a curated split
repair -- see "Curated section-split repairs" above).
Three things about the source are worth recording, because each is a
deliberate decision rather than an oversight.

**It predates the 2019 amendment.** The RTI (Amendment) Act, 2019 (Act
24 of 2019) replaced ss.13, 16 and 27, which govern the term of office
and conditions of service of Information Commissioners and the
rule-making power. This copy still carries the superseded five-year
fixed term and Election-Commissioner salary parity. Serving that as
current law would misstate the institutional position, so those three
sections are excluded at ingestion (`exclude_units` in
`app/ingestion/sources.py`) and the reason is recorded in the source
manifest. The 2019 Act amended only those three; every citizen-facing
provision ingested here — ss.6, 7, 8, 9, 10, 11, 18, 19, 20 — is
unamended.

**s.25 is excluded for retrieval reasons, not currency.** "Monitoring
and reporting" governs the annual report each Commission sends the
appropriate Government. No citizen asks it, but its text ("prepare a
report", "forward a copy", "collect and provide such information") sits
very close in embedding space to "file an FIR" — First *Information
Report*. Ingested, it took the top hybrid hit away from bnss:173/177 on
"how do I file an FIR" and three sibling queries, and alone accounted
for 5 of the 11 RTI intrusions into the dense top-5 of non-RTI citizen
queries. The trade-off is stated rather than hidden: a question about a
Commission's annual reporting duty is now unanswerable.

**Its OCR is imperfect, and only the safe repairs were made.** The
published PDF renders 48 bracketed markers as "(/)". These are *not*
all the same character: most are sub-section "(1)", but in s.2 the same
glyph stands for the definitions clause "(l)" (lower-case L, as in
'(l) "State Chief Information Commissioner"'), and one reads "(/0)"
for "(10)". Rewriting them all to "(1)" would relabel definition
clauses as sub-sections, so the markers are left exactly as extracted;
only the bracketed label is affected and every provision's operative
text is intact. Two *titles* were restored, because titles are part of
the indexed text and garbled ones cost retrieval on the most obvious
queries in the Act: s.3 extracted as "Ftight to information" and s.18
as "Powers and 'Unctions of Information Commissions".

## Safety redirect sources

| Situation | Official route |
| --- | --- |
| Immediate threat, active crime, fire, medical or other emergency | [Emergency Response Support System — 112](https://112.gov.in/) |
| Cybercrime | [National Cyber Crime Reporting Portal](https://www.cybercrime.gov.in/) |
| Financial cyber fraud | [Ministry of Home Affairs information on 1930](https://www.pib.gov.in/PressReleasePage.aspx?PRID=1814120) |
| Women’s support | [Women Helpline — 181](https://www.spniwcd.wcd.gov.in/help/faqs) |

Contact routes are configuration data, not model-generated text. They must be re-verified before each public deployment.
