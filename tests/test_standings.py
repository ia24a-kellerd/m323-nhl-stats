from datetime import date

import pytest

from models import Game
from services.standings import (
    calculate_standings,
    games_of_team,
    goals_for_and_against,
    points_for,
    result_for_team,
    teams_in,
)


def test_calculate_standings_includes_ot_loss_point():
    games = [
        Game(date(2025, 10, 1), "2025-26", "TOR", "MTL", 4, 3, "OT"),
        Game(date(2025, 10, 2), "2025-26", "MTL", "TOR", 2, 1, "REG"),
    ]

    standings = calculate_standings(games)
    by_team = {row["TEAM"]: row for row in standings}

    assert by_team["TOR"]["GP"] == 2
    assert by_team["TOR"]["W"] == 1
    assert by_team["TOR"]["L"] == 1
    assert by_team["TOR"]["OTL"] == 0
    assert by_team["TOR"]["PTS"] == 2

    assert by_team["MTL"]["GP"] == 2
    assert by_team["MTL"]["W"] == 1
    assert by_team["MTL"]["L"] == 0
    assert by_team["MTL"]["OTL"] == 1
    assert by_team["MTL"]["PTS"] == 3


HOME_WIN_REG = Game(date(2025, 10, 1), "2025-26", "TOR", "MTL", 4, 2, "REG")
AWAY_WIN_OT = Game(date(2025, 10, 2), "2025-26", "BOS", "TOR", 2, 3, "OT")
HOME_WIN_SO = Game(date(2025, 10, 3), "2025-26", "MTL", "BOS", 3, 2, "SO")


def test_teams_in_keeps_order_of_first_appearance_without_duplicates():
    assert teams_in([HOME_WIN_REG, AWAY_WIN_OT, HOME_WIN_SO]) == ("TOR", "MTL", "BOS")


def test_teams_in_empty_list():
    assert teams_in([]) == ()


def test_games_of_team_returns_home_and_away_games():
    games = [HOME_WIN_REG, AWAY_WIN_OT, HOME_WIN_SO]

    assert games_of_team(games, "TOR") == (HOME_WIN_REG, AWAY_WIN_OT)
    assert games_of_team(games, "NYR") == ()


def test_goals_for_and_against_from_both_sides():
    assert goals_for_and_against(HOME_WIN_REG, "TOR") == (4, 2)
    assert goals_for_and_against(HOME_WIN_REG, "MTL") == (2, 4)


def test_goals_for_and_against_rejects_team_not_in_game():
    with pytest.raises(ValueError):
        goals_for_and_against(HOME_WIN_REG, "BOS")


def test_result_for_team_regulation():
    assert result_for_team(HOME_WIN_REG, "TOR") == "W"
    assert result_for_team(HOME_WIN_REG, "MTL") == "L"


def test_result_for_team_overtime_and_shootout_loss():
    assert result_for_team(AWAY_WIN_OT, "TOR") == "W"
    assert result_for_team(AWAY_WIN_OT, "BOS") == "OTL"
    assert result_for_team(HOME_WIN_SO, "BOS") == "OTL"


def test_points_for():
    assert points_for("W") == 2
    assert points_for("OTL") == 1
    assert points_for("L") == 0
