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
- Interactive visual dashboard for team comparison, searchable players, player ratings, predictions, validation, and backtests.
- Grounded match reports that cite model inputs and uncertainty.

## Data Sources

Primary free sources:

- [StatsBomb Open Data](https://github.com/statsbomb/open-data): event-level football data with competitions, matches, events, lineups, and selected 360 files.
- [openfootball/worldcup.json](https://github.com/openfootball/worldcup.json): public-domain World Cup JSON data, including a 2026 folder.
- [rezarahiminia/worldcup2026](https://github.com/rezarahiminia/worldcup2026): no-key 2026 World Cup API candidate with matches, teams, groups, standings, scores, and stadiums.
- [football-data.org](https://www.football-data.org/documentation/api): backup fixture/result API; requires an API token.
- FIFA official squad list PDF/CSV for the 48 World Cup squads and 1,248 players. Its `international_goals` value is a career national-team total, not a World Cup 2026 tournament total.
- Researched World Cup 2026 public player-stat pages from [FIFA](https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/statistics/player-statistics), [365Scores](https://www.365scores.com/football/league/fifa-world-cup-5930/stats), [FotMob](https://www.fotmob.com/leagues/77/stats/world-cup/players?season=2026), and [FBref](https://fbref.com/en/comps/1/stats/World-Cup-Stats). The committed `data/official/world_cup_2026_player_stats.csv` file stores current public stat leaders for World Cup goals, assists, goal contributions, xG, xA, clean sheets, conceded rate, and saves.
- API-Football for real teams, fixtures, squads, and fixture player stats when `API_FOOTBALL_KEY` is available.

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
  -> visuals.py renders clean interactive dashboards
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
- `site/index-assets/dashboard.css`
- `site/index-assets/dashboard.js`
- `site/index-assets/app-data.json`

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

The committed sample dataset uses synthetic `Demo ...` players only for pipeline tests. The default dashboard uses the official FIFA squad CSV in `data/official/fifa_squads_2026.csv`, not the sample players.

Generate the official roster dashboard:

```bash
make official-dashboard
```

Then open:

```text
site/index.html
```

The dashboard lets you choose any two teams, compare squad profiles, search all 1,248 official players, filter by team/role, compare players side by side, inspect World Cup goals/assists/xG separately from career international goals, and view rating/prediction coverage status.

Fetch API-Football data after creating a free key:

```bash
export API_FOOTBALL_KEY=your_key_here
make api-football-ingest
```

API-Football fixture player stats can then be loaded into the rating database to unlock real per-game ratings, advanced metrics, and prediction confidence. Unsupported fields such as xG, pressures, and progressive carries remain empty instead of being invented.

Generate the synthetic sample dashboard separately:

```bash
make sample-dashboard
```

This writes `site/sample.html` and isolated `site/sample-assets/*`.

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
- Visual dashboards are generated from official roster data plus real imported report outputs. They include team selectors, roster comparison, searchable player tables, player-vs-player comparison, World Cup stat leaderboards, prediction panels, validation metrics, and data coverage states.

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

The dashboard is a small static app generated under `site/`: an HTML shell plus isolated CSS, JavaScript, and JSON data assets. It can be served locally or published later with GitHub Pages.

See [docs/visual-dashboard.md](docs/visual-dashboard.md).

## Accuracy Notes

Free data will not always include confirmed lineups, injuries, complete current player-level match stats, or external player ratings. The system handles that by lowering confidence, exposing coverage reports, and validating only against rating sources that are actually provided. The official dashboard separates career international goals from World Cup 2026 tournament goals. Full every-player match stats still require a reliable feed such as API-Football fixture player statistics, a licensed export, or a checked local dataset.
