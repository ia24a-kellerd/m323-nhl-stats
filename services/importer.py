"""CSV import utilities for game data."""

from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO

from models import Game

RESULT_TYPES = {"REG", "OT", "SO"}
REQUIRED_FIELDS = (
    "date",
    "season",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "result_type",
)


def missing_fields(row: dict[str, str]) -> list[str]:
    """Return required fields that are missing or blank."""
    return [field for field in REQUIRED_FIELDS if not (row.get(field) or "").strip()]


def parse_row(row: dict[str, str]) -> Game:
    """Parse one CSV row into a Game object."""
    return Game(
        date=datetime.strptime(row["date"].strip(), "%Y-%m-%d").date(),
        season=row["season"].strip(),
        home_team=row["home_team"].strip().upper(),
        away_team=row["away_team"].strip().upper(),
        home_goals=int(row["home_goals"]),
        away_goals=int(row["away_goals"]),
        result_type=row["result_type"].strip().upper(),
    )


def validate_game(game: Game) -> str | None:
    """Validate parsed Game values and return an error message if invalid."""
    if game.home_goals < 0 or game.away_goals < 0:
        return "goals must not be negative"
    if game.home_goals == game.away_goals:
        return "tied score is not allowed"
    if game.result_type not in RESULT_TYPES:
        return "invalid result_type"
    return None


def validate_row(row: dict[str, str]) -> tuple[Game | None, str | None]:
    """Validate one row and return (game, error)."""
    missing = missing_fields(row)
    if missing:
        return None, f"missing fields: {', '.join(missing)}"

    try:
        game = parse_row(row)
    except ValueError as exc:
        return None, str(exc)

    error = validate_game(game)
    if error:
        return None, error
    return game, None


def import_games_from_csv(csv_text: str) -> tuple[list[Game], list[dict[str, object]]]:
    """Import games from CSV text and return (accepted, rejected)."""
    accepted: list[Game] = []
    rejected: list[dict[str, object]] = []

    reader = csv.DictReader(StringIO(csv_text))
    for row_number, row in enumerate(reader, start=2):
        game, error = validate_row(row)
        if error:
            rejected.append({"row_number": row_number, "error": error, "row": row})
        else:
            accepted.append(game)

    return accepted, rejected
