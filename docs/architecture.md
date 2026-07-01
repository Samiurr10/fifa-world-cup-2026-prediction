# Architecture

This project is an accuracy-first football prediction engine built around normalized data and auditable model outputs.

## Data Ingestion

`connectors.py` isolates provider-specific formats:

- StatsBomb event files for rich historical team/player features.
- openfootball JSON for World Cup schedules/results.
- worldcup2026 API responses for 2026 tournament state.
- football-data.org responses when an API token is available.
- local CSV/Kaggle-style files for controlled experiments.

Each connector should output shared records from `schemas.py`, not provider-shaped data.

## Normalized Records

The core normalized records are:

- `MatchRecord`
- `TeamMatchStats`
- `PlayerMatchStats`
- `TeamProfile`
- `MatchPrediction`
- `PlayerImpact`
- `PlayerGameRating`
- `PlayerOverallRating`

These records make it possible to swap data providers without rewriting model logic.

## Feature Layer

`features.py` builds:

- recent weighted team profiles
- attacking and defensive strength
- recent form points
- progressive action strength
- defensive activity
- player role form scores
- opponent weakness multipliers by role

Recent matches are weighted more heavily because 2026 predictions should respond to current form.

## Prediction Layer

`predictors.py` contains three layers:

- expected-goals estimation
- Poisson exact-score distribution
- outcome probabilities from the score distribution

It also ranks player impact with role-specific formulas and opponent matchup adjustment.

## Rating Database Layer

`database.py` stores:

- normalized matches
- players and teams
- player-game stats
- per-game ratings
- overall ratings
- validation metrics

`ratings.py` computes bounded `1-10` player ratings from role-specific attacking, possession, defensive, and goalkeeping components.

`validation.py` compares generated ratings against external/actual ratings when those are available.

## Report Layer

`reports.py` generates Markdown analysis from computed prediction objects. It should never invent unavailable data such as injuries, confirmed lineups, or undocumented player stats.
