"""Approved-source registry.

Only sources listed here may enter the RAG corpus. This mirrors
docs/LEGAL_SOURCES.md exactly on purpose -- if you add a source here,
add it there too (and vice versa). This is the "official-source
allow-list" the project spec requires before any admin-added document
can be indexed.
"""
from __future__ import annotations

import os

from .models import SourceMeta

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "legal-corpus")


def _raw(source_id: str) -> str:
    return os.path.join(_DATA_DIR, source_id, "raw.txt")


APPROVED_SOURCES: dict[str, SourceMeta] = {
    "constitution": SourceMeta(
        source_id="constitution",
        display_name="Constitution of India",
        act_no="",
        official_url="https://www.indiacode.nic.in/bitstream/123456789/16124/1/the_constitution_of_india.pdf",
        publisher="India Code / Ministry of Law and Justice",
        as_on_date="user-supplied PDF, official India Code text",
        raw_path=_raw("constitution"),
        unit_label="Article",
        chunk_style="constitution",
        coverage_note="Full text as supplied. Article titles (marginal notes) are not reliably "
                       "extracted for every article due to the source PDF's two-column layout; "
                       "article numbers and body text are exact.",
    ),
    "bns": SourceMeta(
        source_id="bns",
        display_name="Bharatiya Nyaya Sanhita, 2023",
        act_no="ACT NO. 45 OF 2023",
        official_url="https://www.indiacode.nic.in/bitstream/123456789/20062/1/a202345.pdf",
        publisher="India Code / Ministry of Law and Justice",
        as_on_date="user-supplied PDF, official India Code text",
        raw_path=_raw("bns"),
        unit_label="Section",
        chunk_style="sanhita",
        chunk_start_marker="BE it enacted",
        # Two headers the general pattern cannot match in this PDF: both
        # titles wrap across a line break (joined by cleaning into one
        # long title with no full stop before the em-dash). Located by
        # their full literal header text and split out, restoring each
        # section's own chunk and citation.
        section_splits=(
            (
                "216",
                "217",
                r"\n217\. False information, with intent to cause public "
                r"servant to use his lawful power to injury of another "
                r"person—",
                "False information, with intent to cause public servant to "
                "use his lawful power to injury of another person",
            ),
            (
                "254",
                "255",
                r"\s255\.—Public servant disobeying direction of law "
                r"with intent to save person from punishment or property "
                r"from forfeiture \.—",
                "Public servant disobeying direction of law with intent to "
                "save person from punishment or property from forfeiture",
            ),
        ),
        coverage_note="Full text as supplied from a single-column 'bare Act' India Code PDF "
                       "(the source is cleanly extractable, no two-column layout). Section "
                       "titles are inline in the source text and recovered for all 358 "
                       "sections. Two sections (217, 255) whose header titles wrap across a "
                       "line break in the source PDF -- which the general section-header "
                       "pattern cannot match -- are split out of the preceding section's "
                       "chunk by a curated, asserted repair (see section_splits), so each "
                       "carries its own citation (see docs/LEGAL_SOURCES.md).",
    ),
    "bnss": SourceMeta(
        source_id="bnss",
        display_name="Bharatiya Nagarik Suraksha Sanhita, 2023",
        act_no="ACT NO. 46 OF 2023",
        official_url="https://www.indiacode.nic.in/bitstream/123456789/20099/1/A202346.pdf",
        publisher="India Code / Ministry of Law and Justice",
        as_on_date="user-supplied PDF, official India Code text",
        raw_path=_raw("bnss"),
        unit_label="Section",
        chunk_style="sanhita",
        chunk_start_marker="BE it enacted",
        coverage_note="Full text as supplied from a single-column 'bare Act' India Code PDF "
                       "(replaced this session), including Chapter XIII investigation/FIR "
                       "(ss.173-196) and Chapter XXXV bail and bonds (ss.478-496). Section "
                       "titles are inline in the source text and recovered for all 531 sections "
                       "(100%) -- the old two-column source's ~51% title coverage and known "
                       "337/338 duplicate-numbering fault are both resolved by this replacement "
                       "(see docs/LEGAL_SOURCES.md).",
    ),
    "bsa": SourceMeta(
        source_id="bsa",
        display_name="Bharatiya Sakshya Adhiniyam, 2023",
        act_no="ACT NO. 47 OF 2023",
        official_url="https://www.indiacode.nic.in/bitstream/123456789/20063/1/aa202347.pdf",
        publisher="India Code / Ministry of Law and Justice",
        as_on_date="user-supplied PDF, official India Code text",
        raw_path=_raw("bsa"),
        unit_label="Section",
        chunk_style="sanhita",
        chunk_start_marker="BE it enacted",
        coverage_note="Full text as supplied from a single-column 'bare Act' India Code PDF "
                       "(replaced this session). Section titles are inline in the source text "
                       "and recovered for all 170 sections (100%) -- the old two-column source's "
                       "~52% title coverage is resolved by this replacement (see "
                       "docs/LEGAL_SOURCES.md).",
    ),
    "it_act": SourceMeta(
        source_id="it_act",
        display_name="Information Technology Act, 2000",
        act_no="ACT NO. 21 OF 2000",
        official_url="https://www.indiacode.nic.in/handle/123456789/1999",
        publisher="India Code / Ministry of Law and Justice",
        as_on_date="user-supplied PDF, official India Code text",
        raw_path=_raw("it_act"),
        unit_label="Section",
        chunk_style="sanhita",
        coverage_note="Full text as supplied (single-column official layout; cleanly "
                       "extractable). Covers digital signatures/electronic signatures, "
                       "electronic governance, certifying authorities, cyber offences "
                       "(hacking, identity theft, cyber terrorism) and penalties.",
    ),
    "pwdva": SourceMeta(
        source_id="pwdva",
        display_name="Protection of Women from Domestic Violence Act, 2005",
        act_no="ACT NO. 43 OF 2005",
        official_url="https://www.indiacode.nic.in/handle/123456789/2021",
        publisher="India Code / Ministry of Law and Justice",
        as_on_date="user-supplied PDF, official India Code text",
        raw_path=_raw("pwdva"),
        unit_label="Section",
        chunk_style="sanhita",
        coverage_note="Full text as supplied (single-column official layout; cleanly "
                       "extractable). Covers the definition of domestic violence, "
                       "Protection Officer/service provider duties, and protection, "
                       "residence, monetary relief and custody orders.",
    ),
    "lsa": SourceMeta(
        source_id="lsa",
        display_name="Legal Services Authorities Act, 1987",
        act_no="ACT NO. 39 OF 1987",
        official_url="https://www.indiacode.nic.in/handle/123456789/1925",
        publisher="India Code / Ministry of Law and Justice",
        as_on_date="user-supplied PDF, official India Code text",
        raw_path=_raw("lsa"),
        unit_label="Section",
        chunk_style="sanhita",
        coverage_note="Full text as supplied (single-column official layout; cleanly "
                       "extractable). Covers NALSA/State/District Legal Services "
                       "Authorities, free legal aid entitlement and Lok Adalats.",
    ),
    "cpa2019": SourceMeta(
        source_id="cpa2019",
        display_name="Consumer Protection Act, 2019",
        act_no="ACT NO. 35 OF 2019",
        official_url="https://www.indiacode.nic.in/handle/123456789/18964",
        publisher="India Code / Ministry of Law and Justice",
        as_on_date="user-supplied PDF, official India Code text",
        raw_path=_raw("cpa2019"),
        unit_label="Section",
        chunk_style="sanhita",
        chunk_start_marker="BE it enacted",
        coverage_note="Full text as supplied from a single-column 'bare Act' India Code PDF "
                       "(replaced this session). Section titles are inline in the source text "
                       "and recovered for all 107 sections (100%) -- the old two-column source's "
                       "~49% title coverage is resolved by this replacement (see "
                       "docs/LEGAL_SOURCES.md). Covers Central/State consumer protection "
                       "authorities and councils, consumer complaints and District/State/"
                       "National Commissions, mediation, and product liability.",
    ),
    "jj2015": SourceMeta(
        source_id="jj2015",
        display_name="Juvenile Justice (Care and Protection of Children) Act, 2015",
        act_no="ACT NO. 2 OF 2016",
        official_url="https://www.indiacode.nic.in/handle/123456789/2148",
        publisher="India Code / Ministry of Law and Justice",
        as_on_date="user-supplied PDF, official India Code text",
        raw_path=_raw("jj2015"),
        unit_label="Section",
        chunk_style="sanhita",
        chunk_start_marker="BE it enacted",
        # Two headers the general pattern cannot match in this PDF: the
        # 2021 amendment substituted both sections, so the source marks
        # their opening with a footnote bracket ("61. 2[Procedure...]",
        # "1[86 Classification..." -- s.86's even lacks the dot after
        # the number). Located by their full literal header text and
        # split out, restoring each section's own chunk and citation.
        section_splits=(
            (
                "60",
                "61",
                r"\n61\. 2\[Procedure for disposal of adoption "
                r"proceedings\] \.—",
                "Procedure for disposal of adoption proceedings",
            ),
            (
                "85",
                "86",
                r"\s1\[86 Classification of offences and designated "
                r"court \.—\s*",
                "Classification of offences and designated court",
            ),
        ),
        coverage_note="Full text as supplied from a single-column 'bare Act' India Code PDF. "
                       "Section titles are inline in the source text and recovered for all 112 "
                       "sections -- the old two-column source's ~40% title coverage is resolved "
                       "by this replacement. Two sections (61, 86) that the 2021 amendment "
                       "substituted -- so the source PDF marks their opening number with an "
                       "amendment-substitution footnote bracket (e.g. \"1[86 Classification...\") "
                       "the general section-header pattern cannot match -- are split out of the "
                       "preceding section's chunk by a curated, asserted repair (see "
                       "section_splits), so each carries its own citation (see "
                       "docs/LEGAL_SOURCES.md). Covers children in conflict with law (Juvenile "
                       "Justice Boards), children in need of care and protection (Child Welfare "
                       "Committees), and offences against children.",
    ),
    "rti": SourceMeta(
        source_id="rti",
        display_name="Right to Information Act, 2005",
        act_no="ACT NO. 22 OF 2005",
        official_url="https://cic.gov.in/sites/default/files/RTI-Act_English.pdf",
        publisher="Central Information Commission",
        as_on_date="pre-2019 text as published by the CIC; see exclude_reason",
        raw_path=_raw("rti"),
        unit_label="Section",
        chunk_style="sanhita",
        chunk_start_marker="BE it enacted",
        # The Second Schedule lists intelligence organisations as a
        # numbered list ("9.Border Security Force.", "22.Financial
        # Intelligence Unit, India.") that the sanhita header pattern
        # reads as sections, colliding with the real ss.9 and 22.
        chunk_end_marker="THE FIRST SCHEDULE",
        # Two titles the CIC PDF's OCR damaged. Both are restored to the
        # Act's own headings, verbatim -- s.3 extracts as "Ftight to
        # information" and s.18 as "Powers and 'Unctions of Information
        # Commissions". These are the exact words a citizen searches for
        # ("right to information", "powers and functions"), and titles are
        # indexed, so leaving them garbled costs retrieval on the two most
        # obvious queries in the whole Act.
        title_overrides=(
            ("3", "Right to information"),
            ("18", "Powers and functions of Information Commissions"),
        ),
        # The CIC PDF's OCR omits the full stop before s.14's em-dash
        # ("...or Information Commissioner—CO Subject to..."), so the
        # general header pattern cannot match it and s.14's text lands
        # inside s.13's chunk -- which is excluded below, silently
        # dropping s.14 with it. Split out here (splits run before
        # exclusions), restoring the unamended removal provision. Its
        # first sub-section marker OCRs as "CO" (for "(1)") and is left
        # exactly as extracted, per this source's documented policy of
        # never rewriting ambiguous OCR marks.
        section_splits=(
            (
                "13",
                "14",
                r"\n14\. Removal of Chief Information Commissioner or "
                r"Information Commissioner—",
                "Removal of Chief Information Commissioner or Information "
                "Commissioner",
            ),
        ),
        exclude_units=("13", "16", "25", "27"),
        exclude_reason=(
            "s.25 (Monitoring and reporting) is excluded for a different "
            "reason from the other three: measured retrieval harm. It "
            "governs the annual report each Commission sends the "
            "appropriate Government -- no citizen asks it -- but its text "
            "is dense with 'prepare a report', 'forward a copy' and "
            "'collect and provide such information', which the dense "
            "encoder places very close to 'file an FIR' (First Information "
            "Report). Ingested, it took the top hybrid hit away from "
            "bnss:173/177 on 'how do I file an FIR', 'how to fil fir' and "
            "'NCR filing procedure' (q23, h066, h076, h083), and it alone "
            "accounted for 5 of the 11 RTI intrusions into the dense top-5 "
            "of non-RTI citizen queries, and 4 of the 6 top-1 steals. "
            "Dropping one institutional section is a far smaller loss than "
            "misdirecting the single most common citizen legal question. "
            "The trade-off is real and stated: a question about a "
            "Commission's annual reporting duty is now unanswerable. "
            "The Right to Information (Amendment) Act, 2019 (Act 24 of 2019) "
            "replaced ss.13, 16 and 27. This ingested copy predates it and "
            "still carries the superseded five-year fixed term and "
            "Election-Commissioner salary parity for Information "
            "Commissioners, which the 2019 Act moved to rules prescribed by "
            "the Central Government. Serving that text as current law would "
            "misstate the institutional position, so those three sections "
            "are excluded rather than ingested. The 2019 Act amended only "
            "ss.13, 16 and 27 -- the citizen-facing provisions ingested here "
            "(ss.6, 7, 8, 9, 10, 11, 18, 19, 20) are unamended."
        ),
        coverage_note=(
            "Chapters I-VI as published by the Central Information "
            "Commission, excluding the Schedules and the three sections the "
            "2019 amendment replaced (see exclude_reason). Covers the right "
            "of access and how to request information (ss.3, 6), the "
            "thirty-day disposal limit and the forty-eight-hour limit where "
            "life or liberty is concerned (s.7), the exemptions and "
            "severability rules (ss.8-10), third-party information (s.11), "
            "the Information Commissions' powers (s.18), first and second "
            "appeals (s.19) and penalties for a Public Information Officer "
            "(s.20), and the removal provision (s.14, unamended by the 2019 "
            "Act, recovered by a curated header repair -- see "
            "section_splits; its '(1)' marker OCRs as 'CO' and is left as "
            "extracted). One OCR defect is left deliberately unrepaired: the published PDF "
            "renders 48 bracketed markers as '(/)'. These are NOT all the "
            "same character. Most are sub-section '(1)', but in s.2 the same "
            "glyph stands for the definition clause '(l)' (lower-case L, as "
            "in '(l) \"State Chief Information Commissioner\"'), and one "
            "reads '(/0)' for '(10)'. Rewriting them all to '(1)' would "
            "relabel definition clauses as sub-sections, so the markers are "
            "left exactly as extracted. Only the bracketed label is "
            "affected; every provision's operative text is intact."
        ),
    ),
}


def get_source(source_id: str) -> SourceMeta:
    try:
        return APPROVED_SOURCES[source_id]
    except KeyError as exc:
        raise ValueError(
            f"'{source_id}' is not on the approved-source allow-list "
            f"(see docs/LEGAL_SOURCES.md). Approved: {list(APPROVED_SOURCES)}"
        ) from exc
