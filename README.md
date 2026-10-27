# m323-nhl-stats

Flask app for NHL game results and statistics with CSV import. School project for module 323
(functional programming): the business logic is written as small pure functions on immutable data
(`@dataclass(frozen=True)`, tuples) with `map`, `filter`, `reduce`, lambdas and function composition.

## Features

- **Data folder** (`data/games/`): every `*.csv` file in this folder is loaded at startup (sorted by file name,
  games that appear in an earlier file are skipped). Add more files and restart the app or click
  **Reload folder** on the import page. `data/games/games_2025-26.csv` contains the 1312 games of the
  2025-26 regular season.
- **League overview** (`/`, start page): games, teams, goals per game, home win rate, share of OT and SO games,
  shutouts, top 5 in points, offense, defense and winning streaks, highest-scoring game and biggest win.
- **CSV import** (`/import`): upload a CSV with game results in addition to the data folder. Every line goes through a composed pipeline
  (`read_rows -> parse_row -> validate -> to_game`). Invalid lines are rejected and shown with line number and reason
  (missing columns or values, invalid date, non-numeric or negative goals, tied score, invalid result type,
  OT/SO game not decided by one goal, same team twice, duplicate or already imported game).
- **Game list with filters** (`/games`, newest first): filter by team, season, result type (REG/OT/SO) and date range.
  The filters are combined as a declarative predicate pipeline.
- **Standings** (`/standings`): GP, W, L, OTL, PTS, P% (points percentage), GF, GA, DIFF per team. Win = 2 points, OT/SO loss = 1,
  regulation loss = 0. Tiebreakers: points, wins, goal difference, goals for (all descending), then team (A-Z).
- **Team statistics** (`/teams/<abbr>`, linked everywhere): points and P%, form of the last 5 games, current and
  longest winning streak, home/away, OT/SO and one-goal records, goals for and against per game, shutouts,
  highest-scoring game, biggest win and loss, head-to-head record against every opponent and the full game log.
- **CSV export** (`/standings/export.csv`): download the current standings.

The games are kept in memory only (no database). After a restart only the files in `data/games/` are loaded again,
uploaded files are gone.

## CSV format

```csv
date,season,home_team,away_team,home_goals,away_goals,result_type
2025-10-07,2025-26,FLA,CHI,3,2,REG
2025-10-08,2025-26,EDM,CGY,3,4,SO
```

`result_type` is `REG`, `OT` or `SO`. `data/sample_games.csv` contains 60 example games of 8 teams.
Files must be UTF-8 (with or without BOM, e.g. saved from Excel).

## Installation

Requires Python 3.12.

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
flask --app app:create_app run
```

or `python app.py`. Open http://127.0.0.1:5000. The games from `data/games/` are already loaded.

## Tests

```bash
pytest
```

`tests/test_standings_characterization.py` locks in the standings results from before the refactorings.

## Benchmark

```bash
python scripts/generate_games.py                               # creates data/large_games.csv (50'000 games, seed 323)
python scripts/benchmark.py                                    # old (linear scan) vs. new (index dict + cache)
python scripts/benchmark.py --markdown docs/benchmark.md       # also writes the results to docs/benchmark.md
```

The last measured results are in [docs/benchmark.md](docs/benchmark.md).

## Project structure

```
app.py                  Flask app factory, loads data/games, registers the blueprints
models.py               immutable domain models: Game, TeamRecord, TeamStats, GameLogEntry, LeagueStats
routes/                 Flask blueprints, only HTTP (read request, call service, render template)
  league_routes.py      / (league overview)
  import_routes.py      /import, /import/reload
  games_routes.py       /games
  standings_routes.py   /standings, /standings/export.csv
  teams_routes.py       /teams/<abbr>
services/               business logic as pure functions
  importer.py           CSV import pipeline and validation
  filters.py            predicate factories for the game filters
  standings.py          standings with reduce, index_by_team, lru_cache
  team_stats.py         team statistics with map/filter/reduce
  league_stats.py       league overview statistics
  loader.py             loads all CSV files of the data folder
  export.py             standings_to_csv
  functional.py         generic helpers (compose)
  paradigms.py          points of a team in OO, procedural and functional style (comparison only)
templates/              Jinja2 templates (base layout, macros, one template per page)
static/style.css        plain CSS, light and dark theme
data/games/             CSV files loaded at startup (games_2025-26.csv)
data/                   sample_games.csv for the upload (large_games.csv is generated and not in git)
scripts/                generate_games.py, benchmark.py
docs/                   benchmark.md
tests/                  pytest tests
```
