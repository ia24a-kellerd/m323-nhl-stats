# Benchmark: standings before and after optimization

Measured on 2026-10-27 with `python scripts/benchmark.py`.

- Data: `data/large_games.csv` (50000 games, 32 teams, generated with `scripts/generate_games.py`, seed 323)
- Method: `timeit`, old and new measured alternately, best of 10 rounds with 1 calls each, time per call
- Python 3.12.5 on Windows 11 (AMD64)

| Measurement | old: linear scan (ms) | new: index dict (ms) | speedup |
|---|---:|---:|---:|
| 1. full standings (no cache) | 346.8 | 240.4 | 1.4x |
| 2. games of all 32 teams | 334.6 | 23.0 | 14.5x |
| 3. standings, repeated call (lru_cache) | 358.8 | 5.9 | 60.8x |

## What changed

- **old**: `teams_in` + `games_of_team` per team. Every team scans all games: 32 teams x 50000 games.
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
.venv\Scripts\python scripts\generate_games.py
.venv\Scripts\python scripts\benchmark.py --markdown docs\benchmark.md
```
