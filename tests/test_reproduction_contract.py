"""Assertions for source layout and baseline experiment configuration."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourceContractTests(unittest.TestCase):
    def test_official_six_benchmarks_are_present(self):
        for name in ["humaneval", "mbpp", "gsm8k", "math", "hotpotqa", "drop"]:
            with self.subTest(benchmark=name):
                self.assertTrue((ROOT / "benchmarks" / f"{name}.py").is_file())

    def test_initial_graphs_for_all_six_tasks(self):
        for name in ["HumanEval", "MBPP", "GSM8K", "MATH", "HotpotQA", "DROP"]:
            graph = ROOT / "workspace" / name / "workflows" / "round_1" / "graph.py"
            with self.subTest(name=name):
                self.assertTrue(graph.is_file())
                ast.parse(graph.read_text(encoding="utf-8"))

    def test_original_algorithm_files_are_present(self):
        paths = (
            "scripts/optimizer.py",
            "scripts/optimizer_utils/data_utils.py",
            "scripts/optimizer_utils/graph_utils.py",
            "scripts/optimizer_utils/convergence_utils.py",
            "scripts/optimizer_utils/experience_utils.py",
            "scripts/evaluator.py",
            "run.py",
            "run_baseline.py",
        )
        for name in paths:
            with self.subTest(path=name):
                self.assertTrue((ROOT / name).is_file())

    def test_official_example_not_real_credentials(self):
        example = (ROOT / "config/config2.example.yaml").read_text("utf-8")
        self.assertIn("<your api key>", example)
        self.assertFalse((ROOT / "config/config2.yaml").exists())


if __name__ == "__main__":
    unittest.main()
