import unittest

from fifa_analysis.features import read_player_match_stats
from fifa_analysis.ratings import build_overall_ratings, rate_player_game


class RatingEngineTest(unittest.TestCase):
    def test_rate_player_game_returns_bounded_role_aware_rating(self):
        player = read_player_match_stats("data/sample/player_match_stats_sample.csv")[0]
        rating = rate_player_game(player)

        self.assertGreaterEqual(rating.rating, 1.0)
        self.assertLessEqual(rating.rating, 10.0)
        self.assertEqual(rating.role_group, "attacking_midfielder")
        self.assertTrue(rating.reasons)

    def test_build_overall_ratings_weights_by_minutes(self):
        players = read_player_match_stats("data/sample/player_match_stats_sample.csv")
        ratings = [rate_player_game(row) for row in players]
        overall = build_overall_ratings(ratings)
        creator = next(row for row in overall if row.player == "Demo Creator 10")

        self.assertEqual(creator.matches, 5)
        self.assertGreater(creator.weighted_rating, 6.0)
        self.assertEqual(creator.confidence, "high")


if __name__ == "__main__":
    unittest.main()
