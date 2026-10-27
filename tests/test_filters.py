from datetime import date

from models import Game
from services.filters import (
    FILTERS,
    build_predicates,
    by_date_range,
    by_result_type,
    by_season,
    by_team,
    filter_options,
    matches_all,
    newest_first,
)

GAME = Game(date(2025, 10, 5), "2025-26", "BOS", "TOR", 4, 3, "OT")


def test_by_team_matches_home_team():
    assert by_team("BOS")(GAME) is True


def test_by_team_matches_away_team():
    assert by_team("TOR")(GAME) is True


def test_by_team_rejects_other_team():
    assert by_team("MTL")(GAME) is False


def test_by_season():
    assert by_season("2025-26")(GAME) is True
    assert by_season("2024-25")(GAME) is False


def test_by_result_type():
    assert by_result_type("OT")(GAME) is True
    assert by_result_type("REG")(GAME) is False


def test_by_date_range_includes_both_borders():
    assert by_date_range((date(2025, 10, 5), date(2025, 10, 5)))(GAME) is True


def test_by_date_range_open_ends():
    assert by_date_range((None, date(2025, 10, 4)))(GAME) is False
    assert by_date_range((date(2025, 10, 6), None))(GAME) is False
    assert by_date_range((date(2025, 10, 1), None))(GAME) is True


def test_matches_all_requires_every_predicate():
    assert matches_all((by_team("TOR"), by_result_type("OT")))(GAME) is True
    assert matches_all((by_team("TOR"), by_result_type("SO")))(GAME) is False


def test_matches_all_without_predicates_matches_everything():
    assert matches_all(())(GAME) is True


def test_build_predicates_ignores_empty_values():
    params = {"team": "TOR", "season": "", "result_type": "", "date_range": None}

    predicates = build_predicates(params)

    assert len(predicates) == 1
    assert predicates[0](GAME) is True


def test_filters_dict_contains_all_factories():
    assert FILTERS == {
        "team": by_team,
        "season": by_season,
        "result_type": by_result_type,
        "date_range": by_date_range,
    }


def test_filter_options_lists_teams_and_seasons_sorted():
    games = (GAME, Game(date(2024, 10, 5), "2024-25", "MTL", "BOS", 1, 0, "REG"))

    assert filter_options(games) == {"teams": ("BOS", "MTL", "TOR"), "seasons": ("2024-25", "2025-26")}


def test_newest_first():
    older = Game(date(2025, 10, 1), "2025-26", "MTL", "BOS", 1, 0, "REG")

    assert newest_first((older, GAME)) == (GAME, older)
