.PHONY: test sample-metrics sample-team sample-predict sample-evaluate sample-ingest sample-match sample-impact sample-report sample-backtest verify

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

verify: test sample-metrics sample-team sample-predict sample-evaluate sample-ingest sample-match sample-impact sample-report sample-backtest
