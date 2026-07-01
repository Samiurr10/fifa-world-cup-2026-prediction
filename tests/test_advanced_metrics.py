import json
import unittest

from fifa_analysis.advanced_metrics import calculate_advanced_metrics
from fifa_analysis.features import read_player_match_stats


class AdvancedMetricsTest(unittest.TestCase):
    def test_advanced_metrics_are_bounded_and_role_aware(self):
        stats = read_player_match_stats("data/sample/player_match_stats_sample.csv")
        winger = next(row for row in stats if row.player == "Demo Winger 11")

        metrics = calculate_advanced_metrics(winger)

        self.assertEqual(metrics.role_group, "winger")
        self.assertGreaterEqual(metrics.role_fit_score, 0)
        self.assertLessEqual(metrics.role_fit_score, 10)
        self.assertGreater(metrics.progression_value, 0)
        self.assertIn("progressive_carries", json.loads(metrics.per90_summary_json))


if __name__ == "__main__":
    unittest.main()
