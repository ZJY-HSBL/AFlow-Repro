"""A disposable Docker-based evaluation wrapper for the *unchanged* AFlow MBPP scorer.

Generated code is never executed in the host Python process.
"""
import json
import subprocess

from benchmarks.mbpp import MBPPBenchmark
from scripts.utils.sanitize import sanitize

CONTAINER_RUNNER = r"""
import json
import sys
import math
import hashlib
import re
from typing import List, Dict, Tuple, Optional, Any

payload = json.load(sys.stdin)
scope = {
    "math": math, "hashlib": hashlib, "re": re,
    "List": List, "Dict": Dict, "Tuple": Tuple,
    "Optional": Optional, "Any": Any,
}
try:
    exec(payload["code"], scope)
    if payload["entry_point"] not in scope:
        raise ValueError("Target function is missing")
    exec(payload["test"], scope)
    check = scope["check"]
    outcome = check()
    print(json.dumps({"ok": True, "detail": "Reference tests passed"}))
except BaseException as exc:
    print(json.dumps({"ok": False, "detail": f"{type(exc).__name__}: {exc}"})[:4000])
"""


def docker_command():
    return [
        "docker", "run", "--rm", "-i",
        "--pull=never", "--network=none", "--read-only",
        "--cpus=1", "--memory=384m", "--memory-swap=384m",
        "--pids-limit=32", "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--user=65534:65534",
        "--tmpfs=/tmp:rw,noexec,nosuid,size=16m",
        "python:3.11-slim", "python", "-I", "-S", "-c", CONTAINER_RUNNER,
    ]


class SandboxedMBPPBenchmark(MBPPBenchmark):
    """Same AFlow MBPP solution checker, with the code execution isolated."""

    def check_solution(self, solution, test, entry_point):
        try:
            code = sanitize(code=solution, entrypoint=entry_point)
            payload = json.dumps({
                "code": code, "test": test, "entry_point": entry_point,
            })
            result = subprocess.run(
                docker_command(), input=payload, capture_output=True,
                text=True, timeout=25, check=False,
            )
            if result.returncode != 0:
                return self.FAIL, (result.stderr or result.stdout)[:600]
            verdict = json.loads(result.stdout.strip().splitlines()[-1])
            if verdict.get("ok") is True:
                return self.PASS, "The solution passed all test cases."
            return self.FAIL, str(verdict.get("detail", "Unknown sandbox error"))
        except subprocess.TimeoutExpired:
            return self.FAIL, "Sandbox exceeded 25-second wall-time limit"
        except (OSError, ValueError, IndexError, json.JSONDecodeError) as exc:
            return self.FAIL, f"Sandbox execution error: {type(exc).__name__}: {exc}"
