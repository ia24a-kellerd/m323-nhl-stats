from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from models import Game, TeamRecord
from services.standings import (
    add_game,
    calculate_standings,
    games_of_team,
    goals_for_and_against,
    points_for,
    result_for_team,
    standings_sort_key,
    team_record,
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


def test_team_record_computes_points_and_diff():
    record = TeamRecord(gp=4, w=2, l=1, otl=1, gf=10, ga=12)

    assert record.pts == 5
    assert record.diff == -2


def test_team_record_is_immutable():
    with pytest.raises(FrozenInstanceError):
        TeamRecord().w = 1


def test_add_game_returns_new_record_and_keeps_old_one():
    empty = TeamRecord()

    updated = add_game(empty, AWAY_WIN_OT, "BOS")

    assert updated == TeamRecord(gp=1, otl=1, gf=2, ga=3)
    assert empty == TeamRecord()


def test_team_record_reduces_all_games_of_team():
    games = [HOME_WIN_REG, AWAY_WIN_OT, HOME_WIN_SO]

    assert team_record(games, "TOR") == TeamRecord(gp=2, w=2, gf=7, ga=4)
    assert team_record(games, "NYR") == TeamRecord()


def test_standings_rows_are_read_only():
    row = calculate_standings([HOME_WIN_REG])[0]

    with pytest.raises(TypeError):
        row["PTS"] = 99


def row(team, pts, w, diff, gf):
    """Build a minimal standings row for sort key tests."""
    return {"TEAM": team, "PTS": pts, "W": w, "DIFF": diff, "GF": gf}


def sort_teams(rows):
    return [r["TEAM"] for r in sorted(rows, key=standings_sort_key)]


def test_sort_by_points_first():
    assert sort_teams([row("AAA", 10, 9, 9, 9), row("BBB", 12, 1, -5, 1)]) == ["BBB", "AAA"]


def test_tied_points_more_wins_first():
    # BBB has more goal difference, but AAA wins the tiebreaker on wins
    assert sort_teams([row("BBB", 10, 4, 8, 20), row("AAA", 10, 5, 0, 10)]) == ["AAA", "BBB"]


def test_tied_points_and_wins_better_goal_difference_first():
    assert sort_teams([row("AAA", 10, 5, -1, 30), row("BBB", 10, 5, 3, 10)]) == ["BBB", "AAA"]


def test_tied_up_to_goal_difference_more_goals_for_first():
    assert sort_teams([row("AAA", 10, 5, 2, 12), row("BBB", 10, 5, 2, 15)]) == ["BBB", "AAA"]


def test_completely_tied_teams_sorted_alphabetically():
    assert sort_teams([row("TOR", 10, 5, 2, 12), row("BOS", 10, 5, 2, 12), row("MTL", 10, 5, 2, 12)]) == [
        "BOS",
        "MTL",
        "TOR",
    ]


def test_calculate_standings_breaks_points_tie_by_wins():
    # TOR: 2 W = 4 PTS (DIFF +2); BOS: 1 W + 2 OTL = 4 PTS (DIFF +7) -> TOR first because of more wins
    games = [
        Game(date(2025, 10, 1), "2025-26", "TOR", "MTL", 1, 0, "REG"),
        Game(date(2025, 10, 2), "2025-26", "TOR", "NYR", 1, 0, "REG"),
        Game(date(2025, 10, 3), "2025-26", "BOS", "MTL", 9, 0, "REG"),
        Game(date(2025, 10, 4), "2025-26", "BOS", "NYR", 0, 1, "OT"),
        Game(date(2025, 10, 5), "2025-26", "BOS", "MTL", 0, 1, "SO"),
    ]

    standings = calculate_standings(games)

    assert [(r["TEAM"], r["PTS"], r["W"], r["DIFF"]) for r in standings] == [
        ("TOR", 4, 2, 2),
        ("BOS", 4, 1, 7),
        ("NYR", 2, 1, 0),
        ("MTL", 2, 1, -9),
    ]
