# FIFA World Cup 2026 Prediction And Player Impact Engine

Free-data-first football intelligence system for predicting exact scorelines, win/draw/loss probabilities, and role-aware player impact for FIFA World Cup 2026 matches.

This is not a generic chatbot predictor. The project is a stats engine: data is normalized, features are computed, scorelines are modeled, and AI-style reports only explain computed facts.

## What It Produces

- Expected goals for both teams.
- Top likely exact scorelines.
- Win/draw/loss probabilities.
- Confidence tier based on free-data coverage.
- Role-aware player impact rankings.
- Per-game player performance ratings.
- Overall tournament player ratings.
- SQLite database for matches, players, player-game stats, ratings, and validation.
- Static visual dashboard for ratings, player trends, predictions, validation, and backtests.
- Grounded match reports that cite model inputs and uncertainty.

## Data Sources

Primary free sources:

- [StatsBomb Open Data](https://github.com/statsbomb/open-data): event-level football data with competitions, matches, events, lineups, and selected 360 files.
- [openfootball/worldcup.json](https://github.com/openfootball/worldcup.json): public-domain World Cup JSON data, including a 2026 folder.
- [rezarahiminia/worldcup2026](https://github.com/rezarahiminia/worldcup2026): no-key 2026 World Cup API candidate with matches, teams, groups, standings, scores, and stadiums.
- [football-data.org](https://www.football-data.org/documentation/api): backup fixture/result API; requires an API token.

Kaggle datasets can be added as local CSV inputs after checking columns and license terms.

## Architecture

```text
free data sources
  -> connectors.py normalize source payloads
  -> schemas.py shared match/team/player records
  -> features.py team form, opponent weakness, player role form
  -> predictors.py xG, scorelines, outcome probabilities, player impact
  -> reports.py grounded match/player explanation
  -> database.py stores player stats, game ratings, overall ratings, validation
  -> visuals.py renders clean HTML/SVG dashboards
  -> cli.py repeatable command-line workflows
```

## Quick Verification

```bash
make verify
```

This runs unit tests and generates:

- `reports/player_metrics.csv`
- `reports/team_summary.csv`
- `reports/matches.csv`
- `reports/match_prediction.json`
- `reports/player_impact.csv`
- `reports/player_game_ratings.csv`
- `reports/player_overall_ratings.csv`
- `reports/player_advanced_metrics.csv`
- `reports/rating_validation.json`
- `reports/rating_coverage.json`
- `reports/match_report.md`
- `reports/backtest.json`
- `site/index.html`

## Main Commands

Predict Argentina vs France from sample team stats:

```bash
PYTHONPATH=src python3 -m fifa_analysis.cli predict-match \
  --home Argentina \
  --away France \
  --team-stats data/sample/team_match_stats_sample.csv \
  --output reports/match_prediction.json
```

Rank France player impact against Argentina:

```bash
PYTHONPATH=src python3 -m fifa_analysis.cli player-impact \
  --team France \
  --opponent Argentina \
  --team-stats data/sample/team_match_stats_sample.csv \
  --player-stats data/sample/player_match_stats_sample.csv \
  --output reports/player_impact.csv
```

Generate a grounded report:

```bash
PYTHONPATH=src python3 -m fifa_analysis.cli match-report \
  --home Argentina \
  --away France \
  --team-stats data/sample/team_match_stats_sample.csv \
  --player-stats data/sample/player_match_stats_sample.csv \
  --output reports/match_report.md
```

Backtest scoreline and outcome predictions:

```bash
PYTHONPATH=src python3 -m fifa_analysis.cli backtest \
  --matches data/sample/matches_sample.csv \
  --team-stats data/sample/team_match_stats_sample.csv \
  --output reports/backtest.json
```

Build the SQLite player-rating database:

```bash
make sample-ratings
```

This creates `data/db/sample_worldcup_ratings.sqlite`, loads sample player-game stats, computes game ratings, computes overall ratings, validates against sample external ratings, and exports CSV/JSON reports.

Generate the visual dashboard:

```bash
make sample-dashboard
```

Then open:

```text
site/index.html
```

Normalize an openfootball-style JSON file:

```bash
PYTHONPATH=src python3 -m fifa_analysis.cli ingest-openfootball \
  --input data/sample/openfootball_sample.json \
  --output reports/matches.csv
```

## Model Design

The v1 model is transparent and auditable:

- Team expected goals are estimated from recent weighted xG, goals, shots, goals conceded, xG conceded, shots allowed, form, and host advantage.
- Exact scorelines use a Poisson distribution over each team’s expected goals.
- Win/draw/loss probabilities are summed from the scoreline distribution.
- Player impact combines role-specific form, contribution score, minutes adjustment, and opponent matchup weakness.
- Confidence is reduced when free-data coverage is sparse.
- Backtesting tracks exact-score top-3 hit rate, outcome accuracy, Brier score, log loss, and calibration buckets.
- Player ratings are role-aware, stored per game, aggregated overall, and validated against external ratings when available.
- Advanced role-fit metrics track attacking involvement, progression, ball security, defensive disruption, goalkeeping value, two-way value, usage, and xG efficiency.
- Visual dashboards are generated from the real report outputs and include rating trends, player component charts, advanced metric tables, prediction bars, validation metrics, and leaderboards.

## Player Rating Database

The rating database stores:

- players
- matches
- player-game stats
- per-game ratings
- overall ratings
- validation summaries

See [docs/database.md](docs/database.md) and [docs/player-ratings.md](docs/player-ratings.md).

## Visual Dashboard

The dashboard is a self-contained HTML file with inline CSS/SVG visuals. It can be opened directly or published later with GitHub Pages.

See [docs/visual-dashboard.md](docs/visual-dashboard.md).

## Accuracy Notes

Free data will not always include confirmed lineups, injuries, current player-level stats, or external player ratings. The system handles that by lowering confidence, exposing coverage reports, and validating only against rating sources that are actually provided. Paid APIs or Kaggle exports can be added later behind the same normalized schemas.
