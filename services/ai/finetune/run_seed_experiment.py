#!/usr/bin/env python3
"""Repeated-seed stability experiment driver.

Trains the promoted configuration once per seed -- identical corpus,
triplet splits (finetune/data/*.jsonl, frozen), loss, epochs, batch
size, learning rate, warmup and promotion-relevant evaluation protocol;
the ONLY variable is the random seed -- then evaluates every run on the
production path (deployed benchmark + held-out slice) via eval_seeds.py.

No per-seed tuning of any kind. Existing run directories are skipped so
the driver is resumable.

Usage:
  python finetune/run_seed_experiment.py            # seeds 42..46
  python finetune/run_seed_experiment.py --seeds 42 43 44
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

AI_ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(os.path.dirname(__file__), "output")


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    env = dict(os.environ, USE_TF="0")
    subprocess.run(cmd, cwd=AI_ROOT, env=env, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    args = parser.parse_args()

    for seed in args.seeds:
        run_name = f"seed{seed}_rev"
        model_dir = os.path.join(OUT, run_name, "model")
        if os.path.exists(model_dir):
            print(f"[skip] {run_name}: model already trained", flush=True)
        else:
            run([sys.executable, "finetune/train.py", "--run-name", run_name, "--seed", str(seed)])
        eval_json = os.path.join(OUT, run_name, "seed_eval.json")
        if os.path.exists(eval_json):
            print(f"[skip] {run_name}: already evaluated", flush=True)
        else:
            run([
                sys.executable, "finetune/eval_seeds.py",
                "--model", os.path.join("finetune", "output", run_name, "model"),
                "--label", run_name,
                "--json-out", eval_json,
            ])
    print("Seed experiment complete.", flush=True)


if __name__ == "__main__":
    main()
