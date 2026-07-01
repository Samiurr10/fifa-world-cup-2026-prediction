import unittest

from fifa_analysis.features import read_player_match_stats, read_team_match_stats
from fifa_analysis.predictors import (
    outcome_from_scorelines,
    predict_match,
    rank_player_impact,
    scoreline_distribution,
)


class PredictorTest(unittest.TestCase):
    def test_scoreline_distribution_returns_probabilities(self):
        scorelines = scoreline_distribution(1.7, 1.1, max_goals=6)
        outcomes = outcome_from_scorelines(scorelines)

        self.assertEqual(scorelines[0]["score"].count("-"), 1)
        self.assertAlmostEqual(outcomes["home_win"] + outcomes["draw"] + outcomes["away_win"], 1.0)

    def test_predict_match_returns_scorelines_and_reasons(self):
        team_rows = read_team_match_stats("data/sample/team_match_stats_sample.csv")
        prediction = predict_match("Argentina", "France", team_rows)

        self.assertEqual(prediction.home_team, "Argentina")
        self.assertEqual(len(prediction.top_scorelines), 5)
        self.assertIn(prediction.confidence, {"low", "medium", "high"})
        self.assertTrue(prediction.reasons)

    def test_rank_player_impact_is_role_aware(self):
        team_rows = read_team_match_stats("data/sample/team_match_stats_sample.csv")
        player_rows = read_player_match_stats("data/sample/player_match_stats_sample.csv")
        impacts = rank_player_impact("France", "Argentina", player_rows, team_rows, top_n=3)

        self.assertEqual(impacts[0].team, "France")
        self.assertGreater(impacts[0].impact_score, 0)
        self.assertTrue(impacts[0].reasons)


if __name__ == "__main__":
    unittest.main()

