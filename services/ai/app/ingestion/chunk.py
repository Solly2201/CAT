"""Split cleaned statutory text into one chunk per Section/Article.

Two drafting styles are handled, both verified against the actual
India Code text for BNS/BNSS/BSA/Constitution (see
services/ai/tests/test_ingestion.py):

- "sanhita": "43. Arrest how made.—(1) In making an arrest..." -- the
  BNS/BNSS/BSA style. Title is inline, separated from the body by an
  em/en-dash or double hyphen.
- "constitution": "14. Equality before law.\n(1)..." or just
  "14. (1) India, that is Bharat..." -- articles are not reliably
  followed by an inline title in this source's extracted layout, so we
  chunk on the article number alone and leave title empty rather than
  guess.

Both chunkers only look at line-start section/article numbers, so a
number mentioned mid-sentence ("under section 43") never triggers a
false boundary.
"""
from __future__ import annotations

import re

from .models import Chunk

_SANHITA_HEADER = re.compile(
    r"(?m)^\s*(\d{1,3}[A-Z]?)\.\s*[—–-]{0,2}\s*([A-Z][^\n]*?)\.\s*[—–-]{1,2}\s*"
)
_CONSTITUTION_HEADER = re.compile(
    r"(?m)^\s*(\d{1,3}[A-Z]?)\.\s+(?=[\(A-Z])"
)
# Consolidated "as amended" India Code PDFs print each amendment's
# history as a numbered footnote ("1. Subs. by Act 10 of 2009, s. 2,
# for ...", reusing small numbers that collide with real section
# numbers). A footnote's own text always opens with one of these
# standard amendment-drafting verbs, which a real section title never
# does, so it is a safe, content-based way to reject that false match
# rather than parse it as a bogus duplicate-numbered section.
_FOOTNOTE_TITLE = re.compile(
    r"^(Subs\.|Ins\.|Om\.|Reps\.|Renumbered\b|Added\b|Substituted\b|Inserted\b|Omitted\b)"
)


def chunk_sanhita(
    source_id: str,
    text: str,
    start_marker: str = "BE it enacted",
    end_marker: str = "",
) -> list[Chunk]:
    idx = text.find(start_marker)
    body = text[idx:] if idx != -1 else text
    if end_marker:
        end = body.find(end_marker)
        if end != -1:
            body = body[:end]
    matches = list(_SANHITA_HEADER.finditer(body))
    chunks: list[Chunk] = []
    for i, m in enumerate(matches):
        unit_number = m.group(1)
        title = m.group(2).strip()
        content_start = m.end()
        content_end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        content = body[content_start:content_end].strip()
        if not content or _FOOTNOTE_TITLE.match(title):
            continue
        chunks.append(
            Chunk(
                chunk_id=f"{source_id}:{unit_number}",
                source_id=source_id,
                unit_number=unit_number,
                title=title,
                text=content,
            )
        )
    return chunks


# The Constitution PDF's marginal-note article titles ("Equality before
# law.", "Protection against arrest and detention in certain cases.")
# are real text in raw.txt, but a genuinely two-column layout: the
# extractor emits each page's main-column body first, then that page's
# batch of marginal notes, then its footnotes, then a bare page-number
# line, before the next page's body resumes -- often splitting a single
# sentence across the reordered block. Unlike BSA's two-column fix
# (docs/LEGAL_SOURCES.md), title-to-article association here can't be
# recovered by a general positional rule: marginal-note batches and
# footnote continuations interleave in page-dependent order (confirmed
# by direct inspection of raw.txt), so a general parser risks silently
# mis-assigning one article's title to another -- unacceptable for a
# system whose whole premise is never showing incorrect legal metadata.
#
# eval/queries.jsonl's failure analysis (docs/RETRIEVAL_EVALUATION.md)
# showed this missing-title gap was the single largest failure cluster:
# every constitution article that also has a BM25-strong lexical
# distractor (14 vs 15 vs 16, or 19 vs the Art 105/194 "freedom of
# speech in Parliament" distractors) needs its own title indexed to be
# found reliably by paraphrased queries, the same reason BSA/BNS/BNSS
# titles are indexed at all (see index_build.py's _index_text). Rather
# than risk a general parser, the titles below were read directly out
# of raw.txt at each article's own trailer block and hand-verified
# against that article's body content -- Part III (Fundamental Rights),
# the only part any eval query needs a title from. This is the same
# narrow, evaluation-justified-only pattern as query_expand.py's
# abbreviation dict: extend it only if a future evaluation query names
# another specific missing title, not proactively for the rest of the
# document.
_KNOWN_ARTICLE_TITLES: dict[str, str] = {
    "12": "Definition.",
    "13": "Laws inconsistent with or in derogation of the fundamental rights.",
    "14": "Equality before law.",
    "15": "Prohibition of discrimination on grounds of religion, race, caste, sex or place of birth.",
    "16": "Equality of opportunity in matters of public employment.",
    "17": "Abolition of Untouchability.",
    "18": "Abolition of titles.",
    "19": "Protection of certain rights regarding freedom of speech, etc.",
    "20": "Protection in respect of conviction for offences.",
    "21": "Protection of life and personal liberty.",
    "22": "Protection against arrest and detention in certain cases.",
}


