"""Ingestion helpers for Opta Analyst World Cup player statistics."""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


THEANALYST_WORLD_CUP_TMCL = "873cbl9cd9butm4air0mugxzo"
THEANALYST_PLAYER_STATS_URL = (
    f"https://dataviz.theanalyst.com/project-data/soccer/{THEANALYST_WORLD_CUP_TMCL}/player-stats.json"
)

TOURNAMENT_STAT_COLUMNS = [
    "player",
    "team",
    "position",
    "detailed_position",
    "player_uuid",
    "team_uuid",
    "team_code",
    "age",
    "shirt_number",
    "wc_matches",
    "wc_minutes",
    "wc_goals",
    "wc_assists",
    "wc_goal_assists",
    "wc_xg",
    "wc_xa",
    "wc_shots",
    "wc_shots_on_target",
    "wc_chances_created",
    "wc_passes",
    "wc_successful_passes",
    "wc_pass_completion",
    "wc_final_third_passes",
    "wc_successful_final_third_passes",
    "wc_carries",
    "wc_progressive_carries",
    "wc_carry_distance",
    "wc_progressive_carry_distance",
    "wc_tackles",
    "wc_interceptions",
    "wc_recoveries",
    "wc_blocks",
    "wc_clearances",
    "wc_aerial_duels",
    "wc_aerial_duels_won",
    "wc_yellows",
    "wc_reds",
    "wc_fouls_committed",
    "wc_offsides",
    "wc_saves",
    "wc_save_pct",
    "wc_goals_prevented",
    "wc_xgot_conceded",
    "wc_goals_conceded",
    "source",
    "source_url",
    "last_updated",
    "accessed_date",
]


