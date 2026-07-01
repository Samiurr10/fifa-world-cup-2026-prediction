import unittest

from fifa_analysis.connectors import normalize_openfootball_matches, normalize_worldcup2026_api


class ConnectorTest(unittest.TestCase):
    def test_normalize_openfootball_matches(self):
        matches = normalize_openfootball_matches(
            {
                "rounds": [
                    {
                        "name": "Group A",
                        "matches": [
                            {
                                "num": 1,
                                "date": "2026-06-11",
                                "team1": {"name": "Mexico"},
                                "team2": {"name": "South Africa"},
                                "score": {"ft": {"team1": 2, "team2": 1}},
                            }
                        ],
                    }
                ]
            }
        )

        self.assertEqual(matches[0].home_team, "Mexico")
        self.assertEqual(matches[0].away_team, "South Africa")
        self.assertEqual(matches[0].result, "H")

    def test_normalize_worldcup2026_api(self):
        matches = normalize_worldcup2026_api(
            {
                "games": [
                    {
                        "id": "1",
                        "home_team_name": "Argentina",
                        "away_team_name": "France",
                        "home_score": "0",
                        "away_score": "0",
                        "finished": "FALSE",
                        "group": "J",
                    }
                ]
            }
        )

        self.assertEqual(matches[0].home_team, "Argentina")
        self.assertEqual(matches[0].status, "scheduled")
        self.assertEqual(matches[0].group, "J")


if __name__ == "__main__":
    unittest.main()

