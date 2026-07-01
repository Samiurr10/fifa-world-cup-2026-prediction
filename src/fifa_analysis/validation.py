"""Validation utilities for player ratings and database coverage."""

from __future__ import annotations

import csv
import math
from pathlib import Path

from fifa_analysis.ratings import PlayerGameRating


def read_external_ratings(path: str | Path) -> list[dict[str, object]]:
    with Path(path).open(encoding="utf-8", newline="") as csv_file:
        rows = []
        for row in csv.DictReader(csv_file):
            rows.append(
                {
                    "match_id": row["match_id"],
                    "player": row["player"],
                    "team": row["team"],
                    "external_rating": float(row["external_rating"]),
                    "source": row.get("source", "external"),
                }
            )
        return rows


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return None
    return numerator / (denom_x * denom_y)


def compare_external_ratings(
    generated: list[PlayerGameRating], external: list[dict[str, object]]
) -> dict[str, object]:
    generated_lookup = {
        (row.match_id, row.player, row.team): row.rating
        for row in generated
    }
    pairs: list[tuple[float, float]] = []
    missing: list[dict[str, object]] = []

    for row in external:
        key = (str(row["match_id"]), str(row["player"]), str(row["team"]))
        if key not in generated_lookup:
            missing.append(row)
            continue
        pairs.append((generated_lookup[key], float(row["external_rating"])))

    if not pairs:
        return {
            "sample_size": 0,
            "mae": None,
            "correlation": None,
            "within_half_point_rate": None,
            "missing_external_rows": len(missing),
        }

    generated_values = [pair[0] for pair in pairs]
    external_values = [pair[1] for pair in pairs]
    errors = [abs(generated_value - external_value) for generated_value, external_value in pairs]

    return {
        "sample_size": len(pairs),
        "mae": round(sum(errors) / len(errors), 3),
        "correlation": (
            None
            if _pearson(generated_values, external_values) is None
            else round(_pearson(generated_values, external_values), 3)
        ),
        "within_half_point_rate": round(
            sum(1 for error in errors if error <= 0.5) / len(errors),
            3,
        ),
        "missing_external_rows": len(missing),
    }


def rating_coverage(game_ratings: list[PlayerGameRating]) -> dict[str, object]:
    if not game_ratings:
        return {
            "rated_player_games": 0,
            "players": 0,
            "matches": 0,
            "confidence": {},
        }
    confidence: dict[str, int] = {}
    for row in game_ratings:
        confidence[row.confidence] = confidence.get(row.confidence, 0) + 1
    return {
        "rated_player_games": len(game_ratings),
        "players": len({(row.player, row.team) for row in game_ratings}),
        "matches": len({row.match_id for row in game_ratings}),
        "confidence": confidence,
    }

