"""Role-aware player game and overall rating engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from fifa_analysis.advanced_metrics import calculate_advanced_metrics
from fifa_analysis.schemas import PlayerMatchStats


@dataclass(frozen=True)
class PlayerGameRating:
    match_id: str
    player: str
    team: str
    opponent: str
    position: str
    role_group: str
    rating: float
    confidence: str
    minutes: float
    attacking_score: float
    possession_score: float
    defensive_score: float
    goalkeeping_score: float
    reasons: list[str]


@dataclass(frozen=True)
class PlayerOverallRating:
    player: str
    team: str
    role_group: str
    matches: int
    minutes: float
    average_rating: float
    weighted_rating: float
    best_rating: float
    latest_rating: float
    confidence: str


def _cap(value: float, ceiling: float) -> float:
    if ceiling <= 0:
        return 0.0
    return max(0.0, min(1.0, value / ceiling))


def _per90(value: float, minutes: float) -> float:
    return value * 90.0 / max(minutes, 1.0)


def _pass_quality(pass_completion_pct: float) -> float:
    return max(0.0, min(1.0, (pass_completion_pct - 60.0) / 35.0))


def _minutes_confidence(minutes: float, match_count: int = 1) -> str:
    if match_count >= 5 and minutes >= 300:
        return "high"
    if minutes >= 60 or match_count >= 3:
        return "medium"
    return "low"


def score_components(stats: PlayerMatchStats) -> dict[str, float]:
    minutes = max(stats.minutes, 1.0)
    attacking = (
        _cap(_per90(stats.goals, minutes), 1.5) * 0.26
        + _cap(_per90(stats.assists, minutes), 1.0) * 0.17
        + _cap(_per90(stats.xg, minutes), 0.9) * 0.24
        + _cap(_per90(stats.shots, minutes), 5.5) * 0.13
        + _cap(_per90(stats.chance_creation, minutes), 4.5) * 0.20
    )
    possession = (
        _cap(_per90(stats.progressive_passes, minutes), 10.0) * 0.32
        + _cap(_per90(stats.progressive_carries, minutes), 8.0) * 0.27
        + _cap(_per90(stats.successful_dribbles, minutes), 5.0) * 0.18
        + _cap(_per90(stats.carries, minutes), 14.0) * 0.10
        + _pass_quality(stats.pass_completion_pct) * 0.13
    )
    defensive = (
        _cap(_per90(stats.interceptions, minutes), 4.5) * 0.19
        + _cap(_per90(stats.tackles, minutes), 5.0) * 0.18
        + _cap(_per90(stats.clearances, minutes), 9.0) * 0.18
        + _cap(_per90(stats.aerials_won, minutes), 6.0) * 0.15
        + _cap(_per90(stats.pressures, minutes), 16.0) * 0.12
        + _cap(_per90(stats.ball_recoveries, minutes), 9.0) * 0.18
    )
    goalkeeping = (
        _cap(_per90(stats.saves, minutes), 7.0) * 0.55
        + _cap(_per90(stats.claims, minutes), 4.0) * 0.20
        + _pass_quality(stats.pass_completion_pct) * 0.25
    )
    return {
        "attacking_score": round(attacking, 4),
        "possession_score": round(possession, 4),
        "defensive_score": round(defensive, 4),
        "goalkeeping_score": round(goalkeeping, 4),
    }


ROLE_COMPONENT_WEIGHTS = {
    "goalkeeper": {
        "goalkeeping_score": 0.72,
        "defensive_score": 0.10,
        "possession_score": 0.18,
    },
    "center_back": {
        "defensive_score": 0.58,
        "possession_score": 0.30,
        "attacking_score": 0.12,
    },
    "full_back": {
        "defensive_score": 0.35,
        "possession_score": 0.43,
        "attacking_score": 0.22,
    },
    "defensive_midfielder": {
        "defensive_score": 0.38,
        "possession_score": 0.46,
        "attacking_score": 0.16,
    },
    "central_midfielder": {
        "possession_score": 0.52,
        "defensive_score": 0.23,
        "attacking_score": 0.25,
    },
    "attacking_midfielder": {
        "attacking_score": 0.47,
        "possession_score": 0.42,
        "defensive_score": 0.11,
    },
    "winger": {
        "attacking_score": 0.48,
        "possession_score": 0.40,
        "defensive_score": 0.12,
    },
    "forward": {
        "attacking_score": 0.68,
        "possession_score": 0.17,
        "defensive_score": 0.15,
    },
    "unknown": {
        "attacking_score": 0.34,
        "possession_score": 0.33,
        "defensive_score": 0.33,
    },
}


def rate_player_game(stats: PlayerMatchStats) -> PlayerGameRating:
    components = score_components(stats)
    advanced = calculate_advanced_metrics(stats)
    weights = ROLE_COMPONENT_WEIGHTS.get(stats.role_group, ROLE_COMPONENT_WEIGHTS["unknown"])
    role_score = sum(components[key] * weight for key, weight in weights.items())
    advanced_anchor = advanced.role_fit_score / 10.0
    minutes_factor = 0.88 + min(0.12, stats.minutes / 750.0)
    contribution_anchor = min(1.0, max(0.0, stats.contribution_score / 100.0))
    blended = role_score * 0.58 + contribution_anchor * 0.20 + advanced_anchor * 0.22
    rating = 5.4 + (blended * 4.25 * minutes_factor)

    if stats.goals:
        rating += min(0.45, stats.goals * 0.16)
    if stats.assists:
        rating += min(0.32, stats.assists * 0.12)
    if stats.minutes < 30:
        rating = min(rating, 7.2)

    rating = round(max(1.0, min(10.0, rating)), 2)
    dominant_component = max(components, key=components.get)
    reasons = [
        f"{stats.role_group} weighted most toward {', '.join(weights.keys())}.",
        f"Strongest component: {dominant_component.replace('_', ' ')} {components[dominant_component]:.2f}.",
        f"Advanced role-fit score: {advanced.role_fit_score:.2f}/10.",
    ]
    if stats.minutes < 60:
        reasons.append("Minutes reduced rating confidence.")

    return PlayerGameRating(
        match_id=stats.match_id,
        player=stats.player,
        team=stats.team,
        opponent=stats.opponent,
        position=stats.position,
        role_group=stats.role_group,
        rating=rating,
        confidence=_minutes_confidence(stats.minutes),
        minutes=stats.minutes,
        reasons=reasons,
        **components,
    )


def build_overall_ratings(game_ratings: list[PlayerGameRating]) -> list[PlayerOverallRating]:
    grouped: dict[tuple[str, str], list[PlayerGameRating]] = {}
    for rating in game_ratings:
        grouped.setdefault((rating.player, rating.team), []).append(rating)

    overall: list[PlayerOverallRating] = []
    for (player, team), rows in grouped.items():
        rows = sorted(rows, key=lambda row: row.match_id)
        minutes = sum(row.minutes for row in rows)
        average = sum(row.rating for row in rows) / len(rows)
        weighted = sum(row.rating * max(row.minutes, 1.0) for row in rows) / max(minutes, 1.0)
        confidence = _minutes_confidence(minutes, len(rows))
        overall.append(
            PlayerOverallRating(
                player=player,
                team=team,
                role_group=rows[-1].role_group,
                matches=len(rows),
                minutes=round(minutes, 1),
                average_rating=round(average, 2),
                weighted_rating=round(weighted, 2),
                best_rating=max(row.rating for row in rows),
                latest_rating=rows[-1].rating,
                confidence=confidence,
            )
        )
    return sorted(overall, key=lambda row: row.weighted_rating, reverse=True)


def game_rating_to_row(rating: PlayerGameRating) -> dict[str, object]:
    row = asdict(rating)
    row["reasons"] = " | ".join(rating.reasons)
    return row


def overall_rating_to_row(rating: PlayerOverallRating) -> dict[str, object]:
    return asdict(rating)
