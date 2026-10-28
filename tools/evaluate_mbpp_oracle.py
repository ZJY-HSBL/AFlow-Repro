#!/usr/bin/env python3
"""Oracle/evaluator integration check using the *actual* AFlow author MBPP files.

Reference solutions are used only to validate the evaluation pipeline. This is
NOT a model baseline and NOT an AFlow paper metric.
"""
import argparse
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from tools.sandbox_mbpp import SandboxedMBPPBenchmark


async def run(args):
    data_path = Path("data/datasets") / f"mbpp_{args.split}.jsonl"
    if not data_path.is_file():
        raise FileNotFoundError(f"Missing official AFlow author data: {data_path}")
    contents = data_path.read_bytes()
    rows = [json.loads(line) for line in contents.splitlines() if line.strip()]
    if not rows:
        raise ValueError("Empty MBPP split")
    required = {"prompt", "code", "test", "entry_point"}
    for index, row in enumerate(rows):
        if not required.issubset(row):
            raise ValueError(f"Row {index} missing keys: {required - set(row)}")
    requested = min(args.limit, len(rows))
    responses = {row["prompt"]: row["code"] for row in rows[:requested]}

    async def reference_oracle(problem, entry_point):
        return responses[problem], 0.0

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    benchmark = SandboxedMBPPBenchmark("MBPP", str(data_path), str(output))
    score, _, _ = await benchmark.run_evaluation(
        reference_oracle, list(range(requested)), max_concurrent_tasks=2,
    )
    report = {
        "type": "reference_oracle_evaluator_check",
        "is_llm_result": False,
        "is_paper_replication": False,
        "source": "AFlow author-provided MBPP split",
        "split": args.split,
        "dataset_sha256": hashlib.sha256(contents).hexdigest(),
        "dataset_rows": len(rows),
        "evaluated_rows": requested,
        "reference_test_pass_rate": score,
        "execution": "Docker no-network read-only sandbox, Python 3.11",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "oracle_summary.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["validate", "test"], default="validate")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--output", default="experiments/author-mbpp-oracle")
    args = ap.parse_args()
    if args.limit < 1:
        ap.error("--limit must be positive")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
