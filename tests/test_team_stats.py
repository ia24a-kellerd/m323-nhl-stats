from datetime import date

import pytest

from app import create_app
from models import Game, TeamRecord
from services.team_stats import (
    average,
    away_games,
    format_record,
    highest_scoring_game,
    home_games,
    longest_win_streak,
    team_stats,
    total_goals_against,
    total_goals_for,
)

# TOR results by date: W W OTL OTL W W W
G1 = Game(date(2025, 10, 1), "2025-26", "TOR", "MTL", 3, 1, "REG")
G2 = Game(date(2025, 10, 3), "2025-26", "BOS", "TOR", 2, 4, "REG")
G3 = Game(date(2025, 10, 5), "2025-26", "TOR", "BOS", 2, 3, "OT")
G4 = Game(date(2025, 10, 7), "2025-26", "MTL", "TOR", 5, 4, "SO")
G5 = Game(date(2025, 10, 9), "2025-26", "TOR", "NYR", 6, 1, "REG")
G6 = Game(date(2025, 10, 11), "2025-26", "NYR", "TOR", 1, 2, "REG")
G7 = Game(date(2025, 10, 13), "2025-26", "TOR", "MTL", 3, 0, "REG")
OTHER = Game(date(2025, 10, 2), "2025-26", "MTL", "BOS", 6, 3, "REG")

# intentionally not sorted by date
GAMES = (G5, G1, OTHER, G7, G3, G2, G6, G4)


def test_home_and_away_games():
    assert set(home_games(GAMES, "TOR")) == {G1, G3, G5, G7}
    assert set(away_games(GAMES, "TOR")) == {G2, G4, G6}


def test_format_record():
    assert format_record(TeamRecord(gp=4, w=3, l=0, otl=1)) == "3-0-1"


def test_total_goals_for_and_against():
    assert total_goals_for(GAMES, "TOR") == 24
    assert total_goals_against(GAMES, "TOR") == 13


def test_average_handles_zero_games():
    assert average(24, 7) == pytest.approx(3.4286, abs=1e-4)
    assert average(0, 0) == 0.0


def test_highest_scoring_game_ignores_games_of_other_teams():
    # OTHER also has 9 goals, but TOR did not play in it
    assert highest_scoring_game(GAMES, "TOR") == G4


def test_highest_scoring_game_tie_returns_earliest_game():
    later = Game(date(2025, 11, 1), "2025-26", "TOR", "BOS", 7, 2, "REG")
    earlier = Game(date(2025, 10, 1), "2025-26", "BOS", "TOR", 5, 4, "OT")

    assert highest_scoring_game((later, earlier), "TOR") == earlier


def test_longest_win_streak_uses_date_order_and_counts_streak_at_the_end():
    # W W OTL OTL W W W -> 3, an OT loss breaks the streak
    assert longest_win_streak(GAMES, "TOR") == 3


def test_longest_win_streak_without_wins():
    # NYR lost both games (G5, G6)
    assert longest_win_streak(GAMES, "NYR") == 0


def test_team_stats_for_team_with_games():
    stats = team_stats(GAMES, "TOR")

    assert stats.games_played == 7
    assert format_record(stats.home_record) == "3-0-1"
    assert format_record(stats.away_record) == "2-0-1"
    assert stats.avg_goals_for == pytest.approx(24 / 7)
    assert stats.avg_goals_against == pytest.approx(13 / 7)
    assert stats.highest_scoring_game == G4
    assert stats.longest_win_streak == 3


def test_team_stats_for_team_without_games():
    stats = team_stats(GAMES, "EDM")

    assert stats.games_played == 0
    assert stats.home_record == TeamRecord()
    assert stats.away_record == TeamRecord()
    assert stats.avg_goals_for == 0.0
    assert stats.avg_goals_against == 0.0
    assert stats.highest_scoring_game is None
    assert stats.longest_win_streak == 0


@pytest.fixture
def client():
    app = create_app()
    app.config["GAMES"] = list(GAMES)
    return app.test_client()


def test_team_page_shows_stats(client):
    html = client.get("/teams/tor").get_data(as_text=True)

    assert "<h1>TOR</h1>" in html
    assert "3-0-1" in html
    assert "3.43" in html


def test_team_page_for_team_without_games(client):
    response = client.get("/teams/EDM")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "0.00" in html
    assert "<td>0</td>" in html


def test_standings_link_to_team_page(client):
    html = client.get("/standings/").get_data(as_text=True)

    assert 'href="/teams/TOR"' in html
