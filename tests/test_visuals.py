import tempfile
import unittest
from pathlib import Path

from fifa_analysis.visuals import dashboard_data, generate_dashboard, render_dashboard


class VisualDashboardTest(unittest.TestCase):
    def test_render_dashboard_contains_core_sections_and_escapes_values(self):
        data = dashboard_data(
            overall_rows=[
                {
                    "player": "Demo <Player>",
                    "team": "Argentina",
                    "role_group": "attacking_midfielder",
                    "matches": "1",
                    "minutes": "90",
                    "weighted_rating": "8.2",
                    "best_rating": "8.2",
                    "confidence": "high",
                }
            ],
            game_rows=[
                {
                    "player": "Demo <Player>",
                    "team": "Argentina",
                    "opponent": "France",
                    "role_group": "attacking_midfielder",
                    "rating": "8.2",
                    "minutes": "90",
                    "attacking_score": "0.7",
                    "possession_score": "0.6",
                    "defensive_score": "0.2",
                    "goalkeeping_score": "0.1",
                }
            ],
            advanced_rows=[
                {
                    "player": "Demo <Player>",
                    "team": "Argentina",
                    "opponent": "France",
                    "role_group": "attacking_midfielder",
                    "role_fit_score": "8.0",
                    "attacking_involvement": "8.2",
                    "progression_value": "7.1",
                    "ball_security": "6.9",
                    "defensive_disruption": "2.4",
                    "two_way_value": "5.0",
                    "usage_rate": "7.5",
                    "xg_efficiency": "5.4",
                }
            ],
            team_rows=[
                {
                    "team": "Argentina",
                    "opponent": "France",
                    "xg_for": "1.5",
                    "xg_against": "1.2",
                    "shots_for": "12",
                    "shots_against": "9",
                }
            ],
            prediction={
                "home_team": "Argentina",
                "away_team": "France",
                "expected_home_goals": 1.5,
                "expected_away_goals": 1.2,
                "home_win": 0.45,
                "draw": 0.25,
                "away_win": 0.30,
                "confidence": "high",
                "top_scorelines": [{"score": "1-1", "probability": 0.12}],
                "reasons": ["Reason"],
            },
            validation={"mae": 0.2, "correlation": 0.9, "within_half_point_rate": 0.8},
            backtest={"exact_score_top3_rate": 0.5, "outcome_accuracy": 0.6, "log_loss": 1.0},
        )
        markup = render_dashboard()

        self.assertIn("assets/dashboard.css", markup)
        self.assertIn("assets/dashboard.js", markup)
        self.assertIn("globalSearch", markup)
        self.assertIn("view-players", markup)
        self.assertIn("Predictions", markup)
        self.assertEqual(data["overall"][0]["player"], "Demo <Player>")
        self.assertNotIn("<Player>", markup)

    def test_generate_dashboard_writes_html_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "index.html"
            generate_dashboard(
                overall_ratings_path="reports/player_overall_ratings.csv",
                game_ratings_path="reports/player_game_ratings.csv",
                advanced_metrics_path="reports/player_advanced_metrics.csv",
                roster_path="data/official/fifa_squads_2026.csv",
                tournament_stats_path="data/official/world_cup_2026_player_stats.csv",
                team_stats_path="data/sample/team_match_stats_sample.csv",
                prediction_path="reports/match_prediction.json",
                validation_path="reports/rating_validation.json",
                backtest_path="reports/backtest.json",
                output_path=output,
            )

            self.assertTrue(output.exists())
            self.assertTrue((Path(tmpdir) / "index-assets" / "dashboard.css").exists())
            self.assertTrue((Path(tmpdir) / "index-assets" / "dashboard.js").exists())
            self.assertTrue((Path(tmpdir) / "index-assets" / "app-data.json").exists())
            self.assertIn("<!doctype html>", output.read_text(encoding="utf-8"))
            self.assertIn("tournamentStats", (Path(tmpdir) / "index-assets" / "app-data.json").read_text())


if __name__ == "__main__":
    unittest.main()
