import unittest

from fifa_analysis.theanalyst import normalize_theanalyst_player_stats


class TheAnalystIngestionTest(unittest.TestCase):
    def test_normalize_theanalyst_player_stats_merges_sections(self):
        payload = {
            "lastUpdated": "2026-07-02 04:50:00.984280",
            "league": "FIFA World Cup",
            "attack": {
                "overall": [
                    {
                        "player_id": 14937,
                        "apps": 3,
                        "mins_played": 270,
                        "goals": 2,
                        "xg": 2.19,
                        "shots": 13,
                        "shots_on_target": 6,
                        "player": "Cristiano Ronaldo",
                        "age": 41.43,
                        "shirt_number": 7,
                        "squad_position": "Forward",
                        "squad_position_detailed": "Striker",
                        "player_uuid": "h17s3qts1dz1zqjw19jazzkl",
                        "team_uuid": "8gxg8f7p9299jbrz30u8bsc7g",
                        "contestantName": "Portugal",
                        "contestantCode": "POR",
                    }
                ]
            },
            "possession": {
                "chanceCreation": [
                    {
                        "player_uuid": "h17s3qts1dz1zqjw19jazzkl",
                        "team_uuid": "8gxg8f7p9299jbrz30u8bsc7g",
                        "player": "Cristiano Ronaldo",
                        "contestantName": "Portugal",
                        "assists": 0,
                        "xa": 0.118,
                        "chances_created": 0,
                    }
                ],
                "passing": [
                    {
                        "player_uuid": "h17s3qts1dz1zqjw19jazzkl",
                        "team_uuid": "8gxg8f7p9299jbrz30u8bsc7g",
                        "player": "Cristiano Ronaldo",
                        "contestantName": "Portugal",
                        "passes": 67,
                        "successful_passes": 54,
                        "pass_perc": 80.6,
                    }
                ],
            },
            "carries": {
                "overall": [
                    {
                        "player_uuid": "h17s3qts1dz1zqjw19jazzkl",
                        "team_uuid": "8gxg8f7p9299jbrz30u8bsc7g",
                        "player": "Cristiano Ronaldo",
                        "contestantName": "Portugal",
                        "carries": 11,
                        "progressive_carries": 5,
                    }
                ]
            },
            "defending": {
                "overall": [
                    {
                        "player_uuid": "h17s3qts1dz1zqjw19jazzkl",
                        "team_uuid": "8gxg8f7p9299jbrz30u8bsc7g",
                        "player": "Cristiano Ronaldo",
                        "contestantName": "Portugal",
                        "tackles": 1,
                        "interceptions": 1,
                        "recoveries": 5,
                    }
                ],
                "discipline": [],
            },
            "goalkeeping": {"overall": []},
        }

        rows = normalize_theanalyst_player_stats(payload, accessed_date="2026-07-03")

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["player"], "Cristiano Ronaldo")
        self.assertEqual(row["team"], "Portugal")
        self.assertEqual(row["wc_matches"], 3)
        self.assertEqual(row["wc_minutes"], 270)
        self.assertEqual(row["wc_goals"], 2)
        self.assertEqual(row["wc_xg"], 2.19)
        self.assertEqual(row["wc_shots"], 13)
        self.assertEqual(row["wc_carries"], 11)
        self.assertEqual(row["wc_progressive_carries"], 5)
        self.assertEqual(row["wc_interceptions"], 1)
        self.assertEqual(row["wc_tackles"], 1)
        self.assertEqual(row["last_updated"], "2026-07-02 04:50:00.984280")


if __name__ == "__main__":
    unittest.main()
