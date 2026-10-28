#!/usr/bin/env python3
"""Reanalyse the authors' archived AFlow results without executing their code.

This is a provenance-backed RE-ANALYSIS of the authors' output, not a new
training or optimization run. The archive is read as tar members only.
"""
import argparse
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path

from tools.fetch_author_data import safe_members
from tools.plot_results import summarize, render_svg

ARCHIVE_ID = "1Sr5wjgKf3bN8OC7G6cO3ynzJqD4w6_Dv"
ARCHIVED = {
    "MBPP": "results/MBPP/graphs/results.json",
    "HumanEval": "results/HumanEval/graphs/results.json",
    "GSM8K": "results/GSM8K/graphs/results.json",
    "MATH": "results/MATH/graphs/results.json",
    "DROP": "results/DROP/graphs/results.json",
    "HotpotQA": "results/HotpotQA/graphs/results_hotpotqa.json",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report", default="experiments/author_results_manifest.json"
    )
    args = parser.parse_args()
    import gdown

    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "author_results.tar.gz"
        url = gdown.download(id=ARCHIVE_ID, output=str(archive), quiet=False)
        if not url or not tarfile.is_tarfile(archive):
            raise RuntimeError("Published author results archive unavailable")
        sha256 = hashlib.sha256(archive.read_bytes()).hexdigest()
        evaluations = {}
        with tarfile.open(archive, "r:gz") as tf:
            members = safe_members(tf)
            files = [m for m in members if m.isfile()]
            total_size = sum(m.size for m in files)
            if total_size > 3_000_000_000 or len(files) > 100_000:
                raise ValueError("Archive exceeds safety bounds")
            file_names = {m.name for m in files}
            for name, path in ARCHIVED.items():
                if path not in file_names:
                    evaluations[name] = {"error": "Expected results file missing"}
                    continue
                raw = tf.extractfile(path).read()
                try:
                    records = json.loads(raw)
                    if not isinstance(records, list):
                        raise ValueError("Expected JSON list of round scores")
                    rounds = summarize(records)
                    report = {
                        "source_path": path,
                        "source_file_sha256": hashlib.sha256(raw).hexdigest(),
                        "records": len(records),
                        "rounds": [
                            {"round": round_id, "mean_validation": mean, "n": n}
                            for round_id, mean, n in rounds
                        ],
                        "first_round_score": rounds[0][1],
                        "last_round_score": rounds[-1][1],
                        "best_validation_score": max(x[1] for x in rounds),
                        "best_validation_round": max(rounds, key=lambda x: x[1])[0],
                        "not_new_measurements": True,
                    }
                    evaluations[name] = report
                    out = Path("experiments/author-published")
                    out.mkdir(parents=True, exist_ok=True)
                    (out / f"{name}_round_scores.json").write_text(
                        json.dumps(report, indent=2), encoding="utf-8"
                    )
                    (out / f"{name}_validation.svg").write_text(
                        render_svg(rounds, f"{name}: archived author validation (NOT new experiment)"),
                        encoding="utf-8"
                    )
                except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                    evaluations[name] = {"error": f"{type(exc).__name__}: {exc}"}
        report = {
            "kind": "author_supplied_results_not_new_measurements",
            "google_drive_id": ARCHIVE_ID,
            "sha256": sha256,
            "compressed_bytes": archive.stat().st_size,
            "uncompressed_bytes": total_size,
            "file_count": len(files),
            "example_files": sorted(file_names)[:25],
            "by_dataset": evaluations,
        }
        target = Path(args.report)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("AUTHOR_TRAJECTORIES_SUMMARY=" + json.dumps({
            name: {
                "rounds": len(value.get("rounds", [])),
                "first": value.get("first_round_score"),
                "best": value.get("best_validation_score"),
                "last": value.get("last_round_score"),
                "error": value.get("error"),
            } for name, value in evaluations.items()
        }, ensure_ascii=False))
        print("Author archive SHA256:", sha256)
        if not evaluations.get("MBPP", {}).get("rounds"):
            raise RuntimeError("No parseable MBPP optimization rounds in author archive")


if __name__ == "__main__":
    main()
