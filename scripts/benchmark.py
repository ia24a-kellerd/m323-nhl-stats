"""Measure the standings calculation and the team lookup with timeit.

Usage: python scripts/benchmark.py [--file data/large_games.csv] [--number 3] [--repeat 5]
Create the file first with: python scripts/generate_games.py
"""

from __future__ import annotations

import argparse
import sys
import timeit
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.importer import import_games_from_csv  # noqa: E402
from services.standings import calculate_standings, games_of_team, teams_in  # noqa: E402


def measure(statement, number: int, repeat: int) -> float:
    """Return the best time of one call in milliseconds."""
    return min(timeit.repeat(statement, number=number, repeat=repeat)) / number * 1000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--file", type=Path, default=ROOT / "data" / "large_games.csv")
    parser.add_argument("--number", type=int, default=3, help="calls per measurement")
    parser.add_argument("--repeat", type=int, default=5, help="measurements, the best one counts")
    args = parser.parse_args()

    if not args.file.exists():
        sys.exit(f"{args.file} not found, run: python scripts/generate_games.py")

    games, errors = import_games_from_csv(args.file.read_text(encoding="utf-8"))
    teams = teams_in(games)
    print(f"File:  {args.file.name}")
    print(f"Games: {len(games)} ({len(errors)} rejected), teams: {len(teams)}")
    print(f"timeit: best of {args.repeat} x {args.number} calls\n")

    results = (
        ("1. full standings", measure(lambda: calculate_standings(games), args.number, args.repeat)),
        (
            f"2. games_of_team for all {len(teams)} teams",
            measure(lambda: [games_of_team(games, team) for team in teams], args.number, args.repeat),
        ),
    )

    width = max(len(name) for name, _ in results)
    print(f"{'Measurement':<{width}} | {'ms per call':>11}")
    print(f"{'-' * width}-+-{'-' * 11}")
    for name, milliseconds in results:
        print(f"{name:<{width}} | {milliseconds:>11.1f}")


if __name__ == "__main__":
    main()
