"""Static visual dashboard generation for player ratings and predictions."""

from __future__ import annotations

import csv
import html
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def read_csv(path: str | Path) -> list[dict[str, str]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    with file_path.open(encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def read_json(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    with file_path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def number(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value: object, digits: int = 2) -> str:
    return f"{number(value):.{digits}f}"


def pct(value: object) -> str:
    return f"{number(value) * 100:.1f}%"


def confidence_class(value: object) -> str:
    text = str(value).lower()
    if text == "high":
        return "good"
    if text == "medium":
        return "warn"
    return "risk"


def bar(label: str, value: float, maximum: float, class_name: str = "") -> str:
    width = 0 if maximum <= 0 else max(0, min(100, value / maximum * 100))
    return (
        f'<div class="bar-row {esc(class_name)}">'
        f'<span>{esc(label)}</span>'
        f'<div class="bar-track"><i style="width:{width:.1f}%"></i></div>'
        f"<strong>{value:.2f}</strong>"
        "</div>"
    )


def sparkline(values: list[float], width: int = 170, height: int = 44) -> str:
    if not values:
        return f'<svg class="sparkline" viewBox="0 0 {width} {height}" aria-label="No trend"></svg>'
    min_value = min(values)
    max_value = max(values)
    span = max(max_value - min_value, 0.01)
    if len(values) == 1:
        points = f"{width / 2:.1f},{height / 2:.1f}"
    else:
        points = " ".join(
            f"{index * (width / (len(values) - 1)):.1f},"
            f"{height - ((value - min_value) / span * (height - 8)) - 4:.1f}"
            for index, value in enumerate(values)
        )
    return (
        f'<svg class="sparkline" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Rating trend">'
        f'<polyline points="{points}" fill="none" stroke="currentColor" stroke-width="3" '
        f'stroke-linecap="round" stroke-linejoin="round"></polyline>'
        "</svg>"
    )


def radar(components: dict[str, float], size: int = 138) -> str:
    labels = ["attacking", "possession", "defensive", "goalkeeping"]
    values = [
        number(components.get("attacking_score")),
        number(components.get("possession_score")),
        number(components.get("defensive_score")),
        number(components.get("goalkeeping_score")),
    ]
    center = size / 2
    radius = size * 0.38
    points = []
    axes = []
    for index, value in enumerate(values):
        angle = -1.5708 + index * 1.5708
        axis_x = center + radius * __import__("math").cos(angle)
        axis_y = center + radius * __import__("math").sin(angle)
        point_x = center + radius * max(0, min(1, value)) * __import__("math").cos(angle)
        point_y = center + radius * max(0, min(1, value)) * __import__("math").sin(angle)
        axes.append(
            f'<line x1="{center:.1f}" y1="{center:.1f}" x2="{axis_x:.1f}" y2="{axis_y:.1f}"></line>'
        )
        points.append(f"{point_x:.1f},{point_y:.1f}")
    label_markup = "".join(
        f'<span class="radar-label radar-label-{index}">{esc(label)}</span>'
        for index, label in enumerate(labels)
    )
    return (
        '<div class="radar-wrap">'
        f'<svg class="radar" viewBox="0 0 {size} {size}" role="img" '
        f'aria-label="Role component radar">'
        f'<circle cx="{center:.1f}" cy="{center:.1f}" r="{radius:.1f}"></circle>'
        f'{"".join(axes)}'
        f'<polygon points="{" ".join(points)}"></polygon>'
        "</svg>"
        f"{label_markup}</div>"
    )


def average_components(rows: list[dict[str, str]]) -> dict[str, float]:
    if not rows:
        return {}
    fields = ["attacking_score", "possession_score", "defensive_score", "goalkeeping_score"]
    return {field: sum(number(row.get(field)) for row in rows) / len(rows) for field in fields}


def group_player_games(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["player"], row["team"])].append(row)
    return grouped


def kpi_card(label: str, value: str, detail: str, class_name: str = "") -> str:
    return (
        f'<section class="kpi {esc(class_name)}">'
        f"<span>{esc(label)}</span>"
        f"<strong>{esc(value)}</strong>"
        f"<small>{esc(detail)}</small>"
        "</section>"
    )


def prediction_section(prediction: dict[str, Any]) -> str:
    if not prediction:
        return '<section class="panel"><h2>Prediction</h2><p>No prediction data found.</p></section>'
    top_scorelines = prediction.get("top_scorelines", [])
    max_probability = max([number(row.get("probability")) for row in top_scorelines] or [1])
    scoreline_bars = "".join(
        bar(str(row.get("score")), number(row.get("probability")), max_probability)
        for row in top_scorelines
    )
    outcomes = [
        ("Home", number(prediction.get("home_win"))),
        ("Draw", number(prediction.get("draw"))),
        ("Away", number(prediction.get("away_win"))),
    ]
    outcome_bars = "".join(bar(label, value, 1.0, "probability") for label, value in outcomes)
    reasons = "".join(f"<li>{esc(reason)}</li>" for reason in prediction.get("reasons", []))
    return f"""
    <section class="panel prediction-grid" id="prediction">
      <div>
        <p class="eyebrow">Match Prediction</p>
        <h2>{esc(prediction.get("home_team"))} vs {esc(prediction.get("away_team"))}</h2>
        <div class="xg-line">
          <strong>{fmt(prediction.get("expected_home_goals"))}</strong>
          <span>expected goals</span>
          <strong>{fmt(prediction.get("expected_away_goals"))}</strong>
        </div>
        <div class="confidence {confidence_class(prediction.get("confidence"))}">
          {esc(prediction.get("confidence", "unknown")).title()} confidence
        </div>
        <ul class="reason-list">{reasons}</ul>
      </div>
      <div>
        <h3>Outcome probabilities</h3>
        {outcome_bars}
        <h3>Most likely scorelines</h3>
        {scoreline_bars}
      </div>
    </section>
    """


def validation_section(validation: dict[str, Any], backtest: dict[str, Any]) -> str:
    calibration = "".join(
        f'<span class="pill">{esc(row.get("bucket"))}: {number(row.get("accuracy")):.1%}</span>'
        for row in backtest.get("calibration", [])
    )
    return f"""
    <section class="panel metric-grid" id="validation">
      <div>
        <p class="eyebrow">Rating Validation</p>
        <h2>External rating fit</h2>
        <div class="mini-kpis">
          {kpi_card("MAE", str(validation.get("mae", "n/a")), "mean absolute error")}
          {kpi_card("Correlation", str(validation.get("correlation", "n/a")), "rating movement alignment")}
          {kpi_card("Within 0.5", pct(validation.get("within_half_point_rate", 0)), "close rating share")}
        </div>
      </div>
      <div>
        <p class="eyebrow">Backtest</p>
        <h2>Prediction checks</h2>
        <div class="mini-kpis">
          {kpi_card("Top-3 score", pct(backtest.get("exact_score_top3_rate", 0)), "exact score hit rate")}
          {kpi_card("Outcome", pct(backtest.get("outcome_accuracy", 0)), "W/D/L accuracy")}
          {kpi_card("Log loss", str(backtest.get("log_loss", "n/a")), "lower is better")}
        </div>
        <div class="pill-row">{calibration}</div>
      </div>
    </section>
    """


def player_cards(
    overall_rows: list[dict[str, str]], game_rows: list[dict[str, str]], limit: int = 6
) -> str:
    grouped = group_player_games(game_rows)
    cards = []
    for overall in overall_rows[:limit]:
        key = (overall["player"], overall["team"])
        games = grouped.get(key, [])
        trend = [number(row.get("rating")) for row in games]
        components = average_components(games)
        cards.append(
            f"""
            <article class="player-card">
              <div class="player-card-head">
                <div>
                  <h3>{esc(overall.get("player"))}</h3>
                  <span>{esc(overall.get("team"))} · {esc(overall.get("role_group"))}</span>
                </div>
                <strong>{fmt(overall.get("weighted_rating"))}</strong>
              </div>
              <div class="player-visuals">
                {sparkline(trend)}
                {radar(components)}
              </div>
              <dl>
                <div><dt>Matches</dt><dd>{esc(overall.get("matches"))}</dd></div>
                <div><dt>Minutes</dt><dd>{fmt(overall.get("minutes"), 0)}</dd></div>
                <div><dt>Best</dt><dd>{fmt(overall.get("best_rating"))}</dd></div>
                <div><dt>Confidence</dt><dd><span class="tag {confidence_class(overall.get("confidence"))}">{esc(overall.get("confidence"))}</span></dd></div>
              </dl>
            </article>
            """
        )
    return '<section class="player-grid" id="players">' + "".join(cards) + "</section>"


def role_distribution(overall_rows: list[dict[str, str]]) -> str:
    counts: dict[str, int] = defaultdict(int)
    for row in overall_rows:
        counts[row.get("role_group", "unknown")] += 1
    max_count = max(counts.values() or [1])
    bars = "".join(bar(role, float(count), float(max_count)) for role, count in sorted(counts.items()))
    return f"""
    <section class="panel">
      <p class="eyebrow">Squad Shape</p>
      <h2>Rated players by role</h2>
      {bars}
    </section>
    """


def player_table(rows: list[dict[str, str]]) -> str:
    body = []
    for index, row in enumerate(rows, start=1):
        body.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td><strong>{esc(row.get('player'))}</strong><span>{esc(row.get('team'))}</span></td>"
            f"<td>{esc(row.get('role_group'))}</td>"
            f"<td>{esc(row.get('matches'))}</td>"
            f"<td>{fmt(row.get('minutes'), 0)}</td>"
            f"<td><strong>{fmt(row.get('weighted_rating'))}</strong></td>"
            f"<td>{fmt(row.get('best_rating'))}</td>"
            f"<td><span class=\"tag {confidence_class(row.get('confidence'))}\">{esc(row.get('confidence'))}</span></td>"
            "</tr>"
        )
    return f"""
    <section class="panel wide" id="ratings">
      <p class="eyebrow">Player Ratings</p>
      <h2>Overall leaderboard</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>#</th><th>Player</th><th>Role</th><th>Matches</th><th>Minutes</th><th>Rating</th><th>Best</th><th>Confidence</th></tr></thead>
          <tbody>{''.join(body)}</tbody>
        </table>
      </div>
    </section>
    """


def game_table(rows: list[dict[str, str]], limit: int = 20) -> str:
    body = []
    sorted_rows = sorted(rows, key=lambda row: number(row.get("rating")), reverse=True)
    for row in sorted_rows[:limit]:
        body.append(
            "<tr>"
            f"<td><strong>{esc(row.get('player'))}</strong><span>{esc(row.get('team'))} vs {esc(row.get('opponent'))}</span></td>"
            f"<td>{esc(row.get('role_group'))}</td>"
            f"<td>{fmt(row.get('minutes'), 0)}</td>"
            f"<td>{fmt(row.get('rating'))}</td>"
            f"<td>{fmt(row.get('attacking_score'))}</td>"
            f"<td>{fmt(row.get('possession_score'))}</td>"
            f"<td>{fmt(row.get('defensive_score'))}</td>"
            f"<td>{fmt(row.get('goalkeeping_score'))}</td>"
            "</tr>"
        )
    return f"""
    <section class="panel wide">
      <p class="eyebrow">Game Analysis</p>
      <h2>Best single-game performances</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Player</th><th>Role</th><th>Min</th><th>Rating</th><th>Attack</th><th>Possession</th><th>Defense</th><th>GK</th></tr></thead>
          <tbody>{''.join(body)}</tbody>
        </table>
      </div>
    </section>
    """


def css() -> str:
    return """
    :root {
      color-scheme: light;
      --bg: #f5f7f4;
      --ink: #17201d;
      --muted: #65706c;
      --line: #dbe2dd;
      --panel: #ffffff;
      --accent: #137c55;
      --accent-2: #2454a6;
      --warn: #9d6a00;
      --risk: #a23a3a;
      --shadow: 0 18px 45px rgba(23, 32, 29, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }
    header {
      background: #12201a;
      color: #f7fbf8;
      padding: 34px clamp(18px, 4vw, 54px) 24px;
      border-bottom: 6px solid #28a66f;
    }
    header nav {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 22px;
    }
    header a {
      color: #dff7ea;
      text-decoration: none;
      border: 1px solid rgba(223, 247, 234, 0.28);
      padding: 8px 11px;
      border-radius: 6px;
      font-size: 14px;
    }
    h1, h2, h3, p { margin-top: 0; }
    h1 {
      max-width: 960px;
      margin-bottom: 10px;
      font-size: clamp(32px, 5vw, 58px);
      letter-spacing: 0;
      line-height: 1.02;
    }
    header p {
      max-width: 860px;
      color: #cbd9d2;
      font-size: 17px;
      line-height: 1.55;
      margin-bottom: 0;
    }
    main {
      padding: 26px clamp(14px, 3vw, 40px) 44px;
      max-width: 1500px;
      margin: 0 auto;
    }
    .kpi-row, .mini-kpis {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
    }
    .kpi, .panel, .player-card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    .kpi {
      padding: 18px;
      min-height: 118px;
    }
    .kpi span, .eyebrow {
      color: var(--muted);
      text-transform: uppercase;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: .08em;
    }
    .kpi strong {
      display: block;
      font-size: 31px;
      margin: 8px 0 4px;
    }
    .kpi small { color: var(--muted); line-height: 1.35; }
    .panel {
      padding: clamp(18px, 2.4vw, 28px);
      margin-top: 18px;
    }
    .prediction-grid, .metric-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(320px, .95fr);
      gap: 28px;
      align-items: start;
    }
    .xg-line {
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      gap: 16px;
      align-items: center;
      margin: 18px 0;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f8faf8;
      text-align: center;
    }
    .xg-line strong { font-size: 42px; color: var(--accent); }
    .xg-line span { color: var(--muted); font-weight: 700; }
    .confidence, .tag, .pill {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 5px 9px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 800;
      background: #edf4f0;
      color: var(--accent);
    }
    .warn { color: var(--warn); background: #fff5d8; }
    .risk { color: var(--risk); background: #ffe8e5; }
    .reason-list { color: var(--muted); line-height: 1.55; padding-left: 18px; }
    .bar-row {
      display: grid;
      grid-template-columns: minmax(72px, 130px) 1fr 58px;
      gap: 12px;
      align-items: center;
      margin: 11px 0;
      color: var(--muted);
      font-size: 14px;
    }
    .bar-track {
      height: 12px;
      background: #e9efeb;
      border-radius: 999px;
      overflow: hidden;
    }
    .bar-track i {
      display: block;
      height: 100%;
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
      border-radius: inherit;
    }
    .player-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 16px;
      margin-top: 18px;
    }
    .player-card {
      padding: 18px;
      min-height: 336px;
    }
    .player-card-head {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: start;
    }
    .player-card h3 { margin-bottom: 4px; }
    .player-card-head span, td span { display: block; color: var(--muted); font-size: 13px; margin-top: 3px; }
    .player-card-head strong { font-size: 38px; color: var(--accent); }
    .player-visuals {
      display: grid;
      grid-template-columns: 1fr 150px;
      gap: 12px;
      align-items: center;
      min-height: 158px;
    }
    .sparkline {
      width: 100%;
      height: 72px;
      color: var(--accent-2);
      background: #f8faf8;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
    }
    .radar-wrap {
      position: relative;
      min-height: 150px;
      display: grid;
      place-items: center;
      color: var(--accent);
    }
    .radar circle, .radar line { fill: none; stroke: #d6dfd9; stroke-width: 1.5; }
    .radar polygon { fill: rgba(19, 124, 85, .18); stroke: var(--accent); stroke-width: 2; }
    .radar-label {
      position: absolute;
      color: var(--muted);
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
    }
    .radar-label-0 { top: 0; left: 50%; transform: translateX(-50%); }
    .radar-label-1 { right: 0; top: 45%; }
    .radar-label-2 { bottom: 0; left: 42%; }
    .radar-label-3 { left: 0; top: 45%; }
    dl {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin: 0;
    }
    dt { color: var(--muted); font-size: 11px; text-transform: uppercase; font-weight: 800; }
    dd { margin: 4px 0 0; font-weight: 800; }
    .table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; }
    table { width: 100%; border-collapse: collapse; min-width: 820px; background: #fff; }
    th, td { padding: 13px 14px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
    th { color: var(--muted); background: #f8faf8; font-size: 12px; text-transform: uppercase; letter-spacing: .05em; }
    tbody tr:hover { background: #f8fbf9; }
    .pill-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
    footer { color: var(--muted); text-align: center; padding: 22px; }
    @media (max-width: 860px) {
      .prediction-grid, .metric-grid, .player-visuals { grid-template-columns: 1fr; }
      dl { grid-template-columns: repeat(2, 1fr); }
      .xg-line { grid-template-columns: 1fr; }
    }
    """


def render_dashboard(
    *,
    overall_rows: list[dict[str, str]],
    game_rows: list[dict[str, str]],
    prediction: dict[str, Any],
    validation: dict[str, Any],
    backtest: dict[str, Any],
    title: str = "FIFA World Cup 2026 Performance Dashboard",
) -> str:
    sorted_overall = sorted(overall_rows, key=lambda row: number(row.get("weighted_rating")), reverse=True)
    sorted_games = sorted(game_rows, key=lambda row: number(row.get("rating")), reverse=True)
    best_player = sorted_overall[0] if sorted_overall else {}
    top_game = sorted_games[0] if sorted_games else {}
    kpis = [
        kpi_card("Rated Players", str(len(sorted_overall)), "overall ratings in database"),
        kpi_card("Player Games", str(len(game_rows)), "per-match ratings generated"),
        kpi_card(
            "Top Overall",
            fmt(best_player.get("weighted_rating")),
            f"{best_player.get('player', 'n/a')} · {best_player.get('team', '')}",
        ),
        kpi_card(
            "Best Game",
            fmt(top_game.get("rating")),
            f"{top_game.get('player', 'n/a')} vs {top_game.get('opponent', '')}",
        ),
    ]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>{css()}</style>
</head>
<body>
  <header>
    <h1>{esc(title)}</h1>
    <p>Role-aware player ratings, match predictions, exact-score probabilities, validation metrics, and performance trends generated from the project database and report outputs.</p>
    <nav>
      <a href="#prediction">Prediction</a>
      <a href="#players">Player Cards</a>
      <a href="#ratings">Leaderboard</a>
      <a href="#validation">Validation</a>
    </nav>
  </header>
  <main>
    <section class="kpi-row">{"".join(kpis)}</section>
    {prediction_section(prediction)}
    {player_cards(sorted_overall, game_rows)}
    <div class="metric-grid">
      {role_distribution(sorted_overall)}
      {validation_section(validation, backtest)}
    </div>
    {player_table(sorted_overall)}
    {game_table(game_rows)}
  </main>
  <footer>Generated from local FIFA analysis outputs. Ratings are model-generated and should be validated against trusted external data when available.</footer>
</body>
</html>
"""


def generate_dashboard(
    *,
    overall_ratings_path: str | Path,
    game_ratings_path: str | Path,
    prediction_path: str | Path,
    validation_path: str | Path,
    backtest_path: str | Path,
    output_path: str | Path,
    title: str = "FIFA World Cup 2026 Performance Dashboard",
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    html_output = render_dashboard(
        overall_rows=read_csv(overall_ratings_path),
        game_rows=read_csv(game_ratings_path),
        prediction=read_json(prediction_path),
        validation=read_json(validation_path),
        backtest=read_json(backtest_path),
        title=title,
    )
    output.write_text(html_output, encoding="utf-8")
    return output

