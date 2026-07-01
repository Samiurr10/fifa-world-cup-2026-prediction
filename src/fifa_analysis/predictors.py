"""Accuracy-first scoreline, outcome, and player-impact predictors."""

from __future__ import annotations

import math
from dataclasses import asdict

from fifa_analysis.features import (
    build_team_profile,
    opponent_weakness_against_role,
    player_recent_rows,
    player_role_form_score,
)
from fifa_analysis.schemas import MatchPrediction, PlayerImpact, PlayerMatchStats, TeamMatchStats


def poisson_probability(lam: float, goals: int) -> float:
    lam = max(0.05, lam)
    return math.exp(-lam) * (lam**goals) / math.factorial(goals)


def scoreline_distribution(home_xg: float, away_xg: float, max_goals: int = 7) -> list[dict[str, float]]:
    scorelines: list[dict[str, float]] = []
    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            probability = poisson_probability(home_xg, home_goals) * poisson_probability(
                away_xg, away_goals
            )
            scorelines.append(
                {
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "score": f"{home_goals}-{away_goals}",
                    "probability": probability,
                }
            )
    total = sum(row["probability"] for row in scorelines)
    return sorted(
        [{**row, "probability": round(row["probability"] / total, 4)} for row in scorelines],
        key=lambda row: row["probability"],
        reverse=True,
    )


def outcome_from_scorelines(scorelines: list[dict[str, float]]) -> dict[str, float]:
    home_win = sum(row["probability"] for row in scorelines if row["home_goals"] > row["away_goals"])
    draw = sum(row["probability"] for row in scorelines if row["home_goals"] == row["away_goals"])
    away_win = sum(row["probability"] for row in scorelines if row["away_goals"] > row["home_goals"])
    home = round(home_win, 3)
    draw_probability = round(draw, 3)
    away = round(1.0 - home - draw_probability, 3)
    return {"home_win": home, "draw": draw_probability, "away_win": away}


def estimate_expected_goals(
    home_team: str,
    away_team: str,
    team_rows: list[TeamMatchStats],
    host_advantage: float = 0.12,
) -> tuple[float, float, list[str], str]:
    home = build_team_profile(home_team, team_rows)
    away = build_team_profile(away_team, team_rows)
    average_xg = 1.35

    home_attack = (home.attack_xg * 0.58) + (home.goals_for * 0.24) + (home.shots_for * 0.018)
    away_defense = (away.defense_xg * 0.65) + (away.goals_against * 0.25) + (
        away.shots_against * 0.012
    )
    away_attack = (away.attack_xg * 0.58) + (away.goals_for * 0.24) + (away.shots_for * 0.018)
    home_defense = (home.defense_xg * 0.65) + (home.goals_against * 0.25) + (
        home.shots_against * 0.012
    )

    form_delta = (home.form_points - away.form_points) * 0.045
    home_xg = max(0.15, min(4.5, average_xg * 0.18 + home_attack * 0.48 + away_defense * 0.34))
    away_xg = max(0.15, min(4.5, average_xg * 0.18 + away_attack * 0.48 + home_defense * 0.34))
    home_xg += host_advantage + form_delta
    away_xg -= form_delta
    home_xg = round(max(0.15, home_xg), 3)
    away_xg = round(max(0.15, away_xg), 3)

    reasons = [
        f"{home_team} attack profile: {home.attack_xg:.2f} recent xG, {home.shots_for:.1f} shots.",
        f"{away_team} defense profile: {away.defense_xg:.2f} xG conceded, {away.shots_against:.1f} shots allowed.",
        f"{away_team} attack profile: {away.attack_xg:.2f} recent xG, {away.shots_for:.1f} shots.",
        f"Recent form points: {home_team} {home.form_points:.2f}, {away_team} {away.form_points:.2f}.",
    ]
    sample_size = min(home.matches, away.matches)
    if sample_size >= 5:
        confidence = "high"
    elif sample_size >= 3:
        confidence = "medium"
    else:
        confidence = "low"
        reasons.append("Confidence reduced because free data has limited recent matches for one side.")
    return home_xg, away_xg, reasons, confidence


def predict_match(
    home_team: str,
    away_team: str,
    team_rows: list[TeamMatchStats],
    top_n: int = 5,
) -> MatchPrediction:
    home_xg, away_xg, reasons, confidence = estimate_expected_goals(home_team, away_team, team_rows)
    scorelines = scoreline_distribution(home_xg, away_xg)
    outcomes = outcome_from_scorelines(scorelines)
    return MatchPrediction(
        home_team=home_team,
        away_team=away_team,
        expected_home_goals=home_xg,
        expected_away_goals=away_xg,
        home_win=outcomes["home_win"],
        draw=outcomes["draw"],
        away_win=outcomes["away_win"],
        top_scorelines=scorelines[:top_n],
        confidence=confidence,
        reasons=reasons,
    )


def rank_player_impact(
    team: str,
    opponent: str,
    player_rows: list[PlayerMatchStats],
    team_rows: list[TeamMatchStats],
    top_n: int = 10,
) -> list[PlayerImpact]:
    grouped = player_recent_rows(player_rows, team=team, opponent=opponent)
    impacts: list[PlayerImpact] = []
    for player, rows in grouped.items():
        role_group = rows[-1].role_group
        form_score = player_role_form_score(rows)
        matchup = opponent_weakness_against_role(opponent, role_group, team_rows)
        match_count = len(rows)
        confidence = "high" if match_count >= 5 else "medium" if match_count >= 3 else "low"
        confidence_multiplier = {"high": 1.0, "medium": 0.9, "low": 0.72}[confidence]
        base = rows[-1].contribution_score or form_score
        impact_score = round((base * 0.42 + form_score * 0.58) * matchup * confidence_multiplier, 2)
        reasons = [
            f"{role_group} form score {form_score:.2f} from {match_count} available matches.",
            f"Opponent matchup multiplier {matchup:.2f} against {opponent}.",
        ]
        if confidence == "low":
            reasons.append("Confidence reduced because player-level free data is sparse.")
        impacts.append(
            PlayerImpact(
                player=player,
                team=team,
                opponent=opponent,
                role_group=role_group,
                impact_score=impact_score,
                form_score=form_score,
                matchup_adjustment=round(matchup, 3),
                confidence=confidence,
                reasons=reasons,
            )
        )
    return sorted(impacts, key=lambda row: row.impact_score, reverse=True)[:top_n]


def prediction_to_dict(prediction: MatchPrediction) -> dict[str, object]:
    return asdict(prediction)


def impact_to_rows(impacts: list[PlayerImpact]) -> list[dict[str, object]]:
    rows = []
    for impact in impacts:
        row = asdict(impact)
        row["reasons"] = " | ".join(impact.reasons)
        rows.append(row)
    return rows
