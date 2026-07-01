"""Command-line interface for the FIFA analysis toolkit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fifa_analysis.connectors import (
    load_json,
    match_records_to_rows,
    normalize_openfootball_matches,
    normalize_worldcup2026_api,
    read_match_records,
    write_csv_rows,
)
from fifa_analysis.evaluation import backtest_predictions
from fifa_analysis.features import read_player_match_stats, read_team_match_stats
from fifa_analysis.metrics import load_events, player_metrics, score_contributions, team_summary
from fifa_analysis.models import baseline_match_prediction, evaluate_baseline
from fifa_analysis.predictors import impact_to_rows, predict_match, prediction_to_dict, rank_player_impact
from fifa_analysis.reports import generate_match_report


def command_metrics(args: argparse.Namespace) -> None:
    events = load_events(args.events)
    rows = score_contributions(player_metrics(events))
    write_csv_rows(args.output, rows)
    print(f"Wrote {len(rows)} player rows to {args.output}")


def command_team_summary(args: argparse.Namespace) -> None:
    events = load_events(args.events)
    rows = team_summary(score_contributions(player_metrics(events)))
    write_csv_rows(args.output, rows)
    print(f"Wrote {len(rows)} team rows to {args.output}")


def command_predict(args: argparse.Namespace) -> None:
    prediction = baseline_match_prediction(
        home_attack=args.home_attack,
        home_defense=args.home_defense,
        away_attack=args.away_attack,
        away_defense=args.away_defense,
        home_advantage=args.home_advantage,
    )
    print(json.dumps(prediction.__dict__, indent=2))


def command_evaluate(args: argparse.Namespace) -> None:
    print(json.dumps(evaluate_baseline(args.matches), indent=2))


def command_ingest_openfootball(args: argparse.Namespace) -> None:
    payload = load_json(args.input)
    matches = normalize_openfootball_matches(payload)
    write_csv_rows(args.output, match_records_to_rows(matches))
    print(f"Wrote {len(matches)} normalized matches to {args.output}")


def command_ingest_worldcup2026(args: argparse.Namespace) -> None:
    payload = load_json(args.input)
    matches = normalize_worldcup2026_api(payload)
    write_csv_rows(args.output, match_records_to_rows(matches))
    print(f"Wrote {len(matches)} normalized matches to {args.output}")


def command_predict_match(args: argparse.Namespace) -> None:
    team_rows = read_team_match_stats(args.team_stats)
    prediction = predict_match(args.home, args.away, team_rows, top_n=args.top)
    output = prediction_to_dict(prediction)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"Wrote match prediction to {args.output}")
    else:
        print(json.dumps(output, indent=2))


def command_player_impact(args: argparse.Namespace) -> None:
    team_rows = read_team_match_stats(args.team_stats)
    player_rows = read_player_match_stats(args.player_stats)
    impacts = rank_player_impact(args.team, args.opponent, player_rows, team_rows, top_n=args.top)
    rows = impact_to_rows(impacts)
    if args.output:
        write_csv_rows(args.output, rows)
        print(f"Wrote {len(rows)} player impact rows to {args.output}")
    else:
        print(json.dumps(rows, indent=2))


def command_match_report(args: argparse.Namespace) -> None:
    team_rows = read_team_match_stats(args.team_stats)
    player_rows = read_player_match_stats(args.player_stats) if args.player_stats else []
    prediction = predict_match(args.home, args.away, team_rows, top_n=args.top)
    impacts = []
    if player_rows:
        impacts.extend(rank_player_impact(args.home, args.away, player_rows, team_rows, top_n=args.top))
        impacts.extend(rank_player_impact(args.away, args.home, player_rows, team_rows, top_n=args.top))
        impacts = sorted(impacts, key=lambda impact: impact.impact_score, reverse=True)[: args.top]
    report = generate_match_report(prediction, impacts)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Wrote grounded match report to {args.output}")
    else:
        print(report)


def command_backtest(args: argparse.Namespace) -> None:
    matches = read_match_records(args.matches)
    team_rows = read_team_match_stats(args.team_stats)
    result = backtest_predictions(matches, team_rows)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote backtest metrics to {args.output}")
    else:
        print(json.dumps(result, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="FIFA World Cup player contribution and prediction analysis."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    metrics = subparsers.add_parser("metrics", help="Build role-aware player metrics from events.")
    metrics.add_argument("--events", type=Path, required=True, help="StatsBomb-style event JSON file.")
    metrics.add_argument("--output", type=Path, default=Path("reports/player_metrics.csv"))
    metrics.set_defaults(func=command_metrics)

    team = subparsers.add_parser("team-summary", help="Aggregate player metrics by team.")
    team.add_argument("--events", type=Path, required=True, help="StatsBomb-style event JSON file.")
    team.add_argument("--output", type=Path, default=Path("reports/team_summary.csv"))
    team.set_defaults(func=command_team_summary)

    predict = subparsers.add_parser("predict", help="Run the legacy baseline comparator.")
    predict.add_argument("--home-attack", type=float, required=True)
    predict.add_argument("--home-defense", type=float, required=True)
    predict.add_argument("--away-attack", type=float, required=True)
    predict.add_argument("--away-defense", type=float, required=True)
    predict.add_argument("--home-advantage", type=float, default=0.18)
    predict.set_defaults(func=command_predict)

    evaluate = subparsers.add_parser("evaluate", help="Evaluate the baseline on match features CSV.")
    evaluate.add_argument("--matches", type=Path, required=True)
    evaluate.set_defaults(func=command_evaluate)

    openfootball = subparsers.add_parser(
        "ingest-openfootball", help="Normalize openfootball/worldcup.json data."
    )
    openfootball.add_argument("--input", type=Path, required=True)
    openfootball.add_argument("--output", type=Path, default=Path("reports/matches.csv"))
    openfootball.set_defaults(func=command_ingest_openfootball)

    worldcup2026 = subparsers.add_parser(
        "ingest-worldcup2026", help="Normalize a worldcup2026 /get/games JSON response."
    )
    worldcup2026.add_argument("--input", type=Path, required=True)
    worldcup2026.add_argument("--output", type=Path, default=Path("reports/matches.csv"))
    worldcup2026.set_defaults(func=command_ingest_worldcup2026)

    match = subparsers.add_parser(
        "predict-match", help="Predict expected goals, top scorelines, and win/draw/loss."
    )
    match.add_argument("--home", required=True)
    match.add_argument("--away", required=True)
    match.add_argument("--team-stats", type=Path, required=True)
    match.add_argument("--top", type=int, default=5)
    match.add_argument("--output", type=Path)
    match.set_defaults(func=command_predict_match)

    impact = subparsers.add_parser("player-impact", help="Rank role-aware player impact.")
    impact.add_argument("--team", required=True)
    impact.add_argument("--opponent", required=True)
    impact.add_argument("--team-stats", type=Path, required=True)
    impact.add_argument("--player-stats", type=Path, required=True)
    impact.add_argument("--top", type=int, default=10)
    impact.add_argument("--output", type=Path)
    impact.set_defaults(func=command_player_impact)

    report = subparsers.add_parser(
        "match-report", help="Generate a grounded AI-style match report from computed facts."
    )
    report.add_argument("--home", required=True)
    report.add_argument("--away", required=True)
    report.add_argument("--team-stats", type=Path, required=True)
    report.add_argument("--player-stats", type=Path)
    report.add_argument("--top", type=int, default=5)
    report.add_argument("--output", type=Path)
    report.set_defaults(func=command_match_report)

    backtest = subparsers.add_parser(
        "backtest", help="Evaluate scoreline and outcome predictions against finished matches."
    )
    backtest.add_argument("--matches", type=Path, required=True)
    backtest.add_argument("--team-stats", type=Path, required=True)
    backtest.add_argument("--output", type=Path)
    backtest.set_defaults(func=command_backtest)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
