#!/usr/bin/env python3
"""Safely fetch and inspect the original AFlow author-provided data archive.

Download alone is NOT a scientific reproduction. Exit nonzero for unavailable or
malformed archives. Never run author model code during this step.
"""
import argparse
import hashlib
import json
import os
import tarfile
import tempfile
from pathlib import Path

AFLOW_DATA_ID = "1DNoegtZiUhWtvkd2xoIuElmIi4ah7k8e"
TARGET = Path("data/datasets")


def checksum(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_members(tf):
    names = []
    for member in tf.getmembers():
        p = Path(member.name)
        if p.is_absolute() or ".." in p.parts or not (member.isfile() or member.isdir()):
            raise ValueError(f"Unsafe tar member: {member.name!r}")
        if member.name.startswith("/"):
            raise ValueError("Absolute archive paths are prohibited")
        names.append(member)
    return names


def get_author_archive(archive):
    try:
        import gdown
    except ImportError as exc:
        raise RuntimeError("Install gdown (pip install gdown==5.2.0) first") from exc
    output = gdown.download(id=AFLOW_DATA_ID, output=str(archive), quiet=False)
    if not output or not archive.is_file() or not tarfile.is_tarfile(archive):
        raise RuntimeError("Official Google Drive archive unavailable or not a tar file")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="experiments/author_data_manifest.json")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "aflow_author_data.tar.gz"
        get_author_archive(archive)
        with tarfile.open(archive, "r:gz") as tf:
            members = safe_members(tf)
            size = sum(m.size for m in members if m.isfile())
            if size > 2_000_000_000 or len(members) > 200_000:
                raise ValueError("Archive exceeds preflight safety limits")
            TARGET.mkdir(parents=True, exist_ok=True)
            tf.extractall(path=TARGET, members=members)
        files = sorted(p.relative_to(TARGET).as_posix()
                       for p in TARGET.rglob("*") if p.is_file())
        report = {
            "source": "FoundationAgents/AFlow author dataset archive",
            "google_drive_id": AFLOW_DATA_ID,
            "archive_sha256": checksum(archive),
            "archive_size_bytes": archive.stat().st_size,
            "uncompressed_bytes": size,
            "files_count": len(files),
            "dataset_paths": files,
            "expected_validation_exists": (TARGET / "mbpp_validate.jsonl").exists(),
            "expected_test_exists": (TARGET / "mbpp_test.jsonl").exists(),
        }
        dest = Path(args.report)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        if not report["expected_validation_exists"]:
            raise RuntimeError("Official archive missing expected AFlow MBPP validation split")


if __name__ == "__main__":
    main()
