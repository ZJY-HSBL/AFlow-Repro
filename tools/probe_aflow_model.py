#!/usr/bin/env python3
"""Run an actual open-weight LLM on AFlow's original optimizer prompt.

This probes *proposal feasibility only*; it neither executes the generated
graph nor claims any search improvement. It distinguishes XML parser success
from a genuinely complete and compilable workflow response.
"""
import argparse
import asyncio
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.optimizer import GraphOptimize
from scripts.optimizer_utils.graph_utils import GraphUtils
from scripts.prompts.optimize_prompt import WORKFLOW_TEMPLATE
from scripts.formatter import XmlFormatter
from tools.run_mbpp_cpu import LocalTransformersAdapter

UPSTREAM = Path("workspace/MBPP/workflows/round_1")
MODEL = "Qwen/Qwen2.5-Coder-0.5B-Instruct"


async def evaluate(args):
    utils = GraphUtils("workspace/MBPP")
    original_prompt, graph_content = utils.read_graph_files(1, "workspace/MBPP/workflows")
    graph = utils.extract_solve_graph(graph_content)
    if len(graph) != 1:
        raise ValueError("Expected exactly one original workflow class")
    descriptions = utils.load_operators_description(
        ["Custom", "CustomCodeGenerate", "ScEnsemble", "Test"]
    )
    full_prompt = utils.create_graph_optimize_prompt(
        experience="No previous optimization experience.",
        score=1 / 6,  # Actual six-task measured baseline (small sample).
        graph=graph[0], prompt=original_prompt,
        operator_description=descriptions, type="code", log_data="",
    )
    model = LocalTransformersAdapter(MODEL, args.max_new_tokens)
    response = await asyncio.to_thread(model._infer, full_prompt)
    formatter = XmlFormatter.from_model(GraphOptimize)
    parser_ok, fields = formatter.validate_response(response)
    required = ["modification", "graph", "prompt"]
    fields = fields or {}
    nonempty = {field: bool(str(fields.get(field, "")).strip()) for field in required}
    compile_ok = False
    error = None
    if nonempty["graph"]:
        try:
            ast.parse(WORKFLOW_TEMPLATE.format(
                graph=fields["graph"], round=2, dataset="MBPP"
            ))
            compile_ok = True
        except (SyntaxError, ValueError, KeyError) as exc:
            error = f"{type(exc).__name__}: {exc}"
    strict = bool(parser_ok and all(nonempty.values()) and compile_ok)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output = {
        "experiment": "real_open_weight_model_AFlow_graph_proposal_schema_probe",
        "is_full_optimizer_search": False,
        "is_paper_equivalent": False,
        "model": MODEL,
        "checkpoint": model.revision,
        "max_new_tokens": args.max_new_tokens,
        "source_prompt_round": 1,
        "score_in_optimizer_prompt": 1 / 6,
        "score_source": "Measured tiny six-task direct-model validation baseline (v0.2.0)",
        "optimizer_prompt_sha256": hashlib.sha256(full_prompt.encode()).hexdigest(),
        "optimizer_prompt_characters": len(full_prompt),
        "prompt_tokens": model.prompt_tokens,
        "generated_tokens": model.output_tokens,
        "xml_formatter_accepted": parser_ok,
        "required_fields_nonempty": nonempty,
        "generated_graph_ast_valid": compile_ok,
        "strict_structural_acceptance": strict,
        "graph_compile_error": error,
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "warning": "No generated candidate was run. This is a raw LLM proposal quality check, not MCTS optimization.",
    }
    (output_dir / "proposal_raw.txt").write_text(response, encoding="utf-8")
    (output_dir / "proposal_report.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print("REAL_AFLOW_PROPOSAL_PROBE=" + json.dumps(output))
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-new-tokens", type=int, default=320)
    parser.add_argument("--output", default="experiments/aflow-real-proposal-probe")
    args = parser.parse_args()
    if args.max_new_tokens < 1:
        parser.error("max-new-tokens must be positive")
    asyncio.run(evaluate(args))


if __name__ == "__main__":
    main()
