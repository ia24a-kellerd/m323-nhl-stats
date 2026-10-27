"""Statistics for a single team, built with map/filter/reduce pipelines."""

from __future__ import annotations

from collections.abc import Iterable
from functools import reduce

from models import Game, TeamRecord, TeamStats
from services.standings import games_of_team, goals_for_and_against, result_for_team, team_record


def home_games(games: Iterable[Game], team: str) -> tuple[Game, ...]:
    """Return the games the team played at home."""
    return tuple(filter(lambda g: g.home_team == team, games))


def away_games(games: Iterable[Game], team: str) -> tuple[Game, ...]:
    """Return the games the team played away."""
    return tuple(filter(lambda g: g.away_team == team, games))


def format_record(record: TeamRecord) -> str:
    """Format a record as W-L-OTL, e.g. 5-3-1."""
    return f"{record.w}-{record.l}-{record.otl}"


def total_goals_for(games: Iterable[Game], team: str) -> int:
    """Sum of goals the team scored: filter team games -> map to goals for -> reduce to sum."""
    return reduce(
        lambda total, goals: total + goals,
        map(lambda g: goals_for_and_against(g, team)[0], games_of_team(games, team)),
        0,
    )


def total_goals_against(games: Iterable[Game], team: str) -> int:
    """Sum of goals the team conceded: filter team games -> map to goals against -> reduce to sum."""
    return reduce(
        lambda total, goals: total + goals,
        map(lambda g: goals_for_and_against(g, team)[1], games_of_team(games, team)),
        0,
    )


def average(total: int, count: int) -> float:
    """Return total / count, or 0.0 if there is nothing to divide."""
    return total / count if count else 0.0


def highest_scoring_game(games: Iterable[Game], team: str) -> Game | None:
    """Return the team's game with the most total goals (earliest one on a tie), or None."""
    by_date = sorted(games_of_team(games, team), key=lambda g: g.date)
    return max(by_date, key=lambda g: g.home_goals + g.away_goals, default=None)


def longest_win_streak(games: Iterable[Game], team: str) -> int:
    """Return the longest run of consecutive wins, with reduce over (current, best)."""
    wins = map(
        lambda g: result_for_team(g, team) == "W",
        sorted(games_of_team(games, team), key=lambda g: g.date),
    )
    _, best = reduce(
        lambda streak, won: (streak[0] + 1, max(streak[1], streak[0] + 1)) if won else (0, streak[1]),
        wins,
        (0, 0),
    )
    return best


def team_stats(games: Iterable[Game], team: str) -> TeamStats:
    """Collect all statistics of one team."""
    games = tuple(games)
    games_played = len(games_of_team(games, team))
    return TeamStats(
        team=team,
        games_played=games_played,
        home_record=team_record(home_games(games, team), team),
        away_record=team_record(away_games(games, team), team),
        avg_goals_for=average(total_goals_for(games, team), games_played),
        avg_goals_against=average(total_goals_against(games, team), games_played),
        highest_scoring_game=highest_scoring_game(games, team),
        longest_win_streak=longest_win_streak(games, team),
    )
