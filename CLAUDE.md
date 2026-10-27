# CLAUDE.md

Project rules for Claude Code in this repository.

## Context

- This is a school project for module 323 (functional programming) using Flask.
- The app imports NHL game results from CSV and shows games, standings, team and league statistics.

## Project structure

- `app.py` – Flask app factory, loads all CSV files of `data/games/`, keeps the games in memory (`app.config["GAMES"]`).
  `create_app(games_dir=None)` starts with no games (used in tests).
- `models.py` – immutable domain models (frozen dataclasses).
- `services/` – business logic (import, loader, filters, standings, team and league stats, export).
- `routes/` – Flask blueprints (league overview, import, games, standings, teams).
- `templates/` – Jinja2 templates with a shared `base.html` and `_macros.html`; `static/style.css` (plain CSS).
- `data/games/` – CSV files loaded at startup; `data/sample_games.csv` – sample data for the upload.
- `tests/` – pytest tests.

## Rules

- Domain data is immutable: use `@dataclass(frozen=True)` and tuples instead of lists where data is passed between functions.
- Business logic lives in `services/` as small pure functions with type hints and short docstrings.
- Routes only handle HTTP: read the request, call services, render the template.
- Do not add features, libraries or refactorings that were not asked for in the current prompt.
- Every change must keep all pytest tests green. Run `pytest` before committing.
- Exactly one commit per prompt, with the commit message given in the prompt.

## Commands (Windows)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
flask --app app:create_app run
pytest
```