def chunk_constitution(
    source_id: str,
    text: str,
    start_marker: str = "PART I",
    end_marker: str = "",
) -> list[Chunk]:
    idx = text.find(start_marker)
    body = text[idx:] if idx != -1 else text
    if end_marker:
        end = body.find(end_marker)
        if end != -1:
            body = body[:end]
    matches = list(_CONSTITUTION_HEADER.finditer(body))
    chunks: list[Chunk] = []
    for i, m in enumerate(matches):
        unit_number = m.group(1)
        content_start = m.start()  # keep the article number in the body text for context
        content_end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        content = body[content_start:content_end].strip()
        if not content or len(content) < 5:
            continue
        chunks.append(
            Chunk(
                chunk_id=f"{source_id}:{unit_number}",
                source_id=source_id,
                unit_number=unit_number,
                # chunk_constitution is reused for every two-column gazette
                # source (BNS/BNSS/BSA/CPA2019/JJ Act), each of which
                # recovers its own titles separately via
                # extract_gazette_titles (pipeline.py) -- the hand-verified
                # table above is Constitution-article-number-specific and
                # must never leak into an unrelated Act's same-numbered
                # section.
                title=_KNOWN_ARTICLE_TITLES.get(unit_number, "") if source_id == "constitution" else "",
                text=content,
            )
        )
    return chunks


def apply_section_splits(
    source_id: str,
    chunks: list[Chunk],
    splits: tuple[tuple[str, str, str, str], ...],
) -> list[Chunk]:
    """Split out sections whose headers _SANHITA_HEADER provably cannot
    match in this source (see SourceMeta.section_splits). Every failure
    mode raises rather than degrades: a repair that no longer applies
    means the source text changed underneath it, and silently keeping a
    merged chunk is exactly the citation-attribution defect this exists
    to fix."""
    by_unit = {c.unit_number: c for c in chunks}
    for host_unit, new_unit, header_pattern, title in splits:
        host = by_unit.get(host_unit)
        if host is None:
            raise ValueError(
                f"'{source_id}' section_splits names host unit {host_unit!r}, "
                f"which the chunker did not produce."
            )
        if new_unit in by_unit:
            raise ValueError(
                f"'{source_id}' section_splits would create unit {new_unit!r}, "
                f"but the chunker already produced it; drop the stale repair."
            )
        matches = list(re.finditer(header_pattern, host.text))
        if len(matches) != 1:
            raise ValueError(
                f"'{source_id}' section_splits pattern for unit {new_unit!r} "
                f"matched {len(matches)} times in chunk {host.chunk_id} "
                f"(expected exactly 1); the source layout has changed."
            )
        m = matches[0]
        new_text = host.text[m.end():].strip()
        host_text = host.text[: m.start()].strip()
        if not new_text or not host_text:
            raise ValueError(
                f"'{source_id}' section_splits for unit {new_unit!r} would "
                f"produce an empty chunk; refusing."
            )
        host.text = host_text
        new_chunk = Chunk(
            chunk_id=f"{source_id}:{new_unit}",
            source_id=source_id,
            unit_number=new_unit,
            title=title,
            text=new_text,
        )
        chunks.insert(chunks.index(host) + 1, new_chunk)
        by_unit[new_unit] = new_chunk
    return chunks


CHUNKERS = {
    "sanhita": chunk_sanhita,
    "constitution": chunk_constitution,
}
