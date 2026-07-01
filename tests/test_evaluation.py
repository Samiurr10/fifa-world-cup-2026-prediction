import unittest

from fifa_analysis.connectors import read_match_records
from fifa_analysis.evaluation import backtest_predictions
from fifa_analysis.features import read_team_match_stats


class EvaluationTest(unittest.TestCase):
    def test_backtest_predictions_returns_accuracy_metrics(self):
        matches = read_match_records("data/sample/matches_sample.csv")
        team_rows = read_team_match_stats("data/sample/team_match_stats_sample.csv")

        result = backtest_predictions(matches, team_rows)

        self.assertEqual(result["matches"], 3)
        self.assertIn("exact_score_top3_rate", result)
        self.assertIn("log_loss", result)
        self.assertTrue(result["calibration"])


if __name__ == "__main__":
    unittest.main()

