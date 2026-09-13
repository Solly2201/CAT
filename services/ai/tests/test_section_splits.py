"""Regression tests for the curated section-split repairs
(SourceMeta.section_splits): the four sections whose headers the general
_SANHITA_HEADER pattern provably cannot match (BNS 217/255 wrap their
titles across a line break; JJ Act 61/86 open with an
amendment-substitution bracket) and RTI s.14, whose header OCR omits the
full stop before the em-dash and whose text previously vanished inside
the excluded s.13 chunk.

Each check is anchored to real, independently verifiable statutory text,
in the same style as test_ingestion.py: if a source PDF replacement or a
chunker change silently re-merges one of these sections -- restoring the
citation-attribution defect -- these fail.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ingestion.pipeline import load_chunks  # noqa: E402
from app.ingestion.sources import get_source  # noqa: E402


def _by_unit(source_id):
    return {c.unit_number: c for c in load_chunks(source_id)}


def test_bns_217_is_its_own_chunk():
    chunks = _by_unit("bns")
    assert "217" in chunks
    c = chunks["217"]
    assert c.title.startswith("False information, with intent")
    assert "Whoever gives to any public servant any information" in c.text
    # The section's illustrations travelled with it, not with s.216.
    assert "falsely informs a policeman" in c.text


def test_bns_255_is_its_own_chunk():
    chunks = _by_unit("bns")
    assert "255" in chunks
    c = chunks["255"]
    assert c.title.startswith("Public servant disobeying direction of law")
    assert "knowingly disobeys any direction of the law" in c.text


def test_bns_hosts_no_longer_carry_the_split_sections():
    chunks = _by_unit("bns")
    assert "Whoever gives to any public servant any information" not in chunks["216"].text
    assert "knowingly disobeys any direction of the law" not in chunks["254"].text


def test_jj_61_is_its_own_chunk():
    chunks = _by_unit("jj2015")
    assert "61" in chunks
    c = chunks["61"]
    assert c.title == "Procedure for disposal of adoption proceedings"
    assert "Before issuing an adoption order" in c.text
    assert "Before issuing an adoption order" not in chunks["60"].text


def test_jj_86_is_its_own_chunk():
    chunks = _by_unit("jj2015")
    assert "86" in chunks
    c = chunks["86"]
    assert c.title == "Classification of offences and designated court"
    assert "punishable with imprisonment for a term of more than seven years" in c.text
    assert "punishable with imprisonment" not in chunks["85"].text


def test_rti_14_recovered_and_13_still_excluded():
    chunks = _by_unit("rti")
    assert "14" in chunks
    c = chunks["14"]
    assert c.title == (
        "Removal of Chief Information Commissioner or Information Commissioner"
    )
    assert "removed from his office only by order of the President" in c.text
    # s.13 (replaced by the 2019 amendment) must stay excluded: the split
    # runs before exclusions precisely so recovering s.14 does not
    # resurrect the superseded text it was buried in.
    assert "13" not in chunks


def test_split_chunks_cite_their_own_unit():
    for source_id, unit in [
        ("bns", "217"),
        ("bns", "255"),
        ("jj2015", "61"),
        ("jj2015", "86"),
        ("rti", "14"),
    ]:
        chunk = _by_unit(source_id)[unit]
        citation = chunk.citation(get_source(source_id))
        assert citation["unit"] == f"Section {unit}"
