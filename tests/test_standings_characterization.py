"""Characterization tests: lock in the current standings behavior before refactoring."""

from datetime import date
from pathlib import Path

from models import Game
from services.importer import import_games_from_csv
from services.standings import calculate_standings

SAMPLE_CSV = Path(__file__).resolve().parents[1] / "data" / "sample_games.csv"
COLUMNS = ("TEAM", "GP", "W", "L", "OTL", "PTS", "GF", "GA", "DIFF")


def to_tuples(standings) -> list[tuple]:
    """Convert standings rows into (TEAM, GP, W, L, OTL, PTS, GF, GA, DIFF) tuples."""
    return [tuple(row[column] for column in COLUMNS) for row in standings]


def test_standings_for_sample_csv():
    games, rejected = import_games_from_csv(SAMPLE_CSV.read_text(encoding="utf-8"))
    assert len(games) == 60
    assert rejected == []

    assert to_tuples(calculate_standings(games)) == [
        ("TOR", 15, 8, 0, 7, 23, 47, 46, 1),
        ("MTL", 15, 8, 1, 6, 22, 41, 35, 6),
        ("FLA", 15, 9, 2, 4, 22, 44, 39, 5),
        ("BUF", 15, 7, 2, 6, 20, 43, 38, 5),
        ("NYR", 15, 7, 3, 5, 19, 44, 47, -3),
        ("OTT", 15, 8, 5, 2, 18, 43, 42, 1),
        ("TBL", 15, 7, 4, 4, 18, 41, 48, -7),
        ("BOS", 15, 6, 4, 5, 17, 41, 49, -8),
    ]


def test_standings_with_ot_and_so_loss():
    games = [
        Game(date(2025, 10, 1), "2025-26", "TOR", "MTL", 4, 3, "OT"),
        Game(date(2025, 10, 2), "2025-26", "BOS", "TOR", 2, 1, "SO"),
        Game(date(2025, 10, 3), "2025-26", "MTL", "BOS", 5, 2, "REG"),
    ]

    assert to_tuples(calculate_standings(games)) == [
        ("MTL", 2, 1, 0, 1, 3, 8, 6, 2),
        ("TOR", 2, 1, 0, 1, 3, 5, 5, 0),
        ("BOS", 2, 1, 1, 0, 2, 4, 6, -2),
    ]


def test_standings_for_empty_game_list():
    assert to_tuples(calculate_standings([])) == []
