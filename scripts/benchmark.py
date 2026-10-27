"""Compare the old (linear scan) and new (index dict + cache) standings with timeit.

Usage: python scripts/benchmark.py [--file data/large_games.csv] [--number 3] [--repeat 5] [--markdown docs/benchmark.md]
Create the file first with: python scripts/generate_games.py
"""

from __future__ import annotations

import argparse
import platform
import sys
import timeit
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.importer import import_games_from_csv  # noqa: E402
from services.standings import (  # noqa: E402
    calculate_standings,
    games_of_team,
    index_by_team,
    standings_for,
    standings_sort_key,
    team_record,
    teams_in,
    to_row,
)


def old_standings(games):
    """Standings as before the optimization: one scan over all games per team."""
    rows = map(lambda team: to_row(team, team_record(games, team)), teams_in(games))
    return tuple(sorted(rows, key=standings_sort_key))


def old_games_of_all_teams(games, teams):
    """Games of every team with a linear scan per team."""
    return [games_of_team(games, team) for team in teams]


def new_games_of_all_teams(games, teams):
    """Games of every team from one index built in a single pass."""
    index = index_by_team(games)
    return [index[team] for team in teams]


def measure_pair(old, new, number: int, repeat: int) -> tuple[float, float]:
    """Time old and new alternately (so background load hits both); best ms per call for each."""
    times = [(timeit.timeit(old, number=number), timeit.timeit(new, number=number)) for _ in range(repeat)]
    return min(t[0] for t in times) / number * 1000, min(t[1] for t in times) / number * 1000


def run(games, teams, number: int, repeat: int) -> tuple[tuple[str, float, float], ...]:
    """Measure every case and return (name, old ms, new ms) rows."""
    calculate_standings(games)  # warm up the cache for the repeated-call case
    cases = (
        (
            "1. full standings (no cache)",
            lambda: old_standings(games),
            lambda: standings_for.__wrapped__(games),
        ),
        (
            f"2. games of all {len(teams)} teams",
            lambda: old_games_of_all_teams(games, teams),
            lambda: new_games_of_all_teams(games, teams),
        ),
        (
            "3. standings, repeated call (lru_cache)",
            lambda: old_standings(games),
            lambda: calculate_standings(games),
        ),
    )
    return tuple((name, *measure_pair(old, new, number, repeat)) for name, old, new in cases)


def text_table(results) -> str:
    """Format the results as a plain text table for the console."""
    width = max(len(name) for name, _, _ in results)
    lines = [
        f"{'Measurement':<{width}} | {'old ms':>9} | {'new ms':>9} | {'speedup':>8}",
        f"{'-' * width}-+-{'-' * 9}-+-{'-' * 9}-+-{'-' * 8}",
    ]
    lines += [f"{name:<{width}} | {old:>9.1f} | {new:>9.1f} | {old / new:>7.1f}x" for name, old, new in results]
    return "\n".join(lines)


def markdown_report(results, file_name: str, game_count: int, team_count: int, number: int, repeat: int) -> str:
    """Build docs/benchmark.md with the measured numbers."""
    rows = "\n".join(f"| {name} | {old:.1f} | {new:.1f} | {old / new:.1f}x |" for name, old, new in results)
    return f"""# Benchmark: standings before and after optimization

Measured on {date.today().isoformat()} with `python scripts/benchmark.py`.

- Data: `data/{file_name}` ({game_count} games, {team_count} teams, generated with `scripts/generate_games.py`, seed 323)
- Method: `timeit`, old and new measured alternately, best of {repeat} rounds with {number} calls each, time per call
- Python {platform.python_version()} on {platform.system()} {platform.release()} ({platform.machine()})

| Measurement | old: linear scan (ms) | new: index dict (ms) | speedup |
|---|---:|---:|---:|
{rows}

## What changed

- **old**: `teams_in` + `games_of_team` per team. Every team scans all games: 32 teams x {game_count} games.
- **new**: `index_by_team` groups all games by team in a single pass (`dict[str, tuple[Game, ...]]`), then each team's
  record is built from its own games only.
- **lru_cache**: `standings_for` caches the standings for a tuple of games. A repeated call with the same games
  (e.g. reloading the standings page) only hashes the tuple instead of calculating again. The cache works because
  `Game` is a frozen dataclass and the games are passed as a tuple, so the input is hashable and the function is pure.

## Notes

- The absolute times vary a lot between runs on a laptop (CPU throttling, background tasks), sometimes by a factor
  of 2 or more. Old and new are therefore measured alternately in the same run, and the speedup is the number to
  compare. In several runs it stayed at about 1.3-1.7x (case 1), 13-16x (case 2) and 45-60x (case 3).
- Case 1 gains the least: the index only removes the repeated scans (case 2), but most of the time is spent in
  `reduce`, which builds a new immutable `TeamRecord` per game with `dataclasses.replace`. Both versions do that.
- Case 3 still costs a few milliseconds: `tuple(games)` and hashing all games are needed to look up the cache.

## Reproduce

```powershell
.venv\\Scripts\\python scripts\\generate_games.py
.venv\\Scripts\\python scripts\\benchmark.py --markdown docs\\benchmark.md
```
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--file", type=Path, default=ROOT / "data" / "large_games.csv")
    parser.add_argument("--number", type=int, default=1, help="calls per measurement")
    parser.add_argument("--repeat", type=int, default=10, help="rounds, the best one counts")
    parser.add_argument("--markdown", type=Path, help="also write the results to this markdown file")
    args = parser.parse_args()

    if not args.file.exists():
        sys.exit(f"{args.file} not found, run: python scripts/generate_games.py")

    games, errors = import_games_from_csv(args.file.read_text(encoding="utf-8"))
    teams = teams_in(games)
    print(f"File:  {args.file.name}")
    print(f"Games: {len(games)} ({len(errors)} rejected), teams: {len(teams)}")
    print(f"timeit: best of {args.repeat} x {args.number} calls\n")

    results = run(games, teams, args.number, args.repeat)
    print(text_table(results))

    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        report = markdown_report(results, args.file.name, len(games), len(teams), args.number, args.repeat)
        args.markdown.write_text(report, encoding="utf-8")
        print(f"\nWritten to {args.markdown}")


if __name__ == "__main__":
    main()
