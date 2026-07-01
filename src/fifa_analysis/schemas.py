"""Normalized records shared by data sources, features, and predictors."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MatchRecord:
    match_id: str
    date: str
    home_team: str
    away_team: str
    home_goals: int | None = None
    away_goals: int | None = None
    status: str = "scheduled"
    stage: str = ""
    group: str = ""
    source: str = ""

    @property
    def result(self) -> str | None:
        if self.home_goals is None or self.away_goals is None:
            return None
        if self.home_goals > self.away_goals:
            return "H"
        if self.away_goals > self.home_goals:
            return "A"
        return "D"


@dataclass(frozen=True)
class TeamMatchStats:
    match_id: str
    team: str
    opponent: str
    goals_for: float
    goals_against: float
    xg_for: float
    xg_against: float
    shots_for: float
    shots_against: float
    progressive_passes: float = 0.0
    progressive_carries: float = 0.0
    defensive_actions: float = 0.0
    venue: str = "neutral"
    date: str = ""
    source: str = ""


@dataclass(frozen=True)
class PlayerMatchStats:
    match_id: str
    player: str
    team: str
    opponent: str
    position: str
    role_group: str
    minutes: float = 90.0
    goals: float = 0.0
    assists: float = 0.0
    xg: float = 0.0
    shots: float = 0.0
    progressive_passes: float = 0.0
    progressive_carries: float = 0.0
    carries: float = 0.0
    successful_dribbles: float = 0.0
    interceptions: float = 0.0
    tackles: float = 0.0
    clearances: float = 0.0
    aerials_won: float = 0.0
    pressures: float = 0.0
    ball_recoveries: float = 0.0
    saves: float = 0.0
    claims: float = 0.0
    pass_completion_pct: float = 0.0
    chance_creation: float = 0.0
    contribution_score: float = 0.0
    source: str = ""


@dataclass(frozen=True)
class TeamProfile:
    team: str
    matches: int
    attack_xg: float
    defense_xg: float
    goals_for: float
    goals_against: float
    shots_for: float
    shots_against: float
    form_points: float
    progressive_strength: float
    defensive_activity: float


@dataclass(frozen=True)
class PlayerImpact:
    player: str
    team: str
    opponent: str
    role_group: str
    impact_score: float
    form_score: float
    matchup_adjustment: float
    confidence: str
    reasons: list[str]


@dataclass(frozen=True)
class MatchPrediction:
    home_team: str
    away_team: str
    expected_home_goals: float
    expected_away_goals: float
    home_win: float
    draw: float
    away_win: float
    top_scorelines: list[dict[str, Any]]
    confidence: str
    reasons: list[str]


def to_dict(record: Any) -> dict[str, Any]:
    return asdict(record)


def optional_int(value: Any) -> int | None:
    if value in (None, "", "null", "NULL", "None"):
        return None
    return int(float(value))


def optional_float(value: Any, default: float = 0.0) -> float:
    if value in (None, "", "null", "NULL", "None"):
        return default
    return float(value)

