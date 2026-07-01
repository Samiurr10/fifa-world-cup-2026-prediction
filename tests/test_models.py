import tempfile
import unittest
from pathlib import Path

from fifa_analysis.models import baseline_match_prediction, evaluate_baseline


class ModelBaselineTest(unittest.TestCase):
    def test_baseline_prediction_probabilities_sum_to_one(self):
        prediction = baseline_match_prediction(
            home_attack=1.8,
            home_defense=1.1,
            away_attack=1.2,
            away_defense=0.9,
        )

        self.assertGreater(prediction.home_win, prediction.away_win)
        self.assertEqual(round(prediction.home_win + prediction.draw + prediction.away_win, 3), 1.0)

    def test_evaluate_baseline_reads_feature_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature_file = Path(tmpdir) / "matches.csv"
            feature_file.write_text(
                "home_attack,home_defense,away_attack,away_defense,home_advantage,result\n"
                "1.8,1.1,1.2,0.9,0.18,H\n"
                "1.0,0.8,1.0,0.8,0.00,D\n",
                encoding="utf-8",
            )

            result = evaluate_baseline(feature_file)

        self.assertEqual(result["rows"], 2)
        self.assertGreaterEqual(result["accuracy"], 0)
        self.assertLessEqual(result["accuracy"], 1)
        self.assertGreaterEqual(result["brier_score"], 0)


if __name__ == "__main__":
    unittest.main()

