"""Paired-dataset guard and exact McNemar arithmetic."""
import unittest

from tools.compare_mbpp_baselines import compare, exact_mcnemar_p, render_svg


def fixture(scores, limit):
    meta = {"dataset_sha256": "a", "model": "QwenTest", "model_sha": "b",
            "evaluated_examples": len(scores), "max_new_tokens": limit,
            "accuracy": sum(scores) / len(scores), "total_generated_tokens": 100}
    rows = [{"inputs": f"q{i}", "score": str(x)} for i, x in enumerate(scores)]
    return meta, rows, scores


class PairwiseAnalysisTests(unittest.TestCase):
    def test_one_improvement(self):
        result = compare(fixture([0, 1, 0], 160), fixture([1, 1, 0], 320))
        self.assertEqual(result["improved_tasks"], 1)
        self.assertEqual(result["worsened_tasks"], 0)
        self.assertAlmostEqual(result["delta_accuracy_percentage_points"], 100 / 3)
        self.assertEqual(result["exact_mcnemar_two_sided_p_exploratory"], 1.0)
        self.assertIn("<svg", render_svg(result))

    def test_refuse_unpaired_tasks(self):
        a, b = fixture([0, 1], 160), fixture([1, 1], 320)
        b[1][0]["inputs"] = "different task"
        with self.assertRaisesRegex(ValueError, "Prompt order"):
            compare(a, b)

    def test_exact_p_value(self):
        self.assertEqual(exact_mcnemar_p(0, 0), 1.0)
        self.assertAlmostEqual(exact_mcnemar_p(5, 0), 0.0625)


if __name__ == "__main__":
    unittest.main()
