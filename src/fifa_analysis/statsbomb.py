"""StatsBomb event/lineup normalization for player ratings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fifa_analysis.connectors import load_json
from fifa_analysis.metrics import player_metrics, score_contributions
from fifa_analysis.roles import classify_position
from fifa_analysis.schemas import PlayerMatchStats


def _name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or "")
    return str(value or "")


def _minute(value: Any) -> float:
    if value in (None, ""):
        return 90.0
    text = str(value)
    if ":" not in text:
        return float(text)
    return float(text.split(":", 1)[0])


def _lineup_team(team_payload: dict[str, Any]) -> str:
    return str(
        team_payload.get("team_name")
        or team_payload.get("team")
        or _name(team_payload.get("team_id"))
        or ""
    )


def lineup_player_minutes(lineups: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return best-known team, position, and minutes for StatsBomb lineup players."""

    players: dict[str, dict[str, Any]] = {}
    for team_payload in lineups:
        team = _lineup_team(team_payload)
        for player_payload in team_payload.get("lineup", []) or []:
            player = str(player_payload.get("player_name") or _name(player_payload.get("player")) or "")
            if not player:
                continue
            positions = player_payload.get("positions", []) or []
            minutes = 0.0
            position_minutes: dict[str, float] = {}
            for position_payload in positions:
                position = _name(position_payload.get("position")) or str(
                    position_payload.get("position_name") or "Unknown"
                )
                start = _minute(position_payload.get("from", 0.0))
                end = _minute(position_payload.get("to", 90.0))
                segment = max(0.0, end - start)
                minutes += segment
                position_minutes[position] = position_minutes.get(position, 0.0) + segment
            if not positions:
                minutes = 0.0
                position = str(player_payload.get("position") or "Unknown")
            else:
                position = max(position_minutes, key=position_minutes.get)
            players[player] = {
                "team": team,
                "position": position,
                "role_group": classify_position(position),
                "minutes": round(minutes, 1),
            }
    return players


def statsbomb_events_to_player_stats(
    events: list[dict[str, Any]],
    match_id: str,
    home_team: str,
    away_team: str,
    lineups: list[dict[str, Any]] | None = None,
    source: str = "statsbomb",
) -> list[PlayerMatchStats]:
    lineup_lookup = lineup_player_minutes(lineups or [])
    metric_rows = {
        row["player"]: row
        for row in score_contributions(player_metrics(events))
    }
    all_players = set(metric_rows) | set(lineup_lookup)
    rows: list[PlayerMatchStats] = []

    for player in sorted(all_players):
        metric = metric_rows.get(player, {})
        lineup = lineup_lookup.get(player, {})
        team = str(metric.get("team") or lineup.get("team") or "")
        if not team:
            continue
        opponent = away_team if team == home_team else home_team
        position = str(metric.get("position") or lineup.get("position") or "Unknown")
        role_group = str(metric.get("role_group") or lineup.get("role_group") or classify_position(position))
        rows.append(
            PlayerMatchStats(
                match_id=match_id,
                player=player,
                team=team,
                opponent=opponent,
                position=position,
                role_group=role_group,
                minutes=float(lineup.get("minutes") or 90.0),
                goals=float(metric.get("goals", 0.0)),
                assists=float(metric.get("assists", 0.0)),
                xg=float(metric.get("xg", 0.0)),
                shots=float(metric.get("shots", 0.0)),
                progressive_passes=float(metric.get("progressive_passes", 0.0)),
                progressive_carries=float(metric.get("progressive_carries", 0.0)),
                carries=float(metric.get("carries", 0.0)),
                successful_dribbles=float(metric.get("successful_dribbles", 0.0)),
                interceptions=float(metric.get("interceptions", 0.0)),
                tackles=float(metric.get("tackles", 0.0)),
                clearances=float(metric.get("clearances", 0.0)),
                aerials_won=float(metric.get("aerials_won", 0.0)),
                pressures=float(metric.get("pressures", 0.0)),
                ball_recoveries=float(metric.get("ball_recoveries", 0.0)),
                saves=float(metric.get("saves", 0.0)),
                claims=float(metric.get("claims", 0.0)),
                pass_completion_pct=float(metric.get("pass_completion_pct", 0.0)),
                chance_creation=float(metric.get("chance_creation", 0.0)),
                contribution_score=float(metric.get("contribution_score", 0.0)),
                source=source,
            )
        )
    return rows


def statsbomb_files_to_player_stats(
    events_path: str | Path,
    match_id: str,
    home_team: str,
    away_team: str,
    lineups_path: str | Path | None = None,
) -> list[PlayerMatchStats]:
    events = load_json(events_path)
    lineups = load_json(lineups_path) if lineups_path else None
    return statsbomb_events_to_player_stats(events, match_id, home_team, away_team, lineups)

