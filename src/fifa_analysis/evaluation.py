"""Backtesting metrics for scoreline and outcome predictions."""

from __future__ import annotations

import math
from collections import defaultdict

from fifa_analysis.predictors import predict_match
from fifa_analysis.schemas import MatchRecord, TeamMatchStats


def _actual_outcome(match: MatchRecord) -> str:
    if match.home_goals is None or match.away_goals is None:
        raise ValueError(f"Match {match.match_id} has no final score.")
    if match.home_goals > match.away_goals:
        return "home_win"
    if match.away_goals > match.home_goals:
        return "away_win"
    return "draw"


def _brier(predicted: dict[str, float], actual: str) -> float:
    return sum((predicted[key] - (1.0 if key == actual else 0.0)) ** 2 for key in predicted) / 3


def _log_loss(predicted: dict[str, float], actual: str) -> float:
    return -math.log(max(0.001, predicted[actual]))


def backtest_predictions(matches: list[MatchRecord], team_rows: list[TeamMatchStats]) -> dict[str, object]:
    finished = [match for match in matches if match.home_goals is not None and match.away_goals is not None]
    if not finished:
        raise ValueError("No finished matches available for backtesting.")

    exact_top3 = 0
    outcome_correct = 0
    brier_total = 0.0
    log_loss_total = 0.0
    buckets: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0.0, "correct": 0.0})

    for match in finished:
        prediction = predict_match(match.home_team, match.away_team, team_rows, top_n=5)
        actual_score = f"{match.home_goals}-{match.away_goals}"
        if actual_score in {row["score"] for row in prediction.top_scorelines[:3]}:
            exact_top3 += 1

        probabilities = {
            "home_win": prediction.home_win,
            "draw": prediction.draw,
            "away_win": prediction.away_win,
        }
        predicted_outcome = max(probabilities, key=probabilities.get)
        actual = _actual_outcome(match)
        if predicted_outcome == actual:
            outcome_correct += 1
        brier_total += _brier(probabilities, actual)
        log_loss_total += _log_loss(probabilities, actual)

        favorite_probability = probabilities[predicted_outcome]
        bucket_start = int(favorite_probability * 10) * 10
        bucket = f"{bucket_start}-{bucket_start + 10}%"
        buckets[bucket]["count"] += 1
        buckets[bucket]["correct"] += 1 if predicted_outcome == actual else 0

    calibration = [
        {
            "bucket": bucket,
            "count": int(values["count"]),
            "accuracy": round(values["correct"] / values["count"], 3),
        }
        for bucket, values in sorted(buckets.items())
    ]

    count = len(finished)
    return {
        "matches": count,
        "exact_score_top3_rate": round(exact_top3 / count, 3),
        "outcome_accuracy": round(outcome_correct / count, 3),
        "brier_score": round(brier_total / count, 3),
        "log_loss": round(log_loss_total / count, 3),
        "calibration": calibration,
    }

