# Visual Dashboard

The project includes a self-contained HTML dashboard for player stats, ratings, predictions, and validation.

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
  --prediction reports/match_prediction.json \
  --validation reports/rating_validation.json \
  --backtest reports/backtest.json \
  --output site/index.html
```

## Dashboard Sections

The dashboard includes:

- KPI cards for rated players, player-games, top overall rating, and best game rating.
- Match prediction panel with expected goals, win/draw/loss probabilities, top scorelines, confidence, and model reasons.
- Player cards with rating trends and role-component radar charts.
- Player cards with role-fit and usage indicators.
- Role distribution chart.
- Advanced player metrics table for attack, progression, security, disruption, two-way value, usage, and xG efficiency.
- Rating validation cards with MAE, correlation, and within-half-point rate.
- Backtest cards with exact-score top-3 rate, outcome accuracy, log loss, and calibration buckets.
- Overall player leaderboard.
- Best single-game performance table.

## Design Rules

- The dashboard is generated from real CSV/JSON outputs.
- It does not invent missing player stats.
- It escapes dynamic values before rendering.
- It is responsive for desktop and mobile widths.
- It uses inline SVG/CSS, so it works offline.
