"""Orchestrates one source through: load -> clean -> chunk -> version -> persist.

Usage (also exposed via scripts/ingest_corpus.py):

    from app.ingestion.pipeline import ingest_source, ingest_all
    manifest = ingest_source("bnss")

Drop a new/updated raw.txt (or source PDF, once extract.py's PDF path
is wired up) into data/legal-corpus/<source_id>/ and re-run ingestion --
nothing else needs to change. That's the "upload folder" the RAG
pipeline feeds from.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone

from .chunk import CHUNKERS, apply_section_splits
from .clean import clean_extracted_text
from .extract import extract_gazette_body_text, extract_gazette_titles, extract_pdf_text
from .models import Chunk
from .sources import APPROVED_SOURCES, get_source


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _source_dir(source_id: str) -> str:
    return os.path.dirname(get_source(source_id).raw_path)


def _pdf_path(source_id: str) -> str:
    return os.path.join(_source_dir(source_id), "raw.pdf")


def _ensure_raw_text(source_id: str, raw_path: str) -> None:
    """If raw.txt is missing but raw.pdf is present, extract it once.

    This is the "drop a PDF, don't touch retrieval code" path: a
    reviewer places an approved raw.pdf in the source's corpus folder,
    and ingestion materializes raw.txt from it deterministically. The
    extracted raw.txt is written to disk (not held in memory only) so
    it stays inspectable/diffable exactly like a hand-supplied raw.txt,
    and so re-ingestion doesn't re-run PDF extraction unless raw.txt is
    deleted or the PDF is newer.
    """
    if os.path.exists(raw_path):
        return
    pdf_path = _pdf_path(source_id)
    if not os.path.exists(pdf_path):
        return
    source = get_source(source_id)
    if source.extraction_mode == "gazette_body":
        text = extract_gazette_body_text(pdf_path)
    else:
        text = extract_pdf_text(pdf_path)
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(text)


def ingest_source(source_id: str) -> dict:
    source = get_source(source_id)
    _ensure_raw_text(source_id, source.raw_path)
    if not os.path.exists(source.raw_path):
        raise FileNotFoundError(
            f"No raw text for '{source_id}' at {source.raw_path}, and no "
            f"raw.pdf found alongside it to extract from. Drop an approved "
            f"raw.txt or raw.pdf into that folder and re-run ingestion."
        )

    with open(source.raw_path, encoding="utf-8") as f:
        raw = f.read()

    cleaned = clean_extracted_text(raw)
    chunker = CHUNKERS[source.chunk_style]
    kwargs = {}
    if source.chunk_start_marker:
        kwargs["start_marker"] = source.chunk_start_marker
    if source.chunk_end_marker:
        kwargs["end_marker"] = source.chunk_end_marker
    chunks = chunker(source_id, cleaned, **kwargs)

    # Split out sections whose headers the general pattern provably
    # cannot match in this source (wrapped titles, amendment brackets,
    # OCR-damaged punctuation). Runs before exclusions so a section
    # merged into a later-excluded host (RTI s.14 inside s.13) is
    # recovered rather than dropped with it.
    if source.section_splits:
        chunks = apply_section_splits(source_id, chunks, source.section_splits)

    # Restore titles the source PDF mis-rendered. Asserted, not assumed:
    # an override for a unit the chunker never produced, or one whose
    # title already matches, means the source changed and the override is
    # stale -- silently keeping a wrong title is what this prevents.
    if source.title_overrides:
        by_unit = {c.unit_number: c for c in chunks}
        for unit, correct in source.title_overrides:
            chunk = by_unit.get(unit)
            if chunk is None:
                raise ValueError(
                    f"'{source_id}' has a title override for unit {unit!r}, "
                    f"which the chunker did not produce."
                )
            if chunk.title == correct:
                raise ValueError(
                    f"'{source_id}' unit {unit!r} already extracts the correct "
                    f"title {correct!r}; drop the stale override."
                )
            chunk.title = correct

    # Drop superseded provisions before anything downstream can see them.
    # Done here rather than in the chunker so it stays source-agnostic,
    # and asserted rather than assumed: a unit listed for exclusion that
    # the chunker never produced means the section numbering shifted
    # under us, and silently excluding nothing would be the worst
    # outcome -- the stale text would stay in the corpus.
    if source.exclude_units:
        present = {c.unit_number for c in chunks}
        missing = [u for u in source.exclude_units if u not in present]
        if missing:
            raise ValueError(
                f"'{source_id}' lists units {missing} for exclusion but the "
                f"chunker did not produce them. Refusing to ingest: the "
                f"source layout has changed and the exclusion is no longer "
                f"doing what it claims."
            )
        chunks = [c for c in chunks if c.unit_number not in source.exclude_units]

    # A chunk_id must identify exactly one provision -- citations are
    # built from it. Schedules that reuse the section-header layout can
    # silently produce a second chunk with an existing number.
    ids = [c.chunk_id for c in chunks]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(
            f"'{source_id}' produced duplicate chunk_ids {duplicates}. Two "
            f"different texts would share one citation. Set chunk_end_marker "
            f"to stop before the schedules, or fix the chunker."
        )

    if not chunks:
        raise ValueError(
            f"Chunker produced zero chunks for '{source_id}'. The source text "
            f"likely doesn't match the expected layout -- inspect raw.txt before "
            f"trusting this source for citations."
        )

    if source.extraction_mode == "gazette_body":
        pdf_path = _pdf_path(source_id)
        if os.path.exists(pdf_path):
            # Best-effort title recovery, entirely independent of the
            # chunks/body text already built above -- see
            # extract_gazette_titles's docstring. A section absent from
            # the returned dict just keeps its existing empty title;
            # nothing here is ever inferred or guessed.
            titles = extract_gazette_titles(pdf_path)
            for c in chunks:
                if not c.title and c.unit_number in titles:
                    c.title = titles[c.unit_number]

    out_dir = _source_dir(source_id)
    os.makedirs(out_dir, exist_ok=True)

    chunks_path = os.path.join(out_dir, "chunks.jsonl")
    with open(chunks_path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")

    manifest = {
        "source_id": source.source_id,
        "display_name": source.display_name,
        "act_no": source.act_no,
        "official_url": source.official_url,
        "publisher": source.publisher,
        "as_on_date": source.as_on_date,
        "coverage_note": source.coverage_note,
        "excluded_units": list(source.exclude_units),
        "exclude_reason": source.exclude_reason,
        "unit_label": source.unit_label,
        "checksum": _checksum(cleaned),
        "chunk_count": len(chunks),
        "imported_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path = os.path.join(out_dir, "source.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return manifest


def ingest_all() -> list[dict]:
    return [ingest_source(sid) for sid in APPROVED_SOURCES]


def load_chunks(source_id: str) -> list[Chunk]:
    path = os.path.join(_source_dir(source_id), "chunks.jsonl")
    chunks = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(Chunk(**json.loads(line)))
    return chunks


def load_all_chunks() -> list[Chunk]:
    out: list[Chunk] = []
    for sid in APPROVED_SOURCES:
        manifest_path = os.path.join(_source_dir(sid), "source.json")
        if os.path.exists(manifest_path):
            out.extend(load_chunks(sid))
    return out
