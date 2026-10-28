"""Strict, side-effect-free validation before importing a model-generated AFlow graph.

Upstream XmlFormatter reports syntactic XML extraction as success even if the
three optional Pydantic fields are absent. AFlow subsequently indexes them,
loads the generated prompt as Python, and imports arbitrary generated code.

This separate preflight checks structure but IS NOT a security sandbox.
"""
import ast
from typing import Mapping, Any

from scripts.prompts.optimize_prompt import WORKFLOW_TEMPLATE


def validate_graph_proposal(proposal: Mapping[str, Any], dataset="MBPP", round_number=2):
    reasons = []
    if not isinstance(proposal, dict):
        return {"accepted": False, "reasons": ["response is not a dictionary"]}
    required = ("modification", "graph", "prompt")
    for name in required:
        if not isinstance(proposal.get(name), str) or not proposal[name].strip():
            reasons.append(f"missing or empty {name}")
    if "missing or empty graph" not in reasons:
        try:
            graph_source = WORKFLOW_TEMPLATE.format(
                graph=proposal["graph"], dataset=dataset, round=round_number
            )
            parsed = ast.parse(graph_source)
            workflow_classes = [
                node for node in parsed.body
                if isinstance(node, ast.ClassDef) and node.name == "Workflow"
            ]
            if len(workflow_classes) != 1:
                reasons.append("generated graph must define exactly one Workflow class")
        except (SyntaxError, KeyError, ValueError) as exc:
            reasons.append(f"invalid graph Python: {type(exc).__name__}: {exc}")
    if "missing or empty prompt" not in reasons:
        try:
            ast.parse(proposal["prompt"])
        except SyntaxError as exc:
            reasons.append(f"invalid prompt Python: {type(exc).__name__}: {exc}")
    return {
        "accepted": not reasons,
        "reasons": reasons,
        "note": "Syntax/structural checks only, NOT a secure code execution boundary.",
    }
