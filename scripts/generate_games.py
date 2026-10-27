"""Generate a large CSV with random but valid NHL games for benchmarks.

Usage: python scripts/generate_games.py [--games 50000] [--seed 323] [--output data/large_games.csv]
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

TEAMS = (
    "ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL",
    "DAL", "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD",
    "NSH", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", "SJS",
    "STL", "TBL", "TOR", "UTA", "VAN", "VGK", "WPG", "WSH",
)
HEADER = ("date", "season", "home_team", "away_team", "home_goals", "away_goals", "result_type")
START_DATE = date(2025, 10, 7)


def season_of(day: date) -> str:
    """Return the season label, e.g. 2025-26 (a season starts in July)."""
    start_year = day.year if day.month >= 7 else day.year - 1
    return f"{start_year}-{(start_year + 1) % 100:02d}"


def random_score(rng: random.Random) -> tuple[int, int, str]:
    """Return (home_goals, away_goals, result_type) like a real NHL game."""
    result_type = rng.choices(("REG", "OT", "SO"), weights=(75, 16, 9))[0]
    if result_type == "REG":
        winner = rng.randint(1, 7)
        loser = rng.randint(0, winner - 1)
    else:
        loser = rng.randint(0, 5)
        winner = loser + 1
    return (winner, loser, result_type) if rng.random() < 0.55 else (loser, winner, result_type)


def generate_rows(count: int, rng: random.Random) -> list[tuple]:
    """Generate games: every day each team plays once, so (date, home, away) is unique."""
    rows = []
    day = START_DATE
    while len(rows) < count:
        teams = list(TEAMS)
        rng.shuffle(teams)
        for home, away in zip(teams[0::2], teams[1::2]):
            if len(rows) == count:
                break
            home_goals, away_goals, result_type = random_score(rng)
            rows.append((day.isoformat(), season_of(day), home, away, home_goals, away_goals, result_type))
        day += timedelta(days=1)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=323)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "large_games.csv")
    args = parser.parse_args()

    rows = generate_rows(args.games, random.Random(args.seed))
    with args.output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(HEADER)
        writer.writerows(rows)
    print(f"{len(rows)} games written to {args.output}")


if __name__ == "__main__":
    main()
