#!/usr/bin/env python3
"""Execute one *unaltered AFlow Optimizer._optimize_graph* search step.

Transport is a deterministic reference-code fixture, NOT a model. The actual
AFlow graph loader, original search/selection/experience logic, generated
Python workflow and MBPP benchmark are exercised with 3 author validation
cases. Executable code is scored only in a sandboxed no-network container.

Do not publish the harness's oracle scores as model accuracy.
"""
import argparse
import asyncio
import hashlib
import json
import os
import random
import shutil
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import numpy as np

import scripts.async_llm as async_llm
import scripts.optimizer as original_optimizer
import scripts.optimizer_utils.evaluation_utils as evaluation_utils
from scripts.evaluator import Evaluator
from scripts.formatter import CodeFormatter, XmlFormatter
from tools.sandbox_mbpp import SandboxedMBPPBenchmark

DATASET = Path("data/datasets/mbpp_validate.jsonl")
ROOT = Path("workspace/MBPP/workflows")
OPERATOR_GRAPH = '''
class Workflow:
    def __init__(self, name, llm_config, dataset):
        self.name = name
        self.dataset = dataset
        self.llm = create_llm_instance(llm_config)
        self.custom_code_generate = operator.CustomCodeGenerate(self.llm)

    async def __call__(self, problem: str, entry_point: str):
        result = await self.custom_code_generate(
            problem=problem, entry_point=entry_point, instruction=""
        )
        return result["response"], self.llm.get_usage_summary()["total_cost"]
'''.strip()


class DeterministicFixtureTransport:
    """Uses dataset-provided reference programs, never a pretrained LM."""

    def __init__(self, problems):
        self.problems = problems
        self.calls = {"code": 0, "proposal": 0}

    async def call_with_format(self, prompt, formatter):
        if isinstance(formatter, CodeFormatter):
            matches = [row for row in self.problems if row["prompt"] in prompt]
            if len(matches) != 1:
                raise ValueError(f"Expected one reference task, found {len(matches)}")
            self.calls["code"] += 1
            code = matches[0]["code"]  # Author JSONL already contains the complete function.
            valid, data = formatter.validate_response(code)
            if not valid:
                raise ValueError(f"Reference code validation failed: {data}")
            return data
        if isinstance(formatter, XmlFormatter):
            self.calls["proposal"] += 1
            return {
                "modification": "harness_only_equivalent_workflow",
                "graph": OPERATOR_GRAPH,
                "prompt": "HARNESS ONLY: fixed workflow. Not an LM proposal.",
            }
        raise ValueError(f"Unexpected formatter: {type(formatter).__name__}")

    def get_usage_summary(self):
        return {"total_cost": 0.0}


class BoundedSandboxEvaluator(Evaluator):
    """Only adapts validation subset and process isolation; source unchanged."""
    count = 3

    async def graph_evaluate(self, dataset, graph, params, path, is_test=False):
        if dataset != "MBPP" or is_test:
            raise ValueError("Harness only permits 3 MBPP validation examples")
        benchmark = SandboxedMBPPBenchmark(
            "MBPP", str(DATASET), path
        )
        configured = await self._configure_graph(dataset, graph, params)
        return await benchmark.run_evaluation(
            configured, list(range(self.count)), max_concurrent_tasks=1
        )


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def run(args):
    if not DATASET.is_file():
        raise FileNotFoundError("Original author MBPP dataset missing")
    data = [json.loads(line) for line in DATASET.read_text("utf-8").splitlines() if line]
    if len(data) < args.limit:
        raise ValueError("Not enough author validation examples")
    if (ROOT / "round_2").exists() or (ROOT / "results.json").exists():
        raise RuntimeError("Harness requires a clean checkout (no previous optimizer results)")

    fixture = DeterministicFixtureTransport(data[:args.limit])
    BoundedSandboxEvaluator.count = args.limit
    random.seed(0)
    np.random.seed(0)

    # Actual Optimizer._optimize_graph() is executed without modifying its code.
    with ExitStack() as stack:
        stack.enter_context(patch.object(async_llm, "create_llm_instance", return_value=fixture))
        stack.enter_context(patch.object(original_optimizer, "create_llm_instance", return_value=fixture))
        stack.enter_context(patch.object(evaluation_utils, "Evaluator", BoundedSandboxEvaluator))

        optimizer = original_optimizer.Optimizer(
            dataset="MBPP", question_type="code",
            opt_llm_config="deterministic-harness",
            exec_llm_config="deterministic-harness",
            operators=["Custom", "CustomCodeGenerate", "ScEnsemble", "Test"],
            optimized_path="workspace", sample=4, initial_round=1,
            max_rounds=1, validation_rounds=1, check_convergence=False,
        )
        score = await asyncio.wait_for(
            optimizer._optimize_graph(), timeout=args.timeout
        )

    result_path = ROOT / "results.json"
    experience_path = ROOT / "round_2/experience.json"
    generated = ROOT / "round_2/graph.py"
    if not all(p.is_file() for p in [result_path, experience_path, generated]):
        raise RuntimeError("Original optimizer did not produce all expected evidence")
    rows = json.loads(result_path.read_text("utf-8"))
    experience = json.loads(experience_path.read_text("utf-8"))
    if [x["round"] for x in rows] != [1, 2]:
        raise AssertionError("Expected original baseline + one generated round")
    if fixture.calls["proposal"] != 1 or fixture.calls["code"] != 2 * args.limit:
        raise AssertionError("Expected one proposal and 2N graded programs")
    if experience["father node"] != 1 or experience["modification"] != "harness_only_equivalent_workflow":
        raise AssertionError("Original AFlow experience record corrupted")
    output = {
        "kind": "deterministic_optimizer_end_to_end_integration",
        "is_real_model_result": False,
        "is_paper_metric": False,
        "is_model_generated_proposal": False,
        "uses_unmodified_AFlow_optimizer": True,
        "dataset": "AFlow MBPP author validation",
        "dataset_sha256": digest(DATASET),
        "n_validation_examples": args.limit,
        "seed": 0,
        "measured_baseline_validation": rows[0]["score"],
        "measured_generated_validation": rows[1]["score"],
        "optimizer_returned_score": score,
        "optimization_proposals": fixture.calls["proposal"],
        "reference_program_executions": fixture.calls["code"],
        "experience": experience,
        "generated_graph_sha256": digest(generated),
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "warning": "Scores use oracle reference code and a scripted proposal; NOT an LLM or novel search performance measure.",
    }
    path = Path(args.output)
    path.mkdir(parents=True, exist_ok=True)
    (path / "summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    for filename, source in [
        ("original_search_results.json", result_path),
        ("original_experience.json", experience_path),
        ("generated_graph.py", generated),
    ]:
        shutil.copy2(source, path / filename)
    print("AFLOW_DETERMINISTIC_SEARCH_HARNESS=" + json.dumps(output))
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--output", default="experiments/aflow-search-harness")
    args = parser.parse_args()
    if not (1 <= args.limit <= 10) or args.timeout < 1:
        parser.error("limit must be 1..10; timeout >= 1")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
