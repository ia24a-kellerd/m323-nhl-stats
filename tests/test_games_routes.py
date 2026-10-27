from datetime import date

import pytest

from app import create_app
from models import Game

GAMES = [
    Game(date(2025, 10, 1), "2025-26", "TOR", "MTL", 3, 2, "REG"),
    Game(date(2025, 10, 5), "2025-26", "BOS", "TOR", 4, 3, "OT"),
    Game(date(2025, 10, 10), "2025-26", "MTL", "BOS", 1, 2, "SO"),
    Game(date(2025, 10, 15), "2025-26", "TOR", "BOS", 5, 1, "REG"),
]


@pytest.fixture
def client():
    app = create_app(games_dir=None)
    app.config["GAMES"] = list(GAMES)
    return app.test_client()


def shown_dates(response) -> list[str]:
    """Return the game dates that appear in the rendered table."""
    html = response.get_data(as_text=True)
    return [str(game.date) for game in GAMES if f"<td>{game.date}</td>" in html]


def test_no_filter_shows_all_games(client):
    response = client.get("/games/")

    assert response.status_code == 200
    assert shown_dates(response) == ["2025-10-01", "2025-10-05", "2025-10-10", "2025-10-15"]


def test_team_filter_matches_home_and_away_games(client):
    response = client.get("/games/?team=tor")

    assert shown_dates(response) == ["2025-10-01", "2025-10-05", "2025-10-15"]


def test_combined_team_and_result_type_filter(client):
    response = client.get("/games/?team=TOR&result_type=OT")

    assert shown_dates(response) == ["2025-10-05"]


def test_date_range_includes_both_borders(client):
    response = client.get("/games/?date_from=2025-10-05&date_to=2025-10-10")

    assert shown_dates(response) == ["2025-10-05", "2025-10-10"]


def test_empty_filters_are_ignored(client):
    response = client.get("/games/?team=&season=&result_type=&date_from=&date_to=")

    assert len(shown_dates(response)) == 4


def test_invalid_date_shows_error_instead_of_crash(client):
    response = client.get("/games/?date_from=not-a-date")

    assert response.status_code == 200
    assert "Dates must have the format YYYY-MM-DD." in response.get_data(as_text=True)
