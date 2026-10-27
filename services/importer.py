"""CSV import as a composed pipeline: read_rows -> parse_row -> validate -> to_game."""

from __future__ import annotations

import csv
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import date, datetime
from functools import wraps
from io import StringIO
from types import MappingProxyType
from typing import Any

from models import Game
from services.functional import compose

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


@dataclass(frozen=True)
class RowResult:
    """One CSV line on its way through the pipeline: a value or an error."""

    line: int
    value: Any = None
    error: str | None = None


@dataclass(frozen=True)
class RowError:
    """A rejected CSV line with the reason."""

    line: int
    reason: str


def fail(row: RowResult, reason: str) -> RowResult:
    """Return the row marked as failed."""
    return replace(row, value=None, error=reason)


def skip_on_error(step: Callable[[RowResult], RowResult]) -> Callable[[RowResult], RowResult]:
    """Run the step only for rows without an error; failed rows pass through unchanged."""

    @wraps(step)
    def wrapper(row: RowResult) -> RowResult:
        return row if row.error else step(row)

    return wrapper


def read_rows(text: str) -> tuple[tuple[str, ...], tuple[RowResult, ...]]:
    """Read CSV text into (header, rows); each row keeps its real line number."""
    reader = csv.DictReader(StringIO(text))
    rows = tuple(RowResult(reader.line_num, row) for row in reader)
    return tuple(reader.fieldnames or ()), rows


def check_header(header: tuple[str, ...], rows: tuple[RowResult, ...]) -> RowError | None:
    """Return an error for an empty file, missing columns or a file without games."""
    if not header:
        return RowError(1, "file is empty")
    missing = tuple(filter(lambda field: field not in header, REQUIRED_FIELDS))
    if missing:
        return RowError(1, f"missing columns: {', '.join(missing)}")
    if not rows:
        return RowError(1, "file contains no games")
    return None


def missing_fields(raw: Mapping[str, str | None]) -> tuple[str, ...]:
    """Return required fields that are missing or blank."""
    return tuple(filter(lambda field: not (raw.get(field) or "").strip(), REQUIRED_FIELDS))


def parse_date(text: str) -> date | None:
    """Parse YYYY-MM-DD, return None if invalid."""
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_int(text: str) -> int | None:
    """Parse a whole number, return None if invalid."""
    try:
        return int(text.strip())
    except ValueError:
        return None


@skip_on_error
def parse_row(row: RowResult) -> RowResult:
    """Convert the raw text values into typed values."""
    raw = row.value
    missing = missing_fields(raw)
    if missing:
        return fail(row, f"missing fields: {', '.join(missing)}")

    game_date = parse_date(raw["date"])
    if game_date is None:
        return fail(row, f"invalid date '{raw['date']}' (expected YYYY-MM-DD)")

    home_goals, away_goals = parse_int(raw["home_goals"]), parse_int(raw["away_goals"])
    if home_goals is None or away_goals is None:
        return fail(row, "goals must be whole numbers")

    return replace(
        row,
        value=MappingProxyType(
            {
                "date": game_date,
                "season": raw["season"].strip(),
                "home_team": raw["home_team"].strip().upper(),
                "away_team": raw["away_team"].strip().upper(),
                "home_goals": home_goals,
                "away_goals": away_goals,
                "result_type": raw["result_type"].strip().upper(),
            }
        ),
    )


VALIDATION_RULES: tuple[tuple[Callable[[Mapping[str, Any]], bool], str], ...] = (
    (lambda v: v["home_team"] == v["away_team"], "home and away team are the same"),
    (lambda v: v["home_goals"] < 0 or v["away_goals"] < 0, "goals must not be negative"),
    (lambda v: v["home_goals"] == v["away_goals"], "tied score is not allowed"),
    (lambda v: v["result_type"] not in RESULT_TYPES, "invalid result_type"),
    (
        lambda v: v["result_type"] in {"OT", "SO"} and abs(v["home_goals"] - v["away_goals"]) > 1,
        "OT/SO game must be won by exactly one goal",
    ),
)


@skip_on_error
def validate(row: RowResult) -> RowResult:
    """Check the typed values against VALIDATION_RULES; the first broken rule wins."""
    broken = next(filter(lambda rule: rule[0](row.value), VALIDATION_RULES), None)
    return fail(row, broken[1]) if broken else row


@skip_on_error
def to_game(row: RowResult) -> RowResult:
    """Turn the validated values into a Game."""
    return replace(row, value=Game(**row.value))


import_row: Callable[[RowResult], RowResult] = compose(parse_row, validate, to_game)


def game_key(game: Game) -> tuple[date, str, str]:
    """Identify a game by date, home team and away team."""
    return game.date, game.home_team, game.away_team


def check_duplicate(
    row: RowResult, existing_keys: frozenset[tuple[date, str, str]], first_line: Mapping[tuple, int]
) -> RowResult:
    """Fail the row if the game was imported before or appears earlier in the file."""
    if row.error:
        return row
    key = game_key(row.value)
    if key in existing_keys:
        return fail(row, "game was already imported")
    if first_line[key] != row.line:
        return fail(row, f"duplicate of line {first_line[key]}")
    return row


def mark_duplicates(rows: tuple[RowResult, ...], existing: Iterable[Game]) -> tuple[RowResult, ...]:
    """Mark every repeated game (in the file or already imported) as failed."""
    existing_keys = frozenset(map(game_key, existing))
    valid_rows = tuple(filter(lambda row: row.error is None, rows))
    # reversed: for repeated keys the first line of the file wins
    first_line = dict(reversed(tuple(map(lambda row: (game_key(row.value), row.line), valid_rows))))
    return tuple(map(lambda row: check_duplicate(row, existing_keys, first_line), rows))


def split_results(rows: tuple[RowResult, ...]) -> tuple[tuple[Game, ...], tuple[RowError, ...]]:
    """Split pipeline results into (valid_games, errors)."""
    games = tuple(map(lambda row: row.value, filter(lambda row: row.error is None, rows)))
    errors = tuple(map(lambda row: RowError(row.line, row.error), filter(lambda row: row.error, rows)))
    return games, errors


def import_games_from_csv(
    csv_text: str, existing: Iterable[Game] = ()
) -> tuple[tuple[Game, ...], tuple[RowError, ...]]:
    """Import games from CSV text and return (valid_games, errors). Never raises for bad data."""
    header, rows = read_rows(csv_text)
    header_error = check_header(header, rows)
    if header_error:
        return (), (header_error,)
    return split_results(mark_duplicates(tuple(map(import_row, rows)), existing))
