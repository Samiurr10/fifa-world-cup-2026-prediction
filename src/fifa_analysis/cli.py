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
from fifa_analysis.database import (
    connect,
    fetch_game_ratings,
    fetch_overall_ratings,
    fetch_player_stats,
    init_db,
    insert_rating_validation,
    upsert_game_ratings,
    upsert_matches,
    upsert_overall_ratings,
    upsert_player_stats,
)
from fifa_analysis.ratings import (
    build_overall_ratings,
    game_rating_to_row,
    overall_rating_to_row,
    rate_player_game,
)
from fifa_analysis.reports import generate_match_report
from fifa_analysis.statsbomb import statsbomb_files_to_player_stats
from fifa_analysis.validation import compare_external_ratings, rating_coverage, read_external_ratings


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


def command_init_db(args: argparse.Namespace) -> None:
    init_db(args.db)
    print(f"Initialized rating database at {args.db}")


def command_load_matches(args: argparse.Namespace) -> None:
    init_db(args.db)
    matches = read_match_records(args.matches)
    with connect(args.db) as conn:
        count = upsert_matches(conn, matches)
    print(f"Loaded {count} matches into {args.db}")


def command_load_player_stats(args: argparse.Namespace) -> None:
    init_db(args.db)
    rows = read_player_match_stats(args.player_stats)
    with connect(args.db) as conn:
        count = upsert_player_stats(conn, rows)
    print(f"Loaded {count} player-game stat rows into {args.db}")


def command_rate_db(args: argparse.Namespace) -> None:
    init_db(args.db)
    with connect(args.db) as conn:
        player_stats_rows = fetch_player_stats(conn)
        ratings = [rate_player_game(row) for row in player_stats_rows]
        overall = build_overall_ratings(ratings)
        game_count = upsert_game_ratings(conn, ratings)
        overall_count = upsert_overall_ratings(conn, overall)
    print(f"Rated {game_count} player games and {overall_count} overall players in {args.db}")


def command_export_game_ratings(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        rows = [game_rating_to_row(row) for row in fetch_game_ratings(conn)]
    write_csv_rows(args.output, rows)
    print(f"Exported {len(rows)} player-game ratings to {args.output}")


def command_export_overall_ratings(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        rows = [overall_rating_to_row(row) for row in fetch_overall_ratings(conn)]
    write_csv_rows(args.output, rows)
    print(f"Exported {len(rows)} overall player ratings to {args.output}")


def command_validate_ratings(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        generated = fetch_game_ratings(conn)
        result = compare_external_ratings(generated, read_external_ratings(args.external_ratings))
        if args.store:
            insert_rating_validation(
                conn,
                source=str(args.external_ratings),
                sample_size=int(result["sample_size"]),
                mae=result["mae"],
                correlation=result["correlation"],
                within_half_point_rate=result["within_half_point_rate"],
            )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote rating validation metrics to {args.output}")
    else:
        print(json.dumps(result, indent=2))


def command_rating_coverage(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        result = rating_coverage(fetch_game_ratings(conn))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote rating coverage report to {args.output}")
    else:
        print(json.dumps(result, indent=2))


def command_statsbomb_player_stats(args: argparse.Namespace) -> None:
    rows = statsbomb_files_to_player_stats(
        events_path=args.events,
        lineups_path=args.lineups,
        match_id=args.match_id,
        home_team=args.home,
        away_team=args.away,
    )
    write_csv_rows(args.output, [row.__dict__ for row in rows])
    print(f"Wrote {len(rows)} StatsBomb-normalized player stat rows to {args.output}")


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

    init_database = subparsers.add_parser("init-db", help="Create the SQLite rating database.")
    init_database.add_argument("--db", type=Path, default=Path("data/db/worldcup_ratings.sqlite"))
    init_database.set_defaults(func=command_init_db)

    load_matches = subparsers.add_parser("load-matches", help="Load normalized matches into SQLite.")
    load_matches.add_argument("--db", type=Path, default=Path("data/db/worldcup_ratings.sqlite"))
    load_matches.add_argument("--matches", type=Path, required=True)
    load_matches.set_defaults(func=command_load_matches)

    load_player_stats = subparsers.add_parser(
        "load-player-stats", help="Load player-game stat rows into SQLite."
    )
    load_player_stats.add_argument("--db", type=Path, default=Path("data/db/worldcup_ratings.sqlite"))
    load_player_stats.add_argument("--player-stats", type=Path, required=True)
    load_player_stats.set_defaults(func=command_load_player_stats)

    rate_db = subparsers.add_parser("rate-db", help="Compute player game and overall ratings.")
    rate_db.add_argument("--db", type=Path, default=Path("data/db/worldcup_ratings.sqlite"))
    rate_db.set_defaults(func=command_rate_db)

    export_game = subparsers.add_parser(
        "export-game-ratings", help="Export player-game ratings from SQLite."
    )
    export_game.add_argument("--db", type=Path, default=Path("data/db/worldcup_ratings.sqlite"))
    export_game.add_argument("--output", type=Path, default=Path("reports/player_game_ratings.csv"))
    export_game.set_defaults(func=command_export_game_ratings)

    export_overall = subparsers.add_parser(
        "export-overall-ratings", help="Export overall player ratings from SQLite."
    )
    export_overall.add_argument("--db", type=Path, default=Path("data/db/worldcup_ratings.sqlite"))
    export_overall.add_argument("--output", type=Path, default=Path("reports/player_overall_ratings.csv"))
    export_overall.set_defaults(func=command_export_overall_ratings)

    validate_ratings = subparsers.add_parser(
        "validate-ratings", help="Compare generated ratings against an external ratings CSV."
    )
    validate_ratings.add_argument("--db", type=Path, default=Path("data/db/worldcup_ratings.sqlite"))
    validate_ratings.add_argument("--external-ratings", type=Path, required=True)
    validate_ratings.add_argument("--output", type=Path)
    validate_ratings.add_argument("--store", action="store_true")
    validate_ratings.set_defaults(func=command_validate_ratings)

    coverage = subparsers.add_parser(
        "rating-coverage", help="Summarize how many player-games and players are rated."
    )
    coverage.add_argument("--db", type=Path, default=Path("data/db/worldcup_ratings.sqlite"))
    coverage.add_argument("--output", type=Path)
    coverage.set_defaults(func=command_rating_coverage)

    statsbomb_stats = subparsers.add_parser(
        "statsbomb-player-stats",
        help="Convert StatsBomb event and optional lineup JSON into player-game stats CSV.",
    )
    statsbomb_stats.add_argument("--events", type=Path, required=True)
    statsbomb_stats.add_argument("--lineups", type=Path)
    statsbomb_stats.add_argument("--match-id", required=True)
    statsbomb_stats.add_argument("--home", required=True)
    statsbomb_stats.add_argument("--away", required=True)
    statsbomb_stats.add_argument("--output", type=Path, default=Path("reports/statsbomb_player_stats.csv"))
    statsbomb_stats.set_defaults(func=command_statsbomb_player_stats)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
