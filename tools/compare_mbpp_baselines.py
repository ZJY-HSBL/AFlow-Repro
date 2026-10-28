#!/usr/bin/env python3
"""Paired comparison of two REAL AFlow MBPP direct-model evaluation runs.

Checks dataset/model identity and task order. Uses exact McNemar as an
exploratory diagnostic only; tiny samples must never imply generalization.
"""
import argparse
import csv
import html
import json
import math
from pathlib import Path


def read_run(meta_path, csv_path):
    metadata = json.loads(Path(meta_path).read_text("utf-8"))
    with Path(csv_path).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("Empty baseline CSV")
    scores = [float(row["score"]) for row in rows]
    if any(s not in {0.0, 1.0} for s in scores):
        raise ValueError("MBPP scores must be binary")
    if len(rows) != metadata["evaluated_examples"]:
        raise ValueError("CSV does not match reported number of examples")
    if not math.isclose(sum(scores) / len(scores), metadata["accuracy"], abs_tol=1e-9):
        raise ValueError("CSV scores disagree with summary")
    return metadata, rows, scores


def exact_mcnemar_p(b, c):
    discordant = b + c
    if not discordant:
        return 1.0
    smaller = min(b, c)
    return min(1.0, 2.0 * sum(math.comb(discordant, k)
                            for k in range(smaller + 1)) / (2 ** discordant))


def compare(first, second):
    a_meta, a_rows, a_scores = first
    b_meta, b_rows, b_scores = second
    for key in ("dataset_sha256", "model", "model_sha", "evaluated_examples"):
        if a_meta.get(key) != b_meta.get(key):
            raise ValueError(f"Runs not paired: mismatch in {key}")
    if a_meta["max_new_tokens"] == b_meta["max_new_tokens"]:
        raise ValueError("The decoding token limits must differ")
    if [row["inputs"] for row in a_rows] != [row["inputs"] for row in b_rows]:
        raise ValueError("Prompt order changed, so this is not a paired experiment")
    improved = sum(a == 0 and b == 1 for a, b in zip(a_scores, b_scores))
    worsened = sum(a == 1 and b == 0 for a, b in zip(a_scores, b_scores))
    return {
        "experiment_type": "paired_validation_decoding_length_ablation",
        "not_aflow_optimization": True,
        "not_paper_replication": True,
        "dataset_sha256": a_meta["dataset_sha256"],
        "model_sha": a_meta["model_sha"],
        "n": len(a_scores),
        "configuration_a": {"max_new_tokens": a_meta["max_new_tokens"],
                            "passed": int(sum(a_scores)),
                            "accuracy": a_meta["accuracy"],
                            "generated_tokens": a_meta["total_generated_tokens"]},
        "configuration_b": {"max_new_tokens": b_meta["max_new_tokens"],
                            "passed": int(sum(b_scores)),
                            "accuracy": b_meta["accuracy"],
                            "generated_tokens": b_meta["total_generated_tokens"]},
        "delta_accuracy_percentage_points":
            (sum(b_scores) - sum(a_scores)) * 100 / len(a_scores),
        "improved_tasks": improved,
        "worsened_tasks": worsened,
        "exact_mcnemar_two_sided_p_exploratory": exact_mcnemar_p(improved, worsened),
        "scores_a": a_scores,
        "scores_b": b_scores,
    }


def render_svg(result):
    a, b = result["configuration_a"], result["configuration_b"]
    title = "MBPP: paired decoding-length ablation (measured)"
    n = result["n"]
    header = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="880" height="340" viewBox="0 0 880 340">'
        '<rect width="880" height="340" rx="16" fill="#f8fafb"/>'
        f'<text x="30" y="43" font-family="Arial" font-size="22" fill="#193b49">{html.escape(title)}</text>'
        f'<text x="30" y="68" font-family="Arial" font-size="13" fill="#58717b">Same {n} MBPP validation tasks and Qwen checkpoint; NOT MCTS optimization</text>'
    )
    series = [
        (a, 170, "#98b7bc", "Baseline"),
        (b, 470, "#078a83", "Longer budget"),
    ]
    for record, xpos, fill, label in series:
        value = record["accuracy"]
        bar_height = max(2, int(value * 166))
        header += (
            f'<rect x="{xpos}" y="{264 - bar_height}" width="195" height="{bar_height}" rx="5" fill="{fill}"/>'
            f'<text x="{xpos + 97}" y="{255 - bar_height}" text-anchor="middle" font-size="17" '
            f'font-family="Arial" fill="#193b49">{100 * value:.2f}%</text>'
            f'<text x="{xpos + 97}" y="289" font-family="Arial" font-size="14" '
            f'text-anchor="middle" fill="#506973">{html.escape(label)} ({record["max_new_tokens"]} tokens)</text>'
        )
    return (header + '<line x1="100" y1="264" x2="800" y2="264" stroke="#8fa4ad"/>'
            '<text x="30" y="321" font-family="Arial" font-size="12" fill="#667e88">'
            'Measured directly; n is small, no generalization or paper-equivalent performance claimed.</text></svg>')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--a-json", required=True)
    parser.add_argument("--a-csv", required=True)
    parser.add_argument("--b-json", required=True)
    parser.add_argument("--b-csv", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = compare(read_run(args.a_json, args.a_csv),
                     read_run(args.b_json, args.b_csv))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    out.with_suffix(".svg").write_text(render_svg(result), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
