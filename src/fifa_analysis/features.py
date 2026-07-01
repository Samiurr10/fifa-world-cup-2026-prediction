"""Feature pipelines for team form, scoreline models, and player impact."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from fifa_analysis.connectors import csv_float, load_csv_rows
from fifa_analysis.schemas import PlayerMatchStats, TeamMatchStats, TeamProfile


def read_team_match_stats(path: str | Path) -> list[TeamMatchStats]:
    rows = load_csv_rows(path)
    return [
        TeamMatchStats(
            match_id=row.get("match_id", ""),
            team=row.get("team", ""),
            opponent=row.get("opponent", ""),
            goals_for=csv_float(row, "goals_for"),
            goals_against=csv_float(row, "goals_against"),
            xg_for=csv_float(row, "xg_for", csv_float(row, "goals_for")),
            xg_against=csv_float(row, "xg_against", csv_float(row, "goals_against")),
            shots_for=csv_float(row, "shots_for"),
            shots_against=csv_float(row, "shots_against"),
            progressive_passes=csv_float(row, "progressive_passes"),
            progressive_carries=csv_float(row, "progressive_carries"),
            defensive_actions=csv_float(row, "defensive_actions"),
            venue=row.get("venue", "neutral"),
            date=row.get("date", ""),
            source=row.get("source", ""),
        )
        for row in rows
    ]


def read_player_match_stats(path: str | Path) -> list[PlayerMatchStats]:
    rows = load_csv_rows(path)
    return [
        PlayerMatchStats(
            match_id=row.get("match_id", ""),
            player=row.get("player", ""),
            team=row.get("team", ""),
            opponent=row.get("opponent", ""),
            position=row.get("position", "Unknown"),
            role_group=row.get("role_group", "unknown"),
            minutes=csv_float(row, "minutes", 90.0),
            goals=csv_float(row, "goals"),
            assists=csv_float(row, "assists"),
            xg=csv_float(row, "xg"),
            shots=csv_float(row, "shots"),
            progressive_passes=csv_float(row, "progressive_passes"),
            progressive_carries=csv_float(row, "progressive_carries"),
            carries=csv_float(row, "carries"),
            successful_dribbles=csv_float(row, "successful_dribbles"),
            interceptions=csv_float(row, "interceptions"),
            tackles=csv_float(row, "tackles"),
            clearances=csv_float(row, "clearances"),
            aerials_won=csv_float(row, "aerials_won"),
            pressures=csv_float(row, "pressures"),
            ball_recoveries=csv_float(row, "ball_recoveries"),
            saves=csv_float(row, "saves"),
            claims=csv_float(row, "claims"),
            pass_completion_pct=csv_float(row, "pass_completion_pct"),
            chance_creation=csv_float(row, "chance_creation"),
            contribution_score=csv_float(row, "contribution_score"),
            source=row.get("source", ""),
        )
        for row in rows
    ]


def _points_for(row: TeamMatchStats) -> float:
    if row.goals_for > row.goals_against:
        return 3.0
    if row.goals_for == row.goals_against:
        return 1.0
    return 0.0


def _weighted_average(values: list[float], recent_weight: float = 1.35) -> float:
    if not values:
        return 0.0
    total_weight = 0.0
    weighted_total = 0.0
    for index, value in enumerate(values):
        weight = recent_weight ** index
        total_weight += weight
        weighted_total += value * weight
    return weighted_total / total_weight


def build_team_profile(team: str, rows: list[TeamMatchStats], recent_matches: int = 5) -> TeamProfile:
    team_rows = [row for row in rows if row.team == team]
    team_rows = sorted(team_rows, key=lambda row: row.date)[-recent_matches:]
    if not team_rows:
        return TeamProfile(
            team=team,
            matches=0,
            attack_xg=1.1,
            defense_xg=1.1,
            goals_for=1.1,
            goals_against=1.1,
            shots_for=10.0,
            shots_against=10.0,
            form_points=1.0,
            progressive_strength=20.0,
            defensive_activity=20.0,
        )

    return TeamProfile(
        team=team,
        matches=len(team_rows),
        attack_xg=round(_weighted_average([row.xg_for for row in team_rows]), 3),
        defense_xg=round(_weighted_average([row.xg_against for row in team_rows]), 3),
        goals_for=round(_weighted_average([row.goals_for for row in team_rows]), 3),
        goals_against=round(_weighted_average([row.goals_against for row in team_rows]), 3),
        shots_for=round(_weighted_average([row.shots_for for row in team_rows]), 3),
        shots_against=round(_weighted_average([row.shots_against for row in team_rows]), 3),
        form_points=round(_weighted_average([_points_for(row) for row in team_rows]), 3),
        progressive_strength=round(
            _weighted_average(
                [row.progressive_passes + row.progressive_carries for row in team_rows]
            ),
            3,
        ),
        defensive_activity=round(_weighted_average([row.defensive_actions for row in team_rows]), 3),
    )


def build_all_team_profiles(rows: list[TeamMatchStats], recent_matches: int = 5) -> dict[str, TeamProfile]:
    return {team: build_team_profile(team, rows, recent_matches) for team in sorted({row.team for row in rows})}


def opponent_weakness_against_role(opponent: str, role_group: str, rows: list[TeamMatchStats]) -> float:
    opponent_rows = [row for row in rows if row.team == opponent]
    if not opponent_rows:
        return 1.0
    conceded_xg = sum(row.xg_against for row in opponent_rows) / len(opponent_rows)
    shots_against = sum(row.shots_against for row in opponent_rows) / len(opponent_rows)
    defensive_activity = sum(row.defensive_actions for row in opponent_rows) / len(opponent_rows)

    if role_group in {"forward", "winger", "attacking_midfielder"}:
        return max(0.75, min(1.35, 0.78 + conceded_xg * 0.18 + shots_against * 0.018))
    if role_group in {"central_midfielder", "defensive_midfielder"}:
        return max(0.8, min(1.25, 0.95 + (25.0 - defensive_activity) * 0.006))
    if role_group in {"center_back", "full_back", "goalkeeper"}:
        return max(0.8, min(1.25, 0.95 + shots_against * 0.01))
    return 1.0


def player_recent_rows(
    player_rows: list[PlayerMatchStats], team: str, opponent: str | None = None, recent_matches: int = 5
) -> dict[str, list[PlayerMatchStats]]:
    grouped: dict[str, list[PlayerMatchStats]] = defaultdict(list)
    for row in player_rows:
        if row.team != team:
            continue
        grouped[row.player].append(row)
    return {
        player: sorted(rows, key=lambda row: row.match_id)[-recent_matches:]
        for player, rows in grouped.items()
    }


def player_role_form_score(rows: list[PlayerMatchStats]) -> float:
    if not rows:
        return 0.0
    role = rows[-1].role_group
    scores: list[float] = []
    for row in rows:
        per90 = 90.0 / max(row.minutes, 1.0)
        if role == "forward":
            value = row.xg * 28 + row.shots * 5 + row.goals * 20 + row.assists * 12 + row.pressures * 1.2
        elif role == "winger":
            value = (
                row.progressive_carries * 9
                + row.successful_dribbles * 8
                + row.chance_creation * 10
                + row.xg * 16
                + row.assists * 12
            )
        elif role in {"attacking_midfielder", "central_midfielder"}:
            value = (
                row.progressive_passes * 7
                + row.chance_creation * 12
                + row.progressive_carries * 5
                + row.pass_completion_pct * 0.18
                + row.assists * 12
            )
        elif role == "defensive_midfielder":
            value = (
                row.interceptions * 8
                + row.ball_recoveries * 6
                + row.progressive_passes * 6
                + row.pass_completion_pct * 0.16
                + row.tackles * 7
            )
        elif role in {"center_back", "full_back"}:
            value = (
                row.interceptions * 9
                + row.tackles * 8
                + row.clearances * 4
                + row.aerials_won * 5
                + row.progressive_passes * 5
            )
        elif role == "goalkeeper":
            value = row.saves * 10 + row.claims * 5 + row.pass_completion_pct * 0.12
        else:
            value = row.contribution_score
        scores.append(value * per90)
    return round(_weighted_average(scores), 2)

