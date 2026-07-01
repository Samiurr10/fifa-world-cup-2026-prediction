# Player Performance Ratings

The rating system stores every available player-game row in SQLite and computes:

- one game rating per player per match
- one overall tournament rating per player
- confidence labels based on minutes and match coverage
- validation metrics against external rating sources when available

## Rating Scale

Ratings are bounded from `1.00` to `10.00`.

The engine starts from a neutral baseline and adds role-weighted performance value. It does not use one universal formula for every position.

## Role Weighting

Primary role emphasis:

- goalkeepers: saves, claims, pass quality
- center backs: defensive actions, clearances, aerials, progressive passing
- fullbacks: defending, progression, chance creation
- defensive midfielders: recoveries, interceptions, tackling, progressive passing
- central midfielders: progression, pass quality, defending, chance creation
- attacking midfielders: chance creation, progression, attacking output
- wingers: carries, dribbles, chance creation, attacking output
- forwards: xG, shots, goals, assists, pressing

## Rating Components

Each player-game is split into four component scores:

- `attacking_score`
- `possession_score`
- `defensive_score`
- `goalkeeping_score`

The player role decides how much each component matters. A forward receives more weight from attacking score. A center back receives more from defensive score. A goalkeeper receives most of the weight from goalkeeping score.

## Confidence

Game rating confidence:

- `medium`: player played at least 60 minutes
- `low`: player played fewer than 60 minutes

Overall rating confidence:

- `high`: at least 5 matches and 300 minutes
- `medium`: at least 3 matches or enough minutes
- `low`: sparse minutes or few matches

## Validation

If actual/external ratings are available, provide a CSV:

```csv
match_id,player,team,external_rating,source
ARG-1,Lionel Messi,Argentina,8.8,sample_external
```

Then run:

```bash
PYTHONPATH=src python3 -m fifa_analysis.cli validate-ratings \
  --db data/db/worldcup_ratings.sqlite \
  --external-ratings data/sample/external_ratings_sample.csv \
  --output reports/rating_validation.json \
  --store
```

Validation reports:

- sample size
- mean absolute error
- Pearson correlation
- within-half-point rate
- missing external rows

