"""SQLite storage for World Cup player performance ratings."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from fifa_analysis.ratings import PlayerGameRating, PlayerOverallRating
from fifa_analysis.schemas import MatchRecord, PlayerMatchStats


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    team TEXT NOT NULL,
    position TEXT NOT NULL,
    role_group TEXT NOT NULL,
    UNIQUE(name, team)
);

CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    date TEXT,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_goals INTEGER,
    away_goals INTEGER,
    status TEXT,
    stage TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS player_game_stats (
    match_id TEXT NOT NULL,
    player TEXT NOT NULL,
    team TEXT NOT NULL,
    opponent TEXT NOT NULL,
    position TEXT NOT NULL,
    role_group TEXT NOT NULL,
    minutes REAL NOT NULL,
    goals REAL NOT NULL,
    assists REAL NOT NULL,
    xg REAL NOT NULL,
    shots REAL NOT NULL,
    progressive_passes REAL NOT NULL,
    progressive_carries REAL NOT NULL,
    carries REAL NOT NULL,
    successful_dribbles REAL NOT NULL,
    interceptions REAL NOT NULL,
    tackles REAL NOT NULL,
    clearances REAL NOT NULL,
    aerials_won REAL NOT NULL,
    pressures REAL NOT NULL,
    ball_recoveries REAL NOT NULL,
    saves REAL NOT NULL,
    claims REAL NOT NULL,
    pass_completion_pct REAL NOT NULL,
    chance_creation REAL NOT NULL,
    contribution_score REAL NOT NULL,
    source TEXT,
    PRIMARY KEY(match_id, player, team)
);

CREATE TABLE IF NOT EXISTS player_game_ratings (
    match_id TEXT NOT NULL,
    player TEXT NOT NULL,
    team TEXT NOT NULL,
    opponent TEXT NOT NULL,
    position TEXT NOT NULL,
    role_group TEXT NOT NULL,
    rating REAL NOT NULL,
    confidence TEXT NOT NULL,
    minutes REAL NOT NULL,
    attacking_score REAL NOT NULL,
    possession_score REAL NOT NULL,
    defensive_score REAL NOT NULL,
    goalkeeping_score REAL NOT NULL,
    reasons_json TEXT NOT NULL,
    PRIMARY KEY(match_id, player, team)
);

CREATE TABLE IF NOT EXISTS player_overall_ratings (
    player TEXT NOT NULL,
    team TEXT NOT NULL,
    role_group TEXT NOT NULL,
    matches INTEGER NOT NULL,
    minutes REAL NOT NULL,
    average_rating REAL NOT NULL,
    weighted_rating REAL NOT NULL,
    best_rating REAL NOT NULL,
    latest_rating REAL NOT NULL,
    confidence TEXT NOT NULL,
    PRIMARY KEY(player, team)
);

CREATE TABLE IF NOT EXISTS rating_validation (
    validation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    sample_size INTEGER NOT NULL,
    mae REAL,
    correlation REAL,
    within_half_point_rate REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


def upsert_matches(conn: sqlite3.Connection, matches: Iterable[MatchRecord]) -> int:
    count = 0
    for match in matches:
        conn.execute(
            """
            INSERT INTO matches (
                match_id, date, home_team, away_team, home_goals, away_goals, status, stage, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(match_id) DO UPDATE SET
                date=excluded.date,
                home_team=excluded.home_team,
                away_team=excluded.away_team,
                home_goals=excluded.home_goals,
                away_goals=excluded.away_goals,
                status=excluded.status,
                stage=excluded.stage,
                source=excluded.source
            """,
            (
                match.match_id,
                match.date,
                match.home_team,
                match.away_team,
                match.home_goals,
                match.away_goals,
                match.status,
                match.stage,
                match.source,
            ),
        )
        for team in (match.home_team, match.away_team):
            conn.execute("INSERT OR IGNORE INTO teams(name) VALUES (?)", (team,))
        count += 1
    return count


def upsert_player_stats(conn: sqlite3.Connection, rows: Iterable[PlayerMatchStats]) -> int:
    count = 0
    for row in rows:
        conn.execute("INSERT OR IGNORE INTO teams(name) VALUES (?)", (row.team,))
        conn.execute(
            """
            INSERT INTO players(name, team, position, role_group)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name, team) DO UPDATE SET
                position=excluded.position,
                role_group=excluded.role_group
            """,
            (row.player, row.team, row.position, row.role_group),
        )
        conn.execute(
            """
            INSERT INTO player_game_stats VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(match_id, player, team) DO UPDATE SET
                opponent=excluded.opponent,
                position=excluded.position,
                role_group=excluded.role_group,
                minutes=excluded.minutes,
                goals=excluded.goals,
                assists=excluded.assists,
                xg=excluded.xg,
                shots=excluded.shots,
                progressive_passes=excluded.progressive_passes,
                progressive_carries=excluded.progressive_carries,
                carries=excluded.carries,
                successful_dribbles=excluded.successful_dribbles,
                interceptions=excluded.interceptions,
                tackles=excluded.tackles,
                clearances=excluded.clearances,
                aerials_won=excluded.aerials_won,
                pressures=excluded.pressures,
                ball_recoveries=excluded.ball_recoveries,
                saves=excluded.saves,
                claims=excluded.claims,
                pass_completion_pct=excluded.pass_completion_pct,
                chance_creation=excluded.chance_creation,
                contribution_score=excluded.contribution_score,
                source=excluded.source
            """,
            (
                row.match_id,
                row.player,
                row.team,
                row.opponent,
                row.position,
                row.role_group,
                row.minutes,
                row.goals,
                row.assists,
                row.xg,
                row.shots,
                row.progressive_passes,
                row.progressive_carries,
                row.carries,
                row.successful_dribbles,
                row.interceptions,
                row.tackles,
                row.clearances,
                row.aerials_won,
                row.pressures,
                row.ball_recoveries,
                row.saves,
                row.claims,
                row.pass_completion_pct,
                row.chance_creation,
                row.contribution_score,
                row.source,
            ),
        )
        count += 1
    return count


def fetch_player_stats(conn: sqlite3.Connection) -> list[PlayerMatchStats]:
    rows = conn.execute("SELECT * FROM player_game_stats ORDER BY match_id, team, player").fetchall()
    return [PlayerMatchStats(**dict(row)) for row in rows]


def fetch_game_ratings(conn: sqlite3.Connection) -> list[PlayerGameRating]:
    rows = conn.execute("SELECT * FROM player_game_ratings ORDER BY match_id, team, player").fetchall()
    ratings: list[PlayerGameRating] = []
    for row in rows:
        payload = dict(row)
        payload["reasons"] = json.loads(payload.pop("reasons_json"))
        ratings.append(PlayerGameRating(**payload))
    return ratings


def fetch_overall_ratings(conn: sqlite3.Connection) -> list[PlayerOverallRating]:
    rows = conn.execute(
        "SELECT * FROM player_overall_ratings ORDER BY weighted_rating DESC, minutes DESC"
    ).fetchall()
    return [PlayerOverallRating(**dict(row)) for row in rows]


def upsert_game_ratings(conn: sqlite3.Connection, ratings: Iterable[PlayerGameRating]) -> int:
    count = 0
    for rating in ratings:
        conn.execute(
            """
            INSERT INTO player_game_ratings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(match_id, player, team) DO UPDATE SET
                opponent=excluded.opponent,
                position=excluded.position,
                role_group=excluded.role_group,
                rating=excluded.rating,
                confidence=excluded.confidence,
                minutes=excluded.minutes,
                attacking_score=excluded.attacking_score,
                possession_score=excluded.possession_score,
                defensive_score=excluded.defensive_score,
                goalkeeping_score=excluded.goalkeeping_score,
                reasons_json=excluded.reasons_json
            """,
            (
                rating.match_id,
                rating.player,
                rating.team,
                rating.opponent,
                rating.position,
                rating.role_group,
                rating.rating,
                rating.confidence,
                rating.minutes,
                rating.attacking_score,
                rating.possession_score,
                rating.defensive_score,
                rating.goalkeeping_score,
                json.dumps(rating.reasons),
            ),
        )
        count += 1
    return count


def upsert_overall_ratings(conn: sqlite3.Connection, ratings: Iterable[PlayerOverallRating]) -> int:
    count = 0
    for rating in ratings:
        conn.execute(
            """
            INSERT INTO player_overall_ratings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(player, team) DO UPDATE SET
                role_group=excluded.role_group,
                matches=excluded.matches,
                minutes=excluded.minutes,
                average_rating=excluded.average_rating,
                weighted_rating=excluded.weighted_rating,
                best_rating=excluded.best_rating,
                latest_rating=excluded.latest_rating,
                confidence=excluded.confidence
            """,
            (
                rating.player,
                rating.team,
                rating.role_group,
                rating.matches,
                rating.minutes,
                rating.average_rating,
                rating.weighted_rating,
                rating.best_rating,
                rating.latest_rating,
                rating.confidence,
            ),
        )
        count += 1
    return count


def table_count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])


def insert_rating_validation(
    conn: sqlite3.Connection,
    source: str,
    sample_size: int,
    mae: float | None,
    correlation: float | None,
    within_half_point_rate: float | None,
) -> None:
    conn.execute(
        """
        INSERT INTO rating_validation(source, sample_size, mae, correlation, within_half_point_rate)
        VALUES (?, ?, ?, ?, ?)
        """,
        (source, sample_size, mae, correlation, within_half_point_rate),
    )

