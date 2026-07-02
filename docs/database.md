# Rating Database

The project uses SQLite for reproducible local storage.

Default database path:

```text
data/db/worldcup_ratings.sqlite
```

Generated databases are ignored by Git. The schema and commands are committed, not the local DB file.

## Tables

### `teams`

Stores team names.

### `players`

Stores player identity, team, position, and role group.

Unique key:

```text
player + team
```

### `matches`

Stores normalized match records.

Fields include:

- match id
- date
- home team
- away team
- final score when available
- status
- stage
- source

### `player_game_stats`

Stores the raw stat row used for rating one player in one match.

Important fields:

- minutes
- goals
- assists
- xG
- shots
- progressive passes
- progressive carries
- carries
- dribbles
- interceptions
- tackles
- clearances
- aerials
- pressures
- recoveries
- goalkeeper saves/claims
- pass completion
- chance creation

### `player_game_ratings`

Stores calculated per-game ratings and component scores.

### `player_overall_ratings`

Stores tournament-level player ratings aggregated from game ratings.

### `rating_validation`

Stores validation summaries against external/actual ratings.

## End-to-End Rating Flow

```bash
PYTHONPATH=src python3 -m fifa_analysis.cli init-db --db data/db/worldcup_ratings.sqlite

PYTHONPATH=src python3 -m fifa_analysis.cli load-player-stats \
  --db data/db/worldcup_ratings.sqlite \
  --player-stats data/sample/player_match_stats_sample.csv

PYTHONPATH=src python3 -m fifa_analysis.cli rate-db \
  --db data/db/worldcup_ratings.sqlite

PYTHONPATH=src python3 -m fifa_analysis.cli export-game-ratings \
  --db data/db/worldcup_ratings.sqlite \
  --output reports/player_game_ratings.csv

PYTHONPATH=src python3 -m fifa_analysis.cli export-overall-ratings \
  --db data/db/worldcup_ratings.sqlite \
  --output reports/player_overall_ratings.csv
```

## All Players Requirement

The database can store all World Cup players, but the completeness depends on the source:

- squad/roster data can populate all players
- lineup data can populate players who appeared in matches
- event/player-stat data can produce meaningful game ratings
- tournament stat-leader files can populate current World Cup leader metrics, but they do not replace full per-match player stats

If a player exists only in a roster but has no minutes or stats, they should be stored as a player but should not receive a confident performance rating.

The FIFA squad list `international_goals` field is a career national-team total. World Cup 2026 goals, assists, xG, xA, clean sheets, conceded rate, and saves are stored separately in `data/official/world_cup_2026_player_stats.csv` so career goals are never presented as tournament goals.
