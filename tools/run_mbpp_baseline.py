#!/usr/bin/env python3
"""Direct-model MBPP baseline using the official AFlow operator and benchmark.

This is *not* the AFlow MCTS-optimized workflow. Run in a disposable sandbox:
the official MBPP evaluator executes model-generated code.
"""
import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.mbpp import MBPPBenchmark
from scripts.async_llm import LLMsConfig, create_llm_instance
from scripts.operators import CustomCodeGenerate


class DirectCodeWorkflow:
    def __init__(self, llm_config):
        self.llm = create_llm_instance(llm_config)
        self.generator = CustomCodeGenerate(self.llm)

    async def __call__(self, problem, entry_point):
        response = await self.generator(problem=problem, entry_point=entry_point, instruction="")
        return response["response"], self.llm.get_usage_summary()["total_cost"]


async def evaluate(args):
    if args.split == "test" and not args.allow_test:
        raise ValueError("Test split is held out. Pass --allow-test for a final evaluation.")
    data = Path("data/datasets") / f"mbpp_{args.split}.jsonl"
    if not data.is_file():
        raise FileNotFoundError(f"Missing {data}. Download official AFlow datasets first.")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    config = LLMsConfig.default().get(args.model)
    benchmark = MBPPBenchmark(name="MBPP", file_path=str(data), log_path=str(output))
    workflow = DirectCodeWorkflow(config)
    indices = list(range(args.limit)) if args.limit else None
    score, avg_cost, total_cost = await benchmark.run_evaluation(
        workflow, indices, max_concurrent_tasks=args.concurrency
    )
    receipt = {
        "method": "direct_model_baseline",
        "not_aflow_optimized": True,
        "dataset": "MBPP",
        "split": args.split,
        "model": args.model,
        "limit": args.limit,
        "concurrency": args.concurrency,
        "accuracy": score,
        "avg_reported_cost": avg_cost,
        "total_reported_cost": total_cost,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt_file = output / "baseline_receipt.json"
    receipt_file.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Name in config/config2.yaml")
    parser.add_argument("--split", choices=("validate", "test"), default="validate")
    parser.add_argument("--allow-test", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="0 = full split; >0 is a smoke check")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--output", default="experiments/mbpp-baseline")
    args = parser.parse_args()
    if args.limit < 0 or args.concurrency < 1:
        parser.error("--limit must be >= 0 and --concurrency must be >= 1")
    asyncio.run(evaluate(args))


if __name__ == "__main__":
    main()
