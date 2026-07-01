"""Position families and role-aware contribution weights."""

from __future__ import annotations

from dataclasses import dataclass


POSITION_GROUPS = {
    "goalkeeper": {"Goalkeeper"},
    "center_back": {"Center Back", "Left Center Back", "Right Center Back"},
    "full_back": {"Left Back", "Right Back", "Left Wing Back", "Right Wing Back"},
    "defensive_midfielder": {
        "Center Defensive Midfield",
        "Left Defensive Midfield",
        "Right Defensive Midfield",
    },
    "central_midfielder": {
        "Center Midfield",
        "Left Center Midfield",
        "Right Center Midfield",
    },
    "attacking_midfielder": {
        "Center Attacking Midfield",
        "Left Attacking Midfield",
        "Right Attacking Midfield",
    },
    "winger": {"Left Wing", "Right Wing", "Left Midfield", "Right Midfield"},
    "forward": {"Center Forward", "Left Center Forward", "Right Center Forward", "Striker"},
}


ROLE_WEIGHTS = {
    "goalkeeper": {
        "saves": 2.0,
        "claims": 1.0,
        "defensive_actions": 2.0,
        "interceptions": 1.6,
        "pass_completion_pct": 0.8,
        "progressive_passes": 0.4,
    },
    "center_back": {
        "defensive_actions": 1.8,
        "interceptions": 1.8,
        "clearances": 1.0,
        "aerials_won": 0.9,
        "progressive_passes": 0.8,
        "pass_completion_pct": 0.7,
        "carry_distance": 0.4,
    },
    "full_back": {
        "defensive_actions": 1.3,
        "interceptions": 1.2,
        "tackles": 1.0,
        "progressive_carries": 1.1,
        "progressive_passes": 1.0,
        "chance_creation": 0.9,
    },
    "defensive_midfielder": {
        "defensive_actions": 1.5,
        "interceptions": 1.6,
        "progressive_passes": 1.1,
        "pass_completion_pct": 0.8,
        "ball_recoveries": 1.2,
    },
    "central_midfielder": {
        "progressive_passes": 1.4,
        "pass_completion_pct": 0.9,
        "progressive_carries": 0.9,
        "chance_creation": 0.8,
        "defensive_actions": 0.8,
    },
    "attacking_midfielder": {
        "chance_creation": 1.7,
        "progressive_passes": 1.2,
        "progressive_carries": 1.1,
        "shots": 0.8,
        "goal_contributions": 1.5,
    },
    "winger": {
        "progressive_carries": 1.7,
        "successful_dribbles": 1.5,
        "chance_creation": 1.3,
        "shots": 0.8,
        "goal_contributions": 1.2,
    },
    "forward": {
        "shots": 1.3,
        "xg": 1.6,
        "goal_contributions": 1.8,
        "chance_creation": 0.8,
        "pressures": 0.8,
    },
    "unknown": {
        "goal_contributions": 1.0,
        "chance_creation": 1.0,
        "progressive_passes": 1.0,
        "progressive_carries": 1.0,
        "defensive_actions": 1.0,
    },
}


@dataclass(frozen=True)
class RoleProfile:
    """Resolved role metadata for one player position."""

    position: str
    group: str
    weights: dict[str, float]


def classify_position(position: str | None) -> str:
    """Map an event-data position label to a broader tactical role group."""

    if not position:
        return "unknown"
    for group, labels in POSITION_GROUPS.items():
        if position in labels:
            return group
    return "unknown"


def role_profile(position: str | None) -> RoleProfile:
    """Return the contribution weights for a position."""

    group = classify_position(position)
    return RoleProfile(position=position or "Unknown", group=group, weights=ROLE_WEIGHTS[group])
