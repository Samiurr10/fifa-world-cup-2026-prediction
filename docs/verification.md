# Verification

Run the full local verification path:

```bash
make verify
```

Expected result:

- all unit tests pass
- sample player metrics are generated
- sample team summary is generated
- openfootball-style sample data is normalized
- match prediction JSON is generated
- player impact CSV is generated
- grounded match report is generated
- backtest metrics JSON is generated

## Individual Checks

```bash
make test
make sample-match
make sample-impact
make sample-report
make sample-backtest
```

Prediction output should include:

- expected goals
- win/draw/loss probabilities
- top scorelines
- confidence
- reasons

Player impact output should include:

- impact score
- role group
- form score
- matchup adjustment
- confidence

Backtest output should include:

- exact-score top-3 hit rate
- outcome accuracy
- Brier score
- log loss
- calibration buckets
