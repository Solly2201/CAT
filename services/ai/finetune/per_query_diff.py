#!/usr/bin/env python3
"""Per-query hit/miss comparison for base vs candidate model on the
held-out test split, to distinguish 'nothing changed' from 'offsetting
gains and losses' when the aggregate recall@5 is unchanged."""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

os.environ.setdefault("USE_TF", "0")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "eval"))

from finetune.eval_candidate import build_temp_index, point_search_at  # noqa: E402
from finetune.eval_heldout import held_out_query_ids  # noqa: E402

EVAL_DIR = os.path.join(os.path.dirname(__file__), "..", "eval")


def per_query_hits(model_path_or_name: str, label: str, held: set[str], path: str) -> dict[str, bool]:
    from run_eval import load_queries
    from app.retrieval.search import search

    temp_dir = os.path.join(tempfile.gettempdir(), f"cap_diff_index_{label}")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    build_temp_index(model_path_or_name, temp_dir)
    point_search_at(temp_dir)

    queries = [q for q in load_queries(path) if q["id"] in held and not q["expect_abstain"]]
    hits = {}
    for q in queries:
        results = search(q["query"], top_k=5, mode="hybrid")
        retrieved = {h["chunk_id"] for h in results}
        relevant = set(q["relevant_chunk_ids"])
        hits[q["id"]] = bool(retrieved & relevant)
    shutil.rmtree(temp_dir, ignore_errors=True)
    return hits


def main() -> None:
    held_out = held_out_query_ids()
    path = os.path.join(EVAL_DIR, "queries_human.jsonl")
    base_hits = per_query_hits("sentence-transformers/all-MiniLM-L6-v2", "diff_base", held_out["human"], path)
    cand_hits = per_query_hits(
        os.path.join(os.path.dirname(__file__), "output", "run1", "model"), "diff_cand", held_out["human"], path
    )

    print(f"{'query_id':10s} {'base':6s} {'candidate':10s} change")
    improved, regressed, same = [], [], []
    for qid in sorted(base_hits):
        b, c = base_hits[qid], cand_hits[qid]
        if b == c:
            change = "same"
            same.append(qid)
        elif not b and c:
            change = "IMPROVED"
            improved.append(qid)
        else:
            change = "REGRESSED"
            regressed.append(qid)
        print(f"{qid:10s} {str(b):6s} {str(c):10s} {change}")

    print()
    print(f"improved: {improved}")
    print(f"regressed: {regressed}")
    print(f"same: {len(same)}")


if __name__ == "__main__":
    main()
