import tempfile
import unittest
from pathlib import Path

from fifa_analysis.connectors import read_match_records
from fifa_analysis.database import (
    connect,
    fetch_player_stats,
    init_db,
    table_count,
    upsert_game_ratings,
    upsert_matches,
    upsert_overall_ratings,
    upsert_player_stats,
)
from fifa_analysis.features import read_player_match_stats
from fifa_analysis.ratings import build_overall_ratings, rate_player_game


class DatabaseTest(unittest.TestCase):
    def test_database_stores_stats_and_ratings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "ratings.sqlite"
            init_db(db_path)
            with connect(db_path) as conn:
                matches = read_match_records("data/sample/matches_sample.csv")
                stats = read_player_match_stats("data/sample/player_match_stats_sample.csv")
                self.assertEqual(upsert_matches(conn, matches), 3)
                self.assertEqual(upsert_player_stats(conn, stats), len(stats))
                stored_stats = fetch_player_stats(conn)
                ratings = [rate_player_game(row) for row in stored_stats]
                overall = build_overall_ratings(ratings)
                upsert_game_ratings(conn, ratings)
                upsert_overall_ratings(conn, overall)

                self.assertEqual(table_count(conn, "player_game_stats"), len(stats))
                self.assertEqual(table_count(conn, "player_game_ratings"), len(stats))
                self.assertGreater(table_count(conn, "player_overall_ratings"), 0)


if __name__ == "__main__":
    unittest.main()

