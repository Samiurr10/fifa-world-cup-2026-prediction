.PHONY: test sample-metrics sample-team sample-predict sample-evaluate sample-ingest sample-match sample-impact sample-report sample-backtest sample-ratings sample-statsbomb sample-dashboard official-dashboard api-football-ingest verify

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py'

sample-metrics:
	PYTHONPATH=src python3 -m fifa_analysis.cli metrics --events data/sample/events_sample.json --output reports/player_metrics.csv

sample-team:
	PYTHONPATH=src python3 -m fifa_analysis.cli team-summary --events data/sample/events_sample.json --output reports/team_summary.csv

sample-predict:
	PYTHONPATH=src python3 -m fifa_analysis.cli predict --home-attack 1.8 --home-defense 1.1 --away-attack 1.2 --away-defense 0.9

sample-evaluate:
	PYTHONPATH=src python3 -m fifa_analysis.cli evaluate --matches data/sample/match_features_sample.csv

sample-ingest:
	PYTHONPATH=src python3 -m fifa_analysis.cli ingest-openfootball --input data/sample/openfootball_sample.json --output reports/matches.csv

sample-match:
	PYTHONPATH=src python3 -m fifa_analysis.cli predict-match --home Argentina --away France --team-stats data/sample/team_match_stats_sample.csv --output reports/match_prediction.json

sample-impact:
	PYTHONPATH=src python3 -m fifa_analysis.cli player-impact --team France --opponent Argentina --team-stats data/sample/team_match_stats_sample.csv --player-stats data/sample/player_match_stats_sample.csv --output reports/player_impact.csv

sample-report:
	PYTHONPATH=src python3 -m fifa_analysis.cli match-report --home Argentina --away France --team-stats data/sample/team_match_stats_sample.csv --player-stats data/sample/player_match_stats_sample.csv --output reports/match_report.md

sample-backtest:
	PYTHONPATH=src python3 -m fifa_analysis.cli backtest --matches data/sample/matches_sample.csv --team-stats data/sample/team_match_stats_sample.csv --output reports/backtest.json

sample-ratings:
	rm -f data/db/sample_worldcup_ratings.sqlite
	PYTHONPATH=src python3 -m fifa_analysis.cli init-db --db data/db/sample_worldcup_ratings.sqlite
	PYTHONPATH=src python3 -m fifa_analysis.cli load-player-stats --db data/db/sample_worldcup_ratings.sqlite --player-stats data/sample/player_match_stats_sample.csv
	PYTHONPATH=src python3 -m fifa_analysis.cli rate-db --db data/db/sample_worldcup_ratings.sqlite
	PYTHONPATH=src python3 -m fifa_analysis.cli export-game-ratings --db data/db/sample_worldcup_ratings.sqlite --output reports/player_game_ratings.csv
	PYTHONPATH=src python3 -m fifa_analysis.cli export-overall-ratings --db data/db/sample_worldcup_ratings.sqlite --output reports/player_overall_ratings.csv
	PYTHONPATH=src python3 -m fifa_analysis.cli export-advanced-metrics --db data/db/sample_worldcup_ratings.sqlite --output reports/player_advanced_metrics.csv
	PYTHONPATH=src python3 -m fifa_analysis.cli validate-ratings --db data/db/sample_worldcup_ratings.sqlite --external-ratings data/sample/external_ratings_sample.csv --output reports/rating_validation.json --store
	PYTHONPATH=src python3 -m fifa_analysis.cli rating-coverage --db data/db/sample_worldcup_ratings.sqlite --output reports/rating_coverage.json

sample-statsbomb:
	PYTHONPATH=src python3 -m fifa_analysis.cli statsbomb-player-stats --events data/sample/events_sample.json --lineups data/sample/statsbomb_lineups_sample.json --match-id SAMPLE-1 --home Argentina --away France --output reports/statsbomb_player_stats.csv

sample-dashboard:
	PYTHONPATH=src python3 -m fifa_analysis.cli dashboard --overall-ratings reports/player_overall_ratings.csv --game-ratings reports/player_game_ratings.csv --advanced-metrics reports/player_advanced_metrics.csv --team-stats data/sample/team_match_stats_sample.csv --prediction reports/match_prediction.json --validation reports/rating_validation.json --backtest reports/backtest.json --output site/sample.html

official-dashboard:
	PYTHONPATH=src python3 -m fifa_analysis.cli dashboard --roster data/official/fifa_squads_2026.csv --output site/index.html

api-football-ingest:
	PYTHONPATH=src python3 -m fifa_analysis.cli ingest-api-football

verify: test sample-metrics sample-team sample-predict sample-evaluate sample-ingest sample-match sample-impact sample-report sample-backtest sample-statsbomb sample-ratings official-dashboard