def fetch_theanalyst_player_stats(url: str = THEANALYST_PLAYER_STATS_URL) -> dict[str, Any]:
    """Fetch Opta Analyst player statistics JSON with a browser-like user agent."""

    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_theanalyst_player_stats(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _identity(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "player": row.get("player", ""),
        "team": row.get("contestantName") or row.get("contestantShortName") or "",
        "position": row.get("squad_position", ""),
        "detailed_position": row.get("squad_position_detailed", ""),
        "player_uuid": row.get("player_uuid", ""),
        "team_uuid": row.get("team_uuid", ""),
        "team_code": row.get("contestantCode", ""),
        "age": row.get("age", ""),
        "shirt_number": row.get("shirt_number", ""),
    }


def _merge_values(target: dict[str, Any], source: dict[str, Any], mapping: dict[str, str]) -> None:
    for output_key, input_key in mapping.items():
        value = source.get(input_key)
        if value not in (None, ""):
            target[output_key] = value


def normalize_theanalyst_player_stats(
    payload: dict[str, Any],
    *,
    source_url: str = THEANALYST_PLAYER_STATS_URL,
    accessed_date: str | None = None,
) -> list[dict[str, Any]]:
    """Flatten The Analyst sectioned player stats into one row per tournament player."""

    accessed = accessed_date or datetime.now(UTC).date().isoformat()
    last_updated = payload.get("lastUpdated", "")
    rows: dict[str, dict[str, Any]] = {}

    def get_row(stat_row: dict[str, Any]) -> dict[str, Any]:
        player_uuid = str(stat_row.get("player_uuid") or stat_row.get("player_id") or "")
        team_uuid = str(stat_row.get("team_uuid") or stat_row.get("team_id") or "")
        key = f"{player_uuid}|||{team_uuid}"
        if key not in rows:
            rows[key] = {
                **_identity(stat_row),
                "source": "The Analyst Opta player stats",
                "source_url": source_url,
                "last_updated": last_updated,
                "accessed_date": accessed,
            }
        return rows[key]

    for stat_row in payload.get("attack", {}).get("overall", []):
        row = get_row(stat_row)
        _merge_values(
            row,
            stat_row,
            {
                "wc_matches": "apps",
                "wc_minutes": "mins_played",
                "wc_goals": "goals",
                "wc_xg": "xg",
                "wc_shots": "shots",
                "wc_shots_on_target": "shots_on_target",
            },
        )

    for stat_row in payload.get("possession", {}).get("chanceCreation", []):
        row = get_row(stat_row)
        _merge_values(
            row,
            stat_row,
            {
                "wc_assists": "assists",
                "wc_xa": "xa",
                "wc_chances_created": "chances_created",
            },
        )

    for stat_row in payload.get("possession", {}).get("passing", []):
        row = get_row(stat_row)
        _merge_values(
            row,
            stat_row,
            {
                "wc_passes": "passes",
                "wc_successful_passes": "successful_passes",
                "wc_pass_completion": "pass_perc",
                "wc_final_third_passes": "total_final_third_passes",
                "wc_successful_final_third_passes": "successful_final_third_passes",
            },
        )

    for stat_row in payload.get("carries", {}).get("overall", []):
        row = get_row(stat_row)
        _merge_values(
            row,
            stat_row,
            {
                "wc_carries": "carries",
                "wc_progressive_carries": "progressive_carries",
                "wc_carry_distance": "carry_distance",
                "wc_progressive_carry_distance": "progressive_distance",
            },
        )

    for stat_row in payload.get("defending", {}).get("overall", []):
        row = get_row(stat_row)
        _merge_values(
            row,
            stat_row,
            {
                "wc_tackles": "tackles",
                "wc_interceptions": "interceptions",
                "wc_recoveries": "recoveries",
                "wc_blocks": "blocks",
                "wc_clearances": "clearances",
                "wc_aerial_duels": "aerial_duels",
                "wc_aerial_duels_won": "aerial_duels_won",
            },
        )

    for stat_row in payload.get("defending", {}).get("discipline", []):
        row = get_row(stat_row)
        _merge_values(
            row,
            stat_row,
            {
                "wc_yellows": "yellows",
                "wc_reds": "reds",
                "wc_fouls_committed": "fouls_commited",
                "wc_offsides": "offsides",
            },
        )

    for stat_row in payload.get("goalkeeping", {}).get("overall", []):
        row = get_row(stat_row)
        _merge_values(
            row,
            stat_row,
            {
                "wc_matches": "apps",
                "wc_minutes": "mins_played",
                "wc_saves": "saves_made",
                "wc_save_pct": "save_perc",
                "wc_goals_prevented": "goals_prevented",
                "wc_xgot_conceded": "xgot_conceded",
                "wc_goals_conceded": "goals_conceded",
            },
        )

    normalized = []
    for row in rows.values():
        goal_assists = _to_float(row.get("wc_goals")) + _to_float(row.get("wc_assists"))
        row["wc_goal_assists"] = _clean_number(goal_assists)
        normalized.append({column: row.get(column, "") for column in TOURNAMENT_STAT_COLUMNS})
    return sorted(normalized, key=lambda row: (str(row["team"]), str(row["player"])))


def _to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _clean_number(value: float) -> int | float:
    return int(value) if value.is_integer() else round(value, 3)


def write_tournament_stats_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TOURNAMENT_STAT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_tournament_stats_sqlite(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("drop table if exists player_tournament_stats")
        columns_sql = ", ".join(f"{column} text" for column in TOURNAMENT_STAT_COLUMNS)
        connection.execute(f"create table player_tournament_stats ({columns_sql})")
        placeholders = ", ".join("?" for _ in TOURNAMENT_STAT_COLUMNS)
        connection.executemany(
            f"insert into player_tournament_stats values ({placeholders})",
            [[row.get(column, "") for column in TOURNAMENT_STAT_COLUMNS] for row in rows],
        )
        connection.execute("create index idx_player_tournament_stats_player on player_tournament_stats(player)")
        connection.execute("create index idx_player_tournament_stats_team on player_tournament_stats(team)")
