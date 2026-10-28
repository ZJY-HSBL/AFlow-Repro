"""Offline regression tests for the unmodified AFlow research implementation.

No model API, dataset download, or execution of generated code is required.
"""
import json
import math
import tempfile
import unittest
from pathlib import Path

from scripts.optimizer_utils.convergence_utils import ConvergenceUtils
from scripts.optimizer_utils.data_utils import DataUtils
from scripts.optimizer_utils.experience_utils import ExperienceUtils
from scripts.optimizer_utils.graph_utils import GraphUtils


class ScoreSamplingTests(unittest.TestCase):
    def test_single_candidate(self):
        probabilities = DataUtils("unused")._compute_probabilities([60.0])
        self.assertEqual(probabilities.tolist(), [1.0])

    def test_equal_scores_are_uniform(self):
        probabilities = DataUtils("unused")._compute_probabilities([50.0] * 4)
        self.assertTrue(all(abs(p - 0.25) < 1e-12 for p in probabilities))

    def test_favors_higher_score_but_keeps_exploration(self):
        probabilities = DataUtils("unused")._compute_probabilities([90.0, 20.0, 10.0])
        self.assertGreater(probabilities[0], probabilities[1])
        self.assertGreater(probabilities[1], probabilities[2])
        self.assertTrue(all(p > 0 and math.isfinite(p) for p in probabilities))
        self.assertAlmostEqual(sum(probabilities), 1.0)

    def test_empty_scores_rejected(self):
        with self.assertRaises(ValueError):
            DataUtils("unused")._compute_probabilities([])

    def test_baseline_round_is_included_in_candidate_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workflows"
            workspace.mkdir()
            (workspace / "results.json").write_text(
                json.dumps([
                    {"round": 1, "score": 0.25},
                    {"round": 2, "score": 0.75},
                    {"round": 3, "score": 0.65},
                ]), encoding="utf-8"
            )
            candidates = DataUtils(tmp).get_top_rounds(sample=2)
            self.assertEqual([item["round"] for item in candidates], [1, 2])


class ExperienceTests(unittest.TestCase):
    def test_duplicate_modification_rejected_for_success_and_failure(self):
        experience = {
            1: {
                "score": 0.5,
                "success": {2: {"modification": "try_a", "score": 0.6}},
                "failure": {3: {"modification": "try_b", "score": 0.4}},
            }
        }
        manager = ExperienceUtils("unused")
        self.assertFalse(manager.check_modification(experience, "try_a", 1))
        self.assertFalse(manager.check_modification(experience, "try_b", 1))
        self.assertTrue(manager.check_modification(experience, "try_c", 1))

    def test_experience_score_improvement_is_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = ExperienceUtils(tmp)
            directory = Path(tmp) / "round_2"
            directory.mkdir()
            improvement = manager.create_experience_data(
                {"round": 1, "score": 0.5}, "change prompt"
            )
            manager.update_experience(str(directory), improvement, 0.6)
            saved = json.loads((directory / "experience.json").read_text())
            self.assertEqual(saved["father node"], 1)
            self.assertTrue(saved["succeed"])
            manager.update_experience(str(directory), improvement, 0.5)
            saved = json.loads((directory / "experience.json").read_text())
            self.assertFalse(saved["succeed"])


class WorkflowTests(unittest.TestCase):
    def test_extract_workflow_class(self):
        code = "import os\nclass Workflow:\n    async def __call__(self):\n        return 42\n"
        matches = GraphUtils("unused").extract_solve_graph(code)
        self.assertEqual(len(matches), 1)
        self.assertIn("return 42", matches[0])

    def test_operator_schema_loaded_from_upstream_template(self):
        description = GraphUtils("workspace/MBPP").load_operators_description(["Custom"])
        self.assertIn("Custom", description)

    def test_convergence_stable_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workflows"
            root.mkdir()
            (root / "results.json").write_text(
                json.dumps([{"round": i, "score": 0.7} for i in range(1, 9)]),
                encoding="utf-8",
            )
            converged, first, last = ConvergenceUtils(tmp).check_convergence(
                top_k=3, consecutive_rounds=5
            )
            self.assertTrue(converged)
            self.assertIsNotNone(first)
            self.assertGreaterEqual(last, first)


if __name__ == "__main__":
    unittest.main()
