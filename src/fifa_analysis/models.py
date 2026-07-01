"""Legacy baseline evaluation helpers."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Prediction:
    home_win: float
    draw: float
    away_win: float


def _sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def _rounded_prediction(home_win: float, draw: float, away_win: float) -> Prediction:
    home = round(home_win, 3)
    draw_probability = round(draw, 3)
    away = round(1.0 - home - draw_probability, 3)
    return Prediction(home_win=home, draw=draw_probability, away_win=away)


def baseline_match_prediction(
    home_attack: float,
    home_defense: float,
    away_attack: float,
    away_defense: float,
    home_advantage: float = 0.18,
) -> Prediction:
    """Estimate 1X2 probabilities from aggregate team strengths.

    This transparent baseline is kept for baseline comparison. The production
    prediction path lives in predictors.py and produces scorelines plus outcome
    probabilities from expected goals.
    """

    home_edge = (home_attack - away_defense) - (away_attack - home_defense) + home_advantage
    home_win_raw = _sigmoid(home_edge)
    away_win_raw = _sigmoid(-home_edge)
    draw_raw = max(0.12, 0.32 - abs(home_edge) * 0.08)
    total = home_win_raw + away_win_raw + draw_raw
    return _rounded_prediction(home_win_raw / total, draw_raw / total, away_win_raw / total)


def load_match_features(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def evaluate_baseline(path: str | Path) -> dict[str, float]:
    """Evaluate the baseline on a CSV with team strength columns and result labels."""

    rows = load_match_features(path)
    if not rows:
        raise ValueError("No match rows found.")

    correct = 0
    brier_total = 0.0
    labels = {"H": "home_win", "D": "draw", "A": "away_win"}

    for row in rows:
        pred = baseline_match_prediction(
            home_attack=float(row["home_attack"]),
            home_defense=float(row["home_defense"]),
            away_attack=float(row["away_attack"]),
            away_defense=float(row["away_defense"]),
            home_advantage=float(row.get("home_advantage", 0.18) or 0.18),
        )
        probabilities = pred.__dict__
        predicted_label = max(probabilities, key=probabilities.get)
        actual_label = labels[row["result"]]
        if predicted_label == actual_label:
            correct += 1
        for label_name, probability in probabilities.items():
            observed = 1.0 if label_name == actual_label else 0.0
            brier_total += (probability - observed) ** 2

    return {
        "rows": len(rows),
        "accuracy": round(correct / len(rows), 3),
        "brier_score": round(brier_total / (len(rows) * 3), 3),
    }
