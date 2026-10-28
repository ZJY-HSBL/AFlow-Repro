#!/usr/bin/env python3
"""Acquire the authors' published optimization trajectories and summarize provenance.

This is a re-analysis of author-supplied results, NOT a newly run optimization.
"""
import argparse
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path

from tools.fetch_author_data import safe_members

ARCHIVE_ID = "1Sr5wjgKf3bN8OC7G6cO3ynzJqD4w6_Dv"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="experiments/author_results_manifest.json")
    args = parser.parse_args()
    import gdown

    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "author_results.tar.gz"
        url = gdown.download(id=ARCHIVE_ID, output=str(archive), quiet=False)
        if not url or not tarfile.is_tarfile(archive):
            raise RuntimeError("Published author results archive unavailable")
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        with tarfile.open(archive, "r:gz") as tf:
            members = safe_members(tf)
            files = [m for m in members if m.isfile()]
            size = sum(m.size for m in files)
            if size > 3_000_000_000 or len(files) > 100_000:
                raise ValueError("Archive too large to inspect safely")
            names = [m.name for m in files]
        report = {
            "kind": "author_supplied_results_not_new_measurements",
            "google_drive_id": ARCHIVE_ID,
            "sha256": digest,
            "compressed_bytes": archive.stat().st_size,
            "uncompressed_bytes": size,
            "file_count": len(files),
            "file_examples_first_100": names[:100],
            "results_like_files": [n for n in names if n.endswith("results.json")][:100],
        }
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
