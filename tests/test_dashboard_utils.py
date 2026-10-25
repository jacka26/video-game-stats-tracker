import unittest

from dashboard_utils import calculate_metrics, filter_matches


class TestDashboardUtils(unittest.TestCase):

    def setUp(self):
        self.matches = [
            {"Result": "Win", "Kills": 10, "Deaths": 0},
            {"Result": "Loss", "Kills": 5, "Deaths": 5},
            {"Result": "Win", "Kills": 8, "Deaths": 2}
        ]

    def test_filter_wins(self):
        result = filter_matches(self.matches, ["Win"])
        self.assertEqual(len(result), 2)

    def test_filter_losses(self):
        result = filter_matches(self.matches, ["Loss"])
        self.assertEqual(len(result), 1)

    def test_filter_all(self):
        result = filter_matches(
            self.matches, ["Win", "Loss"]
        )
        self.assertEqual(len(result), 3)

    def test_filter_empty(self):
        result = filter_matches(self.matches, [])
        self.assertEqual(result, [])

    def test_total_matches(self):
        metrics = calculate_metrics(self.matches)
        self.assertEqual(metrics["matches"], 3)

    def test_total_kills(self):
        metrics = calculate_metrics(self.matches)
        self.assertEqual(metrics["kills"], 23)

    def test_win_rate(self):
        metrics = calculate_metrics(self.matches)
        self.assertAlmostEqual(
            metrics["win_rate"], 66.6667, places=3
        )

    def test_zero_deaths(self):
        matches = [
            {"Result": "Win", "Kills": 10, "Deaths": 0}
        ]
        metrics = calculate_metrics(matches)
        self.assertIsNone(metrics["kd_ratio"])

    def test_no_matches(self):
        metrics = calculate_metrics([])
        self.assertEqual(metrics["matches"], 0)
        self.assertEqual(metrics["win_rate"], 0)
        self.assertIsNone(metrics["kd_ratio"])


if __name__ == "__main__":
    unittest.main()
