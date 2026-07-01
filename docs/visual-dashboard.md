# Visual Dashboard

The project includes a self-contained interactive HTML dashboard for team comparison, player search, player ratings, predictions, and validation.

Default output:

```text
site/index.html
```

Open this file directly in a browser. No server or frontend build step is required.

## Generate The Dashboard

```bash
make sample-dashboard
```

Or run the CLI directly:

```bash
PYTHONPATH=src python3 -m fifa_analysis.cli dashboard \
  --overall-ratings reports/player_overall_ratings.csv \
  --game-ratings reports/player_game_ratings.csv \
  --advanced-metrics reports/player_advanced_metrics.csv \
  --team-stats data/sample/team_match_stats_sample.csv \
  --prediction reports/match_prediction.json \
  --validation reports/rating_validation.json \
  --backtest reports/backtest.json \
  --output site/index.html
```

## Dashboard Sections

The dashboard includes:

- Team A and Team B selectors for comparing any teams loaded in the dataset.
- Team profile cards with xG, shots, defensive allowance, roster size, and top rated player.
- Full roster tables for both selected teams.
- Searchable player database across every loaded player and team.
- Role filters for narrowing ratings by tactical profile.
- Player A and Player B selectors for side-by-side player comparison.
- KPI cards for loaded players, teams, player-games, top overall rating, and best game rating.
- Match prediction panel with expected goals, win/draw/loss probabilities, top scorelines, confidence, and model reasons.
- Advanced player metrics table for attack, progression, security, disruption, two-way value, usage, and xG efficiency.
- Rating validation cards with MAE, correlation, and within-half-point rate.
- Backtest cards with exact-score top-3 rate, outcome accuracy, log loss, and calibration buckets.
- Overall player leaderboard.
- Best single-game performance table.

## Design Rules

- The dashboard is generated from real CSV/JSON outputs.
- It does not invent missing player stats.
- The committed sample dashboard uses synthetic `Demo ...` player names and must not be interpreted as current World Cup roster truth.
- It escapes dynamic values before embedding and rendering.
- It is responsive for desktop and mobile widths.
- It uses inline CSS and vanilla JavaScript, so it works offline without a frontend build step.
