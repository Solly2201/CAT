#!/usr/bin/env python3
"""Production-path evaluation of one or more candidate encoders, for the
repeated-seed stability experiment and for re-measuring the deployed
model after a corpus correction.

For each model this reports, on the production path (retrieval on
app.query.normalize's output, the exact text the deployed pipeline
searches, same guards and gate):

  - deployed benchmark: citizen 281 / control 46 retrieval metrics,
    abstention over all rows (313 / 49), false accepts / false abstains,
    wrong-Act top-1 counts, hard-negative Recall@5 (29 rows);
  - held-out slice: the finetune/data/test.jsonl query groups (41
    citizen / 9 control), never trained or selected on.

Reuses eval/run_eval.py's metric functions and eval_candidate.py's
temp-index machinery, so numbers are directly comparable to every
recorded baseline and the production index is never written to.

Usage:
  python finetune/eval_seeds.py --model data/models/m12_run2 --label m12_run2
  python finetune/eval_seeds.py --model sentence-transformers/all-MiniLM-L6-v2 --label base
  python finetune/eval_seeds.py --model finetune/output/seed43/model --label seed43
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "eval"))

from finetune.eval_candidate import build_temp_index, point_search_at  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EVAL_DIR = os.path.join(os.path.dirname(__file__), "..", "eval")


def held_out_query_ids() -> dict[str, set[str]]:
    with open(os.path.join(DATA_DIR, "test.jsonl"), encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    out = {"orig": set(), "human": set()}
    for r in rows:
        tag, qid = r["query_id"].split(":", 1)
        out["orig" if tag == "orig" else "human"].add(qid)
    return out


def _wrong_act_top1(retrieval_results) -> list[str]:
    """Answer-expected rows whose rank-1 chunk belongs to an Act other
    than every labelled target's Act (the docs' wrong-Act top-1 count)."""
    ids = []
    for r in retrieval_results:
        if not r.retrieved_ids or not r.relevant_ids:
            continue
        top_source = r.retrieved_ids[0].split(":", 1)[0]
        target_sources = {c.split(":", 1)[0] for c in r.relevant_ids}
        if top_source not in target_sources:
            ids.append(r.query_id)
    return ids


def _hard_negative_recall(retrieval_results, top_k: int = 5) -> dict:
    rows = [r for r in retrieval_results if r.category == "hard_negative"]
    hit = sum(
        1
        for r in rows
        if r.relevant_ids and r.relevant_ids <= set(r.retrieved_ids[:top_k])
    )
    return {"hit": hit, "total": len(rows)}


def _evaluate_set(queries, mode: str = "hybrid", top_k: int = 5) -> dict:
    from run_eval import evaluate_abstention, evaluate_retrieval, summarize

    retrieval_results = evaluate_retrieval(queries, mode, top_k, production_path=True)
    abstention = evaluate_abstention(queries, mode)
    summary = summarize(mode, retrieval_results, top_k)
    summary["abstention_accuracy"] = round(abstention["accuracy"], 4)
    summary["false_accepts"] = len(abstention["false_answer_ids"])
    summary["false_abstains"] = len(abstention["false_abstain_ids"])
    summary["false_accept_ids"] = abstention["false_answer_ids"]
    summary["false_abstain_ids"] = abstention["false_abstain_ids"]
    summary["wrong_routing_ids"] = abstention["wrong_routing_ids"]
    wrong = _wrong_act_top1(retrieval_results)
    summary["wrong_act_top1"] = len(wrong)
    summary["wrong_act_top1_ids"] = wrong
    hn = _hard_negative_recall(retrieval_results, top_k)
    if hn["total"]:
        summary["hard_negative_recall"] = f"{hn['hit']}/{hn['total']}"
    summary["per_query_top5"] = {
        r.query_id: r.retrieved_ids for r in retrieval_results
    }
    return summary


def evaluate_model(model_path_or_name: str, label: str) -> dict:
    from run_eval import load_queries

    temp_dir = os.path.join(tempfile.gettempdir(), f"cap_seed_eval_{label}")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    build_temp_index(model_path_or_name, temp_dir)
    point_search_at(temp_dir)

    held = held_out_query_ids()
    citizen = load_queries(os.path.join(EVAL_DIR, "queries_human.jsonl"))
    control = load_queries(os.path.join(EVAL_DIR, "queries.jsonl"))

    results = {
        "label": label,
        "model": model_path_or_name,
        "deployed_citizen": _evaluate_set(citizen),
        "deployed_control": _evaluate_set(control),
        "heldout_citizen": _evaluate_set(
            [q for q in citizen if q["id"] in held["human"]]
        ),
        "heldout_control": _evaluate_set(
            [q for q in control if q["id"] in held["orig"]]
        ),
    }
    shutil.rmtree(temp_dir, ignore_errors=True)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args()

    results = evaluate_model(args.model, args.label)

    slim = json.loads(json.dumps(results))
    for k in list(slim):
        if isinstance(slim[k], dict):
            slim[k].pop("per_query_top5", None)
    print(json.dumps(slim, indent=2))

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nWritten to {args.json_out}")


if __name__ == "__main__":
    main()
