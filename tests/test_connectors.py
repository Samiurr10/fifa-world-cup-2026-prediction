import unittest

from fifa_analysis.connectors import (
    normalize_api_football_fixture_players,
    normalize_api_football_fixtures,
    normalize_api_football_squad,
    normalize_api_football_teams,
    normalize_openfootball_matches,
    normalize_worldcup2026_api,
)


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

    def test_normalize_api_football_core_payloads(self):
        teams = normalize_api_football_teams(
            {"response": [{"team": {"id": 1, "name": "Argentina", "code": "ARG", "national": True}}]}
        )
        self.assertEqual(teams[0]["team_id"], 1)
        self.assertEqual(teams[0]["team"], "Argentina")

        squad = normalize_api_football_squad(
            {
                "response": [
                    {
                        "team": {"id": 1, "name": "Argentina"},
                        "players": [
                            {"id": 10, "name": "Lionel Messi", "position": "Attacker", "number": 10}
                        ],
                    }
                ]
            }
        )
        self.assertEqual(squad[0]["player_name"], "Lionel Messi")
        self.assertEqual(squad[0]["role_group"], "forward")

        fixtures = normalize_api_football_fixtures(
            {
                "response": [
                    {
                        "fixture": {"id": 99, "date": "2026-06-11", "status": {"short": "FT"}},
                        "teams": {"home": {"name": "Argentina"}, "away": {"name": "France"}},
                        "goals": {"home": 2, "away": 1},
                        "league": {"round": "Group Stage"},
                    }
                ]
            }
        )
        self.assertEqual(fixtures[0].match_id, "99")
        self.assertEqual(fixtures[0].result, "H")

    def test_normalize_api_football_fixture_players_keeps_missing_advanced_fields_zero(self):
        rows = normalize_api_football_fixture_players(
            {
                "response": [
                    {
                        "team": {"name": "Argentina"},
                        "players": [
                            {
                                "player": {"id": 10, "name": "Lionel Messi"},
                                "statistics": [
                                    {
                                        "games": {"minutes": 90, "position": "Attacker", "rating": "8.3"},
                                        "shots": {"total": 4},
                                        "goals": {"total": 1, "assists": 1},
                                        "passes": {"key": 3, "accuracy": "88"},
                                        "tackles": {"total": 1, "interceptions": 0},
                                        "dribbles": {"success": 2},
                                    }
                                ],
                            }
                        ],
                    }
                ]
            },
            match_id="99",
            opponents_by_team={"Argentina": "France"},
        )

        self.assertEqual(rows[0].player, "Lionel Messi")
        self.assertEqual(rows[0].opponent, "France")
        self.assertEqual(rows[0].role_group, "forward")
        self.assertEqual(rows[0].xg, 0.0)
        self.assertEqual(rows[0].progressive_carries, 0.0)


if __name__ == "__main__":
    unittest.main()
