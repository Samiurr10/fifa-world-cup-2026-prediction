import unittest

from fifa_analysis.metrics import player_metrics, score_contributions, team_summary


def event(event_type, player, team="Argentina", position="Center Midfield", **payload):
    return {
        "type": {"name": event_type},
        "player": {"name": player},
        "team": {"name": team},
        "position": {"name": position},
        **payload,
    }


class PlayerMetricsTest(unittest.TestCase):
    def test_player_metrics_count_progressive_carries_and_interceptions(self):
        events = [
            event(
                "Carry",
                "Alex Mid",
                location=[42, 38],
                carry={"end_location": [58, 41]},
            ),
            event("Interception", "Alex Mid"),
            event(
                "Pass",
                "Alex Mid",
                location=[50, 35],
                **{"pass": {"end_location": [68, 32], "shot_assist": True}},
            ),
        ]

        rows = player_metrics(events)

        self.assertEqual(rows[0]["progressive_carries"], 1)
        self.assertEqual(rows[0]["interceptions"], 1)
        self.assertEqual(rows[0]["progressive_passes"], 1)
        self.assertEqual(rows[0]["chance_creation"], 1)

    def test_score_contributions_uses_role_weights(self):
        rows = player_metrics(
            [
                event("Interception", "Defender", position="Center Back"),
                event("Interception", "Defender", position="Center Back"),
                event("Shot", "Forward", position="Center Forward", shot={"statsbomb_xg": 0.5}),
            ]
        )

        scored = score_contributions(rows)

        self.assertGreater(scored[0]["contribution_score"], 0)
        self.assertEqual({row["role_group"] for row in scored}, {"center_back", "forward"})

    def test_team_summary_aggregates_player_rows(self):
        rows = score_contributions(
            player_metrics(
                [
                    event(
                        "Shot",
                        "Forward",
                        shot={"statsbomb_xg": 0.2, "outcome": {"name": "Goal"}},
                    ),
                    event(
                        "Pass",
                        "Creator",
                        **{"pass": {"end_location": [90, 20], "goal_assist": True}},
                    ),
                ]
            )
        )

        summary = team_summary(rows)

        self.assertEqual(summary[0]["team"], "Argentina")
        self.assertEqual(summary[0]["players"], 2)
        self.assertEqual(summary[0]["goal_contributions"], 2)


if __name__ == "__main__":
    unittest.main()

