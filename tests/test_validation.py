import unittest

from fifa_analysis.features import read_player_match_stats
from fifa_analysis.ratings import rate_player_game
from fifa_analysis.validation import compare_external_ratings, rating_coverage, read_external_ratings


class ValidationTest(unittest.TestCase):
    def test_compare_external_ratings_returns_metrics(self):
        stats = read_player_match_stats("data/sample/player_match_stats_sample.csv")
        generated = [rate_player_game(row) for row in stats]
        external = read_external_ratings("data/sample/external_ratings_sample.csv")

        result = compare_external_ratings(generated, external)

        self.assertEqual(result["sample_size"], 10)
        self.assertIn("mae", result)
        self.assertIn("correlation", result)

    def test_rating_coverage_counts_players_matches_and_confidence(self):
        stats = read_player_match_stats("data/sample/player_match_stats_sample.csv")
        generated = [rate_player_game(row) for row in stats]

        result = rating_coverage(generated)

        self.assertGreater(result["rated_player_games"], 0)
        self.assertGreater(result["players"], 0)
        self.assertTrue(result["confidence"])


if __name__ == "__main__":
    unittest.main()

