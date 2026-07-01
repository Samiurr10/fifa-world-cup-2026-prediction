import unittest

from fifa_analysis.connectors import load_json
from fifa_analysis.statsbomb import lineup_player_minutes, statsbomb_events_to_player_stats


class StatsBombNormalizationTest(unittest.TestCase):
    def test_lineup_player_minutes_extracts_position_and_minutes(self):
        lineups = load_json("data/sample/statsbomb_lineups_sample.json")
        players = lineup_player_minutes(lineups)

        self.assertEqual(players["Lionel Messi"]["minutes"], 82.0)
        self.assertEqual(players["Kylian Mbappe"]["role_group"], "winger")

    def test_statsbomb_events_to_player_stats_merges_events_and_lineups(self):
        events = load_json("data/sample/events_sample.json")
        lineups = load_json("data/sample/statsbomb_lineups_sample.json")
        rows = statsbomb_events_to_player_stats(
            events,
            match_id="SAMPLE-1",
            home_team="Argentina",
            away_team="France",
            lineups=lineups,
        )
        messi = next(row for row in rows if row.player == "Lionel Messi")
        griezmann = next(row for row in rows if row.player == "Antoine Griezmann")

        self.assertEqual(messi.minutes, 82.0)
        self.assertEqual(messi.opponent, "France")
        self.assertEqual(griezmann.team, "France")
        self.assertGreaterEqual(len(rows), 7)


if __name__ == "__main__":
    unittest.main()

