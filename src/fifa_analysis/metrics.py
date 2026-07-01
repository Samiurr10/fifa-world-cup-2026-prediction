"""Player-level football metrics from event data."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from fifa_analysis.roles import role_profile

PITCH_LENGTH = 120.0


def load_events(path: str | Path) -> list[dict[str, Any]]:
    """Load a StatsBomb-style JSON event file."""

    with Path(path).open(encoding="utf-8") as event_file:
        events = json.load(event_file)
    if not isinstance(events, list):
        raise ValueError("Expected a JSON array of event objects.")
    return events


def _name(value: Any) -> str | None:
    if isinstance(value, dict):
        return value.get("name")
    if isinstance(value, str):
        return value
    return None


def _event_type(event: dict[str, Any]) -> str:
    return _name(event.get("type")) or "Unknown"


def _player_name(event: dict[str, Any]) -> str | None:
    return _name(event.get("player"))


def _team_name(event: dict[str, Any]) -> str | None:
    return _name(event.get("team"))


def _position_name(event: dict[str, Any]) -> str | None:
    return _name(event.get("position"))


def _location(event: dict[str, Any], key: str = "location") -> tuple[float, float] | None:
    value = event.get(key)
    if isinstance(value, list) and len(value) >= 2:
        return float(value[0]), float(value[1])
    return None


def _end_location(event: dict[str, Any], nested_key: str) -> tuple[float, float] | None:
    payload = event.get(nested_key)
    if isinstance(payload, dict):
        value = payload.get("end_location")
        if isinstance(value, list) and len(value) >= 2:
            return float(value[0]), float(value[1])
    return None


def _forward_progress(start: tuple[float, float] | None, end: tuple[float, float] | None) -> float:
    if start is None or end is None:
        return 0.0
    return max(0.0, end[0] - start[0])


def _distance(start: tuple[float, float] | None, end: tuple[float, float] | None) -> float:
    if start is None or end is None:
        return 0.0
    return math.dist(start, end)


def _is_successful(event: dict[str, Any], nested_key: str) -> bool:
    payload = event.get(nested_key)
    return not (isinstance(payload, dict) and "outcome" in payload)


def _shot_goal(event: dict[str, Any]) -> bool:
    shot = event.get("shot")
    return isinstance(shot, dict) and _name(shot.get("outcome")) == "Goal"


def _shot_xg(event: dict[str, Any]) -> float:
    shot = event.get("shot")
    if isinstance(shot, dict):
        return float(shot.get("statsbomb_xg", 0.0) or 0.0)
    return 0.0


def empty_player_row(player: str, team: str | None, position: str | None) -> dict[str, Any]:
    profile = role_profile(position)
    return {
        "player": player,
        "team": team or "Unknown",
        "position": profile.position,
        "role_group": profile.group,
        "events": 0,
        "passes": 0,
        "completed_passes": 0,
        "pass_completion_pct": 0.0,
        "progressive_passes": 0,
        "carries": 0,
        "carry_distance": 0.0,
        "progressive_carries": 0,
        "dribbles": 0,
        "successful_dribbles": 0,
        "interceptions": 0,
        "tackles": 0,
        "clearances": 0,
        "aerials_won": 0,
        "pressures": 0,
        "ball_recoveries": 0,
        "saves": 0,
        "claims": 0,
        "defensive_actions": 0,
        "shots": 0,
        "xg": 0.0,
        "goals": 0,
        "assists": 0,
        "key_passes": 0,
        "chance_creation": 0,
        "goal_contributions": 0,
        "contribution_score": 0.0,
    }


def player_metrics(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate event data into player-level contribution metrics."""

    players: dict[str, dict[str, Any]] = {}

    for event in events:
        player = _player_name(event)
        if not player:
            continue

        if player not in players:
            players[player] = empty_player_row(player, _team_name(event), _position_name(event))

        row = players[player]
        row["events"] += 1
        event_type = _event_type(event)
        start = _location(event)

        if event_type == "Pass":
            row["passes"] += 1
            if _is_successful(event, "pass"):
                row["completed_passes"] += 1
            end = _end_location(event, "pass")
            if _forward_progress(start, end) >= 10:
                row["progressive_passes"] += 1
            pass_payload = event.get("pass")
            if isinstance(pass_payload, dict) and pass_payload.get("shot_assist"):
                row["key_passes"] += 1
                row["chance_creation"] += 1
            if isinstance(pass_payload, dict) and pass_payload.get("goal_assist"):
                row["assists"] += 1
                row["goal_contributions"] += 1

        elif event_type == "Carry":
            row["carries"] += 1
            end = _end_location(event, "carry")
            row["carry_distance"] += _distance(start, end)
            if _forward_progress(start, end) >= 10:
                row["progressive_carries"] += 1

        elif event_type == "Dribble":
            row["dribbles"] += 1
            dribble = event.get("dribble")
            if isinstance(dribble, dict) and _name(dribble.get("outcome")) == "Complete":
                row["successful_dribbles"] += 1

        elif event_type == "Interception":
            row["interceptions"] += 1
            row["defensive_actions"] += 1

        elif event_type == "Duel":
            duel = event.get("duel")
            if isinstance(duel, dict) and _name(duel.get("type")) == "Tackle":
                row["tackles"] += 1
                row["defensive_actions"] += 1
            if isinstance(duel, dict) and _name(duel.get("outcome")) in {
                "Won",
                "Success In Play",
                "Success Out",
            }:
                row["aerials_won"] += 1

        elif event_type == "Pressure":
            row["pressures"] += 1
            row["defensive_actions"] += 1

        elif event_type == "Ball Recovery":
            row["ball_recoveries"] += 1
            row["defensive_actions"] += 1

        elif event_type == "Clearance":
            row["clearances"] += 1
            row["defensive_actions"] += 1

        elif event_type == "Goal Keeper":
            goalkeeper = event.get("goalkeeper")
            action_type = _name(goalkeeper.get("type")) if isinstance(goalkeeper, dict) else None
            if action_type in {"Shot Saved", "Save", "Collected"}:
                row["saves"] += 1
            if action_type in {"Claim", "Collected", "Punch"}:
                row["claims"] += 1

        elif event_type == "Shot":
            row["shots"] += 1
            row["xg"] += _shot_xg(event)
            if _shot_goal(event):
                row["goals"] += 1
                row["goal_contributions"] += 1

    for row in players.values():
        if row["passes"]:
            row["pass_completion_pct"] = round(row["completed_passes"] / row["passes"] * 100, 2)
        row["carry_distance"] = round(row["carry_distance"], 2)
        row["xg"] = round(row["xg"], 3)

    return sorted(players.values(), key=lambda row: row["player"])


