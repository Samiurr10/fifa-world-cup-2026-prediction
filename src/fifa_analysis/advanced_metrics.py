"""Advanced role-aware player metrics for performance analysis."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from fifa_analysis.schemas import PlayerMatchStats


@dataclass(frozen=True)
class AdvancedPlayerMetrics:
    match_id: str
    player: str
    team: str
    opponent: str
    role_group: str
    minutes: float
    attacking_involvement: float
    progression_value: float
    ball_security: float
    defensive_disruption: float
    goalkeeping_value: float
    two_way_value: float
    xg_efficiency: float
    usage_rate: float
    role_fit_score: float
    per90_summary_json: str


def _per90(value: float, minutes: float) -> float:
    return value * 90.0 / max(minutes, 1.0)


def _clamp(value: float, lower: float = 0.0, upper: float = 10.0) -> float:
    return max(lower, min(upper, value))


def _scale(value: float, ceiling: float, upper: float = 10.0) -> float:
    if ceiling <= 0:
        return 0.0
    return _clamp(value / ceiling * upper, 0.0, upper)


def _pass_security(pass_completion_pct: float) -> float:
    return _clamp((pass_completion_pct - 55.0) / 40.0 * 10.0)


ROLE_ADVANCED_WEIGHTS = {
    "goalkeeper": {
        "goalkeeping_value": 0.62,
        "ball_security": 0.22,
        "defensive_disruption": 0.16,
    },
    "center_back": {
        "defensive_disruption": 0.44,
        "ball_security": 0.24,
        "progression_value": 0.22,
        "attacking_involvement": 0.10,
    },
    "full_back": {
        "progression_value": 0.34,
        "defensive_disruption": 0.30,
        "ball_security": 0.18,
        "attacking_involvement": 0.18,
    },
    "defensive_midfielder": {
        "defensive_disruption": 0.34,
        "progression_value": 0.30,
        "ball_security": 0.24,
        "attacking_involvement": 0.12,
    },
    "central_midfielder": {
        "progression_value": 0.36,
        "ball_security": 0.26,
        "defensive_disruption": 0.20,
        "attacking_involvement": 0.18,
    },
    "attacking_midfielder": {
        "attacking_involvement": 0.38,
        "progression_value": 0.34,
        "ball_security": 0.16,
        "defensive_disruption": 0.12,
    },
    "winger": {
        "attacking_involvement": 0.36,
        "progression_value": 0.38,
        "ball_security": 0.12,
        "defensive_disruption": 0.14,
    },
    "forward": {
        "attacking_involvement": 0.56,
        "progression_value": 0.13,
        "defensive_disruption": 0.18,
        "ball_security": 0.13,
    },
    "unknown": {
        "attacking_involvement": 0.25,
        "progression_value": 0.25,
        "defensive_disruption": 0.25,
        "ball_security": 0.25,
    },
}


def calculate_advanced_metrics(stats: PlayerMatchStats) -> AdvancedPlayerMetrics:
    minutes = max(stats.minutes, 1.0)
    goals_p90 = _per90(stats.goals, minutes)
    assists_p90 = _per90(stats.assists, minutes)
    xg_p90 = _per90(stats.xg, minutes)
    shots_p90 = _per90(stats.shots, minutes)
    chances_p90 = _per90(stats.chance_creation, minutes)
    prog_passes_p90 = _per90(stats.progressive_passes, minutes)
    prog_carries_p90 = _per90(stats.progressive_carries, minutes)
    carries_p90 = _per90(stats.carries, minutes)
    dribbles_p90 = _per90(stats.successful_dribbles, minutes)
    interceptions_p90 = _per90(stats.interceptions, minutes)
    tackles_p90 = _per90(stats.tackles, minutes)
    clearances_p90 = _per90(stats.clearances, minutes)
    aerials_p90 = _per90(stats.aerials_won, minutes)
    pressures_p90 = _per90(stats.pressures, minutes)
    recoveries_p90 = _per90(stats.ball_recoveries, minutes)
    saves_p90 = _per90(stats.saves, minutes)
    claims_p90 = _per90(stats.claims, minutes)

    attacking_raw = (
        goals_p90 * 1.35
        + assists_p90 * 1.05
        + xg_p90 * 1.25
        + shots_p90 * 0.19
        + chances_p90 * 0.36
    )
    progression_raw = (
        prog_passes_p90 * 0.34
        + prog_carries_p90 * 0.54
        + dribbles_p90 * 0.40
        + carries_p90 * 0.06
    )
    defensive_raw = (
        interceptions_p90 * 0.52
        + tackles_p90 * 0.48
        + clearances_p90 * 0.25
        + aerials_p90 * 0.33
        + pressures_p90 * 0.09
        + recoveries_p90 * 0.31
    )
    goalkeeping_raw = saves_p90 * 0.9 + claims_p90 * 0.45 + _pass_security(stats.pass_completion_pct) * 0.08

    attacking_involvement = round(_scale(attacking_raw, 4.2), 2)
    progression_value = round(_scale(progression_raw, 5.3), 2)
    defensive_disruption = round(_scale(defensive_raw, 5.4), 2)
    goalkeeping_value = round(_scale(goalkeeping_raw, 5.0), 2)
    ball_security = round(
        _clamp(_pass_security(stats.pass_completion_pct) * 0.72 + _scale(carries_p90, 16.0) * 0.28),
        2,
    )
    two_way_value = round((min(attacking_involvement, defensive_disruption) * 0.45) + (progression_value * 0.55), 2)
    xg_efficiency = round(_clamp((stats.goals - stats.xg) * 2.0 + 5.0, 0.0, 10.0), 2)
    usage_rate = round(
        _clamp(
            _scale(shots_p90, 5.0) * 0.28
            + _scale(chances_p90, 5.0) * 0.28
            + _scale(prog_passes_p90 + prog_carries_p90, 13.0) * 0.28
            + _scale(pressures_p90 + tackles_p90, 18.0) * 0.16
        ),
        2,
    )

    components = {
        "attacking_involvement": attacking_involvement,
        "progression_value": progression_value,
        "ball_security": ball_security,
        "defensive_disruption": defensive_disruption,
        "goalkeeping_value": goalkeeping_value,
    }
    weights = ROLE_ADVANCED_WEIGHTS.get(stats.role_group, ROLE_ADVANCED_WEIGHTS["unknown"])
    role_fit_score = round(sum(components[key] * weight for key, weight in weights.items()), 2)
    per90_summary = {
        "goals": round(goals_p90, 3),
        "assists": round(assists_p90, 3),
        "xg": round(xg_p90, 3),
        "shots": round(shots_p90, 3),
        "chance_creation": round(chances_p90, 3),
        "progressive_passes": round(prog_passes_p90, 3),
        "progressive_carries": round(prog_carries_p90, 3),
        "successful_dribbles": round(dribbles_p90, 3),
        "interceptions": round(interceptions_p90, 3),
        "tackles": round(tackles_p90, 3),
        "pressures": round(pressures_p90, 3),
        "recoveries": round(recoveries_p90, 3),
    }
    return AdvancedPlayerMetrics(
        match_id=stats.match_id,
        player=stats.player,
        team=stats.team,
        opponent=stats.opponent,
        role_group=stats.role_group,
        minutes=stats.minutes,
        attacking_involvement=attacking_involvement,
        progression_value=progression_value,
        ball_security=ball_security,
        defensive_disruption=defensive_disruption,
        goalkeeping_value=goalkeeping_value,
        two_way_value=two_way_value,
        xg_efficiency=xg_efficiency,
        usage_rate=usage_rate,
        role_fit_score=role_fit_score,
        per90_summary_json=json.dumps(per90_summary, sort_keys=True),
    )


def calculate_many(rows: list[PlayerMatchStats]) -> list[AdvancedPlayerMetrics]:
    return [calculate_advanced_metrics(row) for row in rows]


def advanced_metric_to_row(metrics: AdvancedPlayerMetrics) -> dict[str, object]:
    return asdict(metrics)

