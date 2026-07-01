"""Free-data-first ingestion connectors.

Connectors normalize source-specific payloads into shared records. Network
connectors are deliberately small wrappers around JSON endpoints so tests can
use local fixtures and future paid providers can be added behind the same
normalized schema.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fifa_analysis.schemas import MatchRecord, optional_float, optional_int


def load_json(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as json_file:
        return json.load(json_file)


def fetch_json(url: str, headers: dict[str, str] | None = None, timeout: int = 20) -> Any:
    request = Request(url, headers=headers or {})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not fetch JSON from {url}: {exc}") from exc


def load_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv_rows(path: str | Path, rows: list[dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output_path.write_text("", encoding="utf-8")
        return
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _team_name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("title") or value.get("code") or "")
    return str(value or "")


def _score_value(value: Any, keys: tuple[str, ...]) -> int | None:
    if isinstance(value, dict):
        for key in keys:
            if key in value:
                return optional_int(value[key])
    return optional_int(value)


def normalize_openfootball_matches(payload: Any, source: str = "openfootball") -> list[MatchRecord]:
    """Normalize openfootball/worldcup.json-style match payloads."""

    matches: list[MatchRecord] = []
    rounds = payload.get("rounds", []) if isinstance(payload, dict) else payload
    for round_index, round_payload in enumerate(rounds or [], start=1):
        stage = str(round_payload.get("name") or round_payload.get("stage") or round_index)
        for game_index, game in enumerate(round_payload.get("matches", []) or [], start=1):
            teams = game.get("team1"), game.get("team2")
            score = game.get("score") or {}
            match_id = str(game.get("num") or game.get("id") or f"{round_index}-{game_index}")
            matches.append(
                MatchRecord(
                    match_id=match_id,
                    date=str(game.get("date") or ""),
                    home_team=_team_name(teams[0]),
                    away_team=_team_name(teams[1]),
                    home_goals=_score_value(score.get("ft", score), ("team1", "home")),
                    away_goals=_score_value(score.get("ft", score), ("team2", "away")),
                    status="finished" if score else "scheduled",
                    stage=stage,
                    group=str(game.get("group") or ""),
                    source=source,
                )
            )
    return matches


def normalize_worldcup2026_api(payload: Any, source: str = "worldcup2026") -> list[MatchRecord]:
    """Normalize rezarahiminia/worldcup2026 `/get/games` responses."""

    games = payload.get("games", payload) if isinstance(payload, dict) else payload
    matches: list[MatchRecord] = []
    for game in games or []:
        if not isinstance(game, dict):
            continue
        home_team = game.get("home_team") or game.get("home_team_name") or game.get("home_name")
        away_team = game.get("away_team") or game.get("away_team_name") or game.get("away_name")
        matches.append(
            MatchRecord(
                match_id=str(game.get("id") or game.get("_id") or ""),
                date=str(game.get("local_date") or game.get("date") or ""),
                home_team=_team_name(home_team or game.get("home_team_id")),
                away_team=_team_name(away_team or game.get("away_team_id")),
                home_goals=optional_int(game.get("home_score")),
                away_goals=optional_int(game.get("away_score")),
                status="finished" if str(game.get("finished", "")).upper() == "TRUE" else "scheduled",
                stage=str(game.get("stage") or ""),
                group=str(game.get("group") or ""),
                source=source,
            )
        )
    return matches


def normalize_football_data_org(payload: Any, source: str = "football-data.org") -> list[MatchRecord]:
    """Normalize football-data.org match responses."""

    matches_payload = payload.get("matches", payload) if isinstance(payload, dict) else payload
    matches: list[MatchRecord] = []
    for item in matches_payload or []:
        score = item.get("score") or {}
        full_time = score.get("fullTime") or {}
        matches.append(
            MatchRecord(
                match_id=str(item.get("id") or ""),
                date=str(item.get("utcDate") or ""),
                home_team=_team_name(item.get("homeTeam")),
                away_team=_team_name(item.get("awayTeam")),
                home_goals=optional_int(full_time.get("home")),
                away_goals=optional_int(full_time.get("away")),
                status=str(item.get("status") or "").lower(),
                stage=str(item.get("stage") or ""),
                group=str(item.get("group") or ""),
                source=source,
            )
        )
    return matches


def fetch_worldcup2026_matches(base_url: str = "https://worldcup26.ir") -> list[MatchRecord]:
    return normalize_worldcup2026_api(fetch_json(f"{base_url.rstrip('/')}/get/games"))


def fetch_football_data_org_matches(api_token: str, competition_code: str) -> list[MatchRecord]:
    url = f"https://api.football-data.org/v4/competitions/{competition_code}/matches"
    return normalize_football_data_org(fetch_json(url, headers={"X-Auth-Token": api_token}))


def match_records_to_rows(matches: list[MatchRecord]) -> list[dict[str, Any]]:
    return [
        {
            "match_id": match.match_id,
            "date": match.date,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "home_goals": "" if match.home_goals is None else match.home_goals,
            "away_goals": "" if match.away_goals is None else match.away_goals,
            "status": match.status,
            "stage": match.stage,
            "group": match.group,
            "source": match.source,
        }
        for match in matches
    ]


def read_match_records(path: str | Path) -> list[MatchRecord]:
    rows = load_csv_rows(path)
    return [
        MatchRecord(
            match_id=row.get("match_id", ""),
            date=row.get("date", ""),
            home_team=row.get("home_team", ""),
            away_team=row.get("away_team", ""),
            home_goals=optional_int(row.get("home_goals")),
            away_goals=optional_int(row.get("away_goals")),
            status=row.get("status", ""),
            stage=row.get("stage", ""),
            group=row.get("group", ""),
            source=row.get("source", ""),
        )
        for row in rows
    ]


def csv_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    return optional_float(row.get(key), default)

