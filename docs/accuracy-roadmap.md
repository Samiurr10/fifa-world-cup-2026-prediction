# Accuracy Roadmap

The roadmap is ordered by likely improvement to forecast quality.

## 1. Better Data Coverage

- Add more historical national-team matches.
- Add current 2026 results as the tournament progresses.
- Add reliable lineups only when the source is trustworthy.
- Track missing data explicitly and reduce confidence when coverage is weak.

## 2. Stronger Feature Engineering

- Team xG for and against.
- Shot quality and shot volume.
- Progressive passes and carries.
- Defensive pressure and recoveries.
- Rest days and travel burden.
- Tournament stage and knockout context.
- Opponent-specific weaknesses.

## 3. Better Score Models

- Calibrate Poisson scorelines against backtests.
- Add Dixon-Coles style low-score adjustment.
- Add team-specific attack/defense ratings.
- Compare against Elo/FIFA-ranking baselines.

## 4. Better Player Impact

- Normalize all player stats per 90 minutes.
- Separate starters from substitutes when lineup data exists.
- Add opponent-side matchup features.
- Use role-specific baselines instead of one global score.

## 5. Better Evaluation

- Track exact-score top-3 hit rate.
- Track outcome log loss and Brier score.
- Track calibration.
- Compare against naive baselines before claiming improvement.

