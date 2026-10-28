#!/usr/bin/env python3
"""Preflight report: never downloads data, invokes models, or prints secrets."""
import argparse
import json
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ("HumanEval", "MBPP", "GSM8K", "MATH", "HotpotQA", "DROP")


def inspect(dataset):
    data_root = ROOT / "data" / "datasets"
    config_path = ROOT / "config" / "config2.yaml"
    initial_path = ROOT / "workspace" / dataset / "workflows" / "round_1" / "graph.py"
    return {
        "dataset": dataset,
        "python": platform.python_version(),
        "original_algorithm": (ROOT / "scripts" / "optimizer.py").exists(),
        "initial_workflow": initial_path.exists(),
        "config_present": config_path.exists(),
        "validation_data_present": (data_root / f"{dataset.lower()}_validate.jsonl").exists(),
        "test_data_present": (data_root / f"{dataset.lower()}_test.jsonl").exists(),
        "note": "Presence checks only; no model or benchmark has run.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=DATASETS, default="MBPP")
    parser.add_argument("--strict", action="store_true", help="Fail unless config and datasets exist.")
    args = parser.parse_args()
    report = inspect(args.dataset)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.strict and not all(
        report[k] for k in (
            "original_algorithm", "initial_workflow", "config_present",
            "validation_data_present", "test_data_present"
        )
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
