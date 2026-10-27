from datetime import date

import pytest

from models import Game
from services.league_stats import biggest_win, highest_scoring_game, league_stats, share, top, total_goals

L1 = Game(date(2025, 10, 1), "2025-26", "TOR", "MTL", 3, 1, "REG")
L2 = Game(date(2025, 10, 2), "2025-26", "BOS", "TOR", 2, 3, "OT")
L3 = Game(date(2025, 10, 3), "2025-26", "MTL", "BOS", 0, 4, "REG")
L4 = Game(date(2025, 10, 4), "2025-26", "TOR", "BOS", 5, 4, "SO")
GAMES = (L1, L2, L3, L4)


def test_total_goals():
    assert total_goals(GAMES) == 22
    assert total_goals(()) == 0


def test_share():
    assert share(GAMES, lambda g: g.result_type == "REG") == 0.5
    assert share((), lambda g: True) == 0.0


def test_highest_scoring_game_and_biggest_win():
    assert highest_scoring_game(GAMES) == L4
    assert biggest_win(GAMES) == L3
    assert highest_scoring_game(()) is None


def test_top_sorts_by_value_then_name_and_limits_to_five():
    entries = [("F", 1), ("B", 3), ("A", 3), ("C", 2), ("D", 0), ("E", 5)]

    assert top(entries) == (("E", 5), ("A", 3), ("B", 3), ("C", 2), ("F", 1))
    assert top(entries, descending=False)[0] == ("D", 0)


def test_league_stats():
    stats = league_stats(GAMES)

    assert (stats.games, stats.teams, stats.seasons) == (4, 3, ("2025-26",))
    assert (stats.first_date, stats.last_date) == (date(2025, 10, 1), date(2025, 10, 4))
    assert stats.goals_per_game == 5.5
    assert (stats.home_win_pct, stats.ot_pct, stats.so_pct) == (0.5, 0.25, 0.25)
    assert stats.shutouts == 1
    assert stats.top_points == (("TOR", 6), ("BOS", 4), ("MTL", 0))
    assert [team for team, _ in stats.top_offense] == ["TOR", "BOS", "MTL"]
    assert stats.top_offense[0][1] == pytest.approx(11 / 3)
    assert [team for team, _ in stats.top_defense] == ["TOR", "BOS", "MTL"]
    assert stats.top_streaks == (("TOR", 3), ("BOS", 1), ("MTL", 0))


def test_league_stats_without_games():
    stats = league_stats(())

    assert stats.games == 0
    assert stats.goals_per_game == 0.0
    assert stats.first_date is None
    assert stats.highest_scoring_game is None
    assert stats.top_points == ()
