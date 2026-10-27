# m323-nhl-stats

Starter Flask application for NHL results and standings with CSV import.

## Requirements

- Python 3.12
- pip

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
flask --app app:create_app run
```

Open:

- `/import` for CSV upload
- `/games` for game list
- `/standings` for standings table

Use `data/sample_games.csv` as sample import data.

## Tests

```bash
pytest
```
