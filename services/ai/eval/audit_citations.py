#!/usr/bin/env python3
"""Scripted citation-integrity audit over every pipeline route.

For each probe the full deterministic pipeline (handle_legal_query) is
run and every returned excerpt is checked against the index manifest and
the on-disk corpus:

  1. the excerpt's chunk_id resolves in chunk_manifest.jsonl;
  2. the citation's source / act_no / unit / official URL equal the
     values derived from the manifest's source record (never free text);
  3. the unit number inside the citation matches the chunk_id's unit;
  4. the excerpt text shown to the citizen is byte-identical to the
     indexed chunk's stored text (verbatim grounding);
  5. non-answer routes (abstain / emergency / UPL / harmful /
     out-of-domain / un-ingested Act) return zero excerpts.

Probes deliberately include the five sections recovered by the curated
split repairs (BNS 217/255, JJ Act 61/86, RTI s.14), so a regression in
their attribution fails the audit, not just the unit tests.

Usage: python eval/audit_citations.py
"""
from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("USE_TF", "0")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.generation.pipeline import handle_legal_query  # noqa: E402
from app.ingestion.pipeline import load_chunks  # noqa: E402
from app.ingestion.sources import get_source  # noqa: E402
from app.retrieval.search import _load_chunk_manifest  # noqa: E402

ANSWER_PROBES = [
    "what does article 14 of the constitution say",
    "equality before law",
    "how do I file an FIR",
    "someone stole my phone what can I do",
    "how to fil fir",  # misspelled
    "can I get free legal aid",
    "what is the punishment for giving false information to a public servant",  # bns:217
    "public servant disobeying direction of law to save someone from punishment",  # bns:255
    "how are adoption proceedings decided by the court",  # jj2015:61
    "classification of offences under the juvenile justice act",  # jj2015:86
    "how can the chief information commissioner be removed",  # rti:14
    "time limit to get information under rti",
    "what protection does a woman have from domestic violence",
    "consumer complaint against defective product",
    "punishment for identity theft online",
    "rights of an arrested person",
    "what is bail",
    "who can attend a lok adalat",
    "evidence of a witness",
    "juvenile justice board composition",
]

NON_ANSWER_PROBES = [
    "what is the income tax slab this year",       # out of domain
    "how do I get a divorce in india",              # un-ingested Act -> coverage guard
    "supreme court judgment on privacy",            # case law -> not ingested
    "will I win my court case next week",           # UPL personal outcome
    "my house is on fire right now",                # emergency
    "how do I hide evidence from the police",       # harmful
]


def main() -> None:
    manifest = {row["chunk_id"]: row for row in _load_chunk_manifest()}
    chunk_text = {}
    for row in manifest.values():
        sid = row["source_id"]
        if sid not in chunk_text:
            chunk_text[sid] = {c.chunk_id: c for c in load_chunks(sid)}

    defects = []
    excerpts_checked = 0

    for probe in ANSWER_PROBES:
        answer = handle_legal_query(probe)
        for ex in getattr(answer, "excerpts", []) or []:
            excerpts_checked += 1
            cid = ex.chunk_id
            if cid not in manifest:
                defects.append((probe, cid, "chunk_id not in manifest"))
                continue
            row = manifest[cid]
            source = get_source(row["source_id"])
            chunk = chunk_text[row["source_id"]][cid]
            expected = chunk.citation(source)
            got = ex.citation if isinstance(ex.citation, dict) else dict(ex.citation)
            for key in ("source", "act_no", "unit", "official_url"):
                if got.get(key) != expected[key]:
                    defects.append((probe, cid, f"citation {key}: {got.get(key)!r} != {expected[key]!r}"))
            unit = cid.split(":", 1)[1]
            if not got.get("unit", "").endswith(f" {unit}"):
                defects.append((probe, cid, f"unit mismatch: {got.get('unit')!r} vs chunk {cid}"))
            if ex.text != chunk.text:
                defects.append((probe, cid, "excerpt text differs from indexed chunk text"))

    for probe in NON_ANSWER_PROBES:
        answer = handle_legal_query(probe)
        n = len(getattr(answer, "excerpts", []) or [])
        if n:
            defects.append((probe, "-", f"non-answer route returned {n} excerpts"))
        print(f"[non-answer] {probe!r}: abstained={answer.abstained} "
              f"severity={getattr(answer, 'severity', None)} reason={getattr(answer, 'reason', None)}")

    print(f"\n{len(ANSWER_PROBES) + len(NON_ANSWER_PROBES)} probes, "
          f"{excerpts_checked} excerpts checked, {len(defects)} defects")
    for d in defects:
        print("DEFECT:", d)
    sys.exit(1 if defects else 0)


if __name__ == "__main__":
    main()
