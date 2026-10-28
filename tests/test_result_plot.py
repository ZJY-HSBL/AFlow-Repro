"""Tests use synthetic data only as unit fixtures; never publish as measurements."""
import unittest
from tools.plot_results import render_svg, summarize


class ResultPlotTests(unittest.TestCase):
    def test_rejects_missing_data(self):
        with self.assertRaises(ValueError):
            summarize([])

    def test_rejects_invalid_scores(self):
        with self.assertRaises(ValueError):
            summarize([{"round": 1, "score": 1.5}])

    def test_aggregates_multiple_observations_per_round(self):
        data = [{"round": 1, "score": 0.4}, {"round": 1, "score": 0.8},
                {"round": 2, "score": 0.7}]
        rows = summarize(data)
        self.assertAlmostEqual(rows[0][1], 0.6)
        self.assertEqual(rows[0][2], 2)
        svg = render_svg(rows, "Measured <scores>")
        self.assertIn("<svg", svg)
        self.assertIn("Measured &lt;scores&gt;", svg)


if __name__ == "__main__":
    unittest.main()