def score_contributions(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add a normalized, role-aware contribution score to each player row."""

    rows = [dict(row) for row in rows]
    max_by_metric: dict[str, float] = defaultdict(float)

    for row in rows:
        for metric, value in row.items():
            if isinstance(value, (int, float)) and metric not in {"contribution_score"}:
                max_by_metric[metric] = max(max_by_metric[metric], float(value))

    for row in rows:
        profile = role_profile(row.get("position"))
        weighted_total = 0.0
        weight_sum = 0.0
        for metric, weight in profile.weights.items():
            denominator = max_by_metric.get(metric, 0.0)
            if denominator <= 0:
                continue
            weighted_total += (float(row.get(metric, 0.0)) / denominator) * weight
            weight_sum += weight
        row["contribution_score"] = round((weighted_total / weight_sum) * 100, 2) if weight_sum else 0.0

    return sorted(rows, key=lambda row: row["contribution_score"], reverse=True)


def team_summary(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate player metrics into team totals."""

    teams: dict[str, dict[str, Any]] = {}
    numeric_fields = [
        "progressive_passes",
        "progressive_carries",
        "interceptions",
        "defensive_actions",
        "shots",
        "xg",
        "goals",
        "assists",
        "chance_creation",
        "goal_contributions",
    ]
    for row in rows:
        team = row["team"]
        teams.setdefault(team, {"team": team, "players": 0, **{field: 0.0 for field in numeric_fields}})
        teams[team]["players"] += 1
        for field in numeric_fields:
            teams[team][field] += float(row.get(field, 0.0))

    for team in teams.values():
        team["xg"] = round(team["xg"], 3)

    return sorted(teams.values(), key=lambda row: row["team"])
