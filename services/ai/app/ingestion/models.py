"""Typed structures shared across the ingestion pipeline.

Every chunk produced by this pipeline carries enough metadata to satisfy
CAP's citation rule: exact source, exact section/article, official URL,
and a verification ("as on") date. Nothing here ever paraphrases the
underlying legal text -- ingestion only cleans and cuts, never rewrites.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class SourceMeta:
    """One approved legal source, mirroring docs/LEGAL_SOURCES.md."""

    source_id: str        # short slug, e.g. "bnss"
    display_name: str     # "Bharatiya Nagarik Suraksha Sanhita, 2023"
    act_no: str           # "ACT NO. 46 OF 2023"
    official_url: str     # India Code bitstream/handle URL
    publisher: str        # "India Code / Ministry of Law and Justice"
    as_on_date: str       # verification date printed on the source PDF
    raw_path: str         # path to the raw text file under data/legal-corpus/<id>/
    unit_label: str = "Section"  # "Section" for the Sanhitas/Adhiniyam, "Article" for the Constitution
    chunk_style: str = "sanhita"  # "sanhita" | "constitution"
    extraction_mode: str = "plain"  # "plain" | "gazette_body" -- see extract.py's extract_gazette_body_text
    chunk_start_marker: str = ""  # override chunk_constitution's default "PART I" start marker, e.g. "BE it enacted"
    # Stop chunking at this literal, when a source's schedules reuse the
    # section-header layout. The RTI Act's Second Schedule lists numbered
    # security organisations ("9.Border Security Force.", "22.Financial
    # Intelligence Unit") that the sanhita header pattern reads as
    # sections, producing chunks that collide with the real ss.9 and 22.
    # Empty (the default) keeps the previous behaviour of chunking to the
    # end of the document, so no existing source is affected.
    chunk_end_marker: str = ""
    # Section/article numbers to drop after chunking. For provisions that
    # a later amendment replaced, where the ingested copy still carries
    # the superseded text -- publishing those as current law would be
    # worse than not covering them at all. Recorded in the manifest so
    # the omission is visible rather than silent.
    exclude_units: tuple[str, ...] = ()
    exclude_reason: str = ""  # why exclude_units were dropped, for the manifest
    # Corrections for section titles the source PDF mis-renders, as
    # ((unit_number, correct_title), ...). Titles are concatenated into
    # the indexed text (see index_build._index_text), so a garbled title
    # costs retrieval on exactly the words a citizen would search for.
    # Only ever used to restore a title the source itself states and OCR
    # damaged -- never to invent or paraphrase one, and never applied to
    # body text, which stays exactly as extracted.
    title_overrides: tuple[tuple[str, str], ...] = ()
    coverage_note: str = ""  # honest note on what part of the source is ingested, if partial
    import_date: str = field(default_factory=lambda: date.today().isoformat())


@dataclass
class Chunk:
    """One retrievable unit of legal text -- one Section or Article."""

    chunk_id: str    # "{source_id}:{unit_number}"
    source_id: str
    unit_number: str  # "43" or "43(5)" for a specific subsection
    title: str        # section/article title if the source provides one, else ""
    text: str         # the verbatim statutory text, cleaned of layout artifacts only
    part_or_chapter: str = ""  # e.g. "Chapter V — Arrest of Persons"

    def citation(self, source: SourceMeta) -> dict:
        return {
            "source": source.display_name,
            "act_no": source.act_no,
            "unit": f"{source.unit_label} {self.unit_number}",
            "official_url": source.official_url,
            "verified_as_on": source.as_on_date,
        }
