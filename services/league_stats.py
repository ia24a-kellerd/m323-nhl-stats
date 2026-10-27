"""Statistics over all games (overview page), built with map/filter/reduce."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from functools import reduce

from models import Game, LeagueStats
from services.standings import calculate_standings, index_by_team
from services.team_stats import average, longest_win_streak

TOP = 5


def total_goals(games: Iterable[Game]) -> int:
    """Sum of all goals: map to goals per game -> reduce to sum."""
    return reduce(lambda total, goals: total + goals, map(lambda g: g.home_goals + g.away_goals, games), 0)


def share(games: tuple[Game, ...], predicate: Callable[[Game], bool]) -> float:
    """Share (0.0-1.0) of games matching the predicate, 0.0 without games."""
    return average(len(tuple(filter(predicate, games))), len(games))


def goal_margin(game: Game) -> int:
    """Difference between winner and loser goals."""
    return abs(game.home_goals - game.away_goals)


def highest_scoring_game(games: Iterable[Game]) -> Game | None:
    """Game with the most goals (earliest one on a tie)."""
    by_date = sorted(games, key=lambda g: g.date)
    return max(by_date, key=lambda g: g.home_goals + g.away_goals, default=None)


def biggest_win(games: Iterable[Game]) -> Game | None:
    """Game with the largest goal margin (earliest one on a tie)."""
    return max(sorted(games, key=lambda g: g.date), key=goal_margin, default=None)


def seasons(games: Iterable[Game]) -> tuple[str, ...]:
    """All seasons, sorted."""
    return tuple(sorted(set(map(lambda g: g.season, games))))


def top(entries: Iterable[tuple[str, float]], descending: bool = True) -> tuple[tuple[str, float], ...]:
    """The TOP entries by value (ties sorted by team name)."""
    sign = -1 if descending else 1
    return tuple(sorted(entries, key=lambda entry: (sign * entry[1], entry[0])))[:TOP]


def league_stats(games: Iterable[Game]) -> LeagueStats:
    """Collect all statistics over the games."""
    games = tuple(games)
    rows = calculate_standings(games)
    index = index_by_team(games)
    dates = tuple(map(lambda g: g.date, games))
    return LeagueStats(
        games=len(games),
        teams=len(index),
        seasons=seasons(games),
        first_date=min(dates, default=None),
        last_date=max(dates, default=None),
        goals_per_game=average(total_goals(games), len(games)),
        home_win_pct=share(games, lambda g: g.home_goals > g.away_goals),
        ot_pct=share(games, lambda g: g.result_type == "OT"),
        so_pct=share(games, lambda g: g.result_type == "SO"),
        shutouts=len(tuple(filter(lambda g: min(g.home_goals, g.away_goals) == 0, games))),
        highest_scoring_game=highest_scoring_game(games),
        biggest_win=biggest_win(games),
        top_points=tuple(map(lambda row: (row["TEAM"], row["PTS"]), rows[:TOP])),
        top_offense=top(map(lambda row: (row["TEAM"], row["GF"] / row["GP"]), rows)),
        top_defense=top(map(lambda row: (row["TEAM"], row["GA"] / row["GP"]), rows), descending=False),
        top_streaks=top(map(lambda item: (item[0], longest_win_streak(item[1], item[0])), index.items())),
    )
