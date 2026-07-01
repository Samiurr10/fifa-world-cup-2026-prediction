"""Grounded report generation from computed prediction facts."""

from __future__ import annotations

from fifa_analysis.schemas import MatchPrediction, PlayerImpact


def confidence_note(confidence: str) -> str:
    if confidence == "high":
        return "Confidence is high because both sides have enough recent free-data coverage."
    if confidence == "medium":
        return "Confidence is medium because the model has some recent data but not a complete player picture."
    return "Confidence is low because free-data coverage is incomplete; treat this as a cautious forecast."


def generate_match_report(prediction: MatchPrediction, impacts: list[PlayerImpact] | None = None) -> str:
    favorite = max(
        [
            ("home win", prediction.home_win, prediction.home_team),
            ("draw", prediction.draw, "Draw"),
            ("away win", prediction.away_win, prediction.away_team),
        ],
        key=lambda item: item[1],
    )
    lines = [
        f"# {prediction.home_team} vs {prediction.away_team} prediction",
        "",
        "## Score forecast",
        f"- Expected goals: {prediction.home_team} {prediction.expected_home_goals:.2f}, "
        f"{prediction.away_team} {prediction.expected_away_goals:.2f}.",
        f"- Most likely outcome: {favorite[2]} ({favorite[1]:.1%}).",
        f"- Win/draw/loss: {prediction.home_win:.1%} / {prediction.draw:.1%} / "
        f"{prediction.away_win:.1%}.",
        "- Top scorelines: "
        + ", ".join(
            f"{row['score']} ({row['probability']:.1%})" for row in prediction.top_scorelines[:5]
        )
        + ".",
        f"- {confidence_note(prediction.confidence)}",
        "",
        "## Model reasons",
    ]
    lines.extend(f"- {reason}" for reason in prediction.reasons)

    if impacts:
        lines.extend(["", "## Player impact"])
        for impact in impacts[:5]:
            lines.append(
                f"- {impact.player} ({impact.team}): {impact.impact_score:.1f} impact score, "
                f"{impact.role_group}, {impact.confidence} confidence."
            )
    lines.extend(
        [
            "",
            "## Grounding rule",
            "This report only summarizes computed model inputs and outputs. It does not invent injuries, "
            "lineups, or unavailable player statistics.",
        ]
    )
    return "\n".join(lines)
