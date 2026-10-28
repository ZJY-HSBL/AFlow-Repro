"""Byte-level regression test against the frozen author source tree.

Every upstream text blob must retain exactly its original content; additional
files are allowed outside that list.
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class UpstreamHashTest(unittest.TestCase):
    def test_all_frozen_upstream_files_remain_unchanged(self):
        manifest = json.loads((ROOT / "docs" / "UPSTREAM_BLOBS.json").read_text("utf-8"))
        original = manifest["verified_files"]
        self.assertEqual(len(original), 102)
        for spec in original:
            with self.subTest(path=spec["path"]):
                content = (ROOT / spec["path"]).read_bytes()
                self.assertEqual(len(content), spec["size"])
                h = hashlib.sha1(
                    f"blob {len(content)}\0".encode("ascii") + content
                ).hexdigest()
                self.assertEqual(h, spec["git_blob_sha1"])


if __name__ == "__main__":
    unittest.main()
