"""Statistics for a single team, built with map/filter/reduce pipelines."""

from __future__ import annotations

from collections.abc import Iterable
from functools import reduce
from itertools import takewhile

from models import Game, GameLogEntry, TeamRecord, TeamStats
from services.standings import (
    Result,
    games_of_team,
    goals_for_and_against,
    record_from_games,
    result_for_team,
    team_record,
)


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


def sorted_by_date(games: Iterable[Game]) -> tuple[Game, ...]:
    """Return the games sorted by date (stable for games on the same day)."""
    return tuple(sorted(games, key=lambda g: g.date))


def results_by_date(games: Iterable[Game], team: str) -> tuple[Result, ...]:
    """Return the team's results (W, L, OTL) in date order."""
    return tuple(map(lambda g: result_for_team(g, team), sorted_by_date(games_of_team(games, team))))


def form(games: Iterable[Game], team: str, count: int = 5) -> tuple[Result, ...]:
    """Return the results of the last `count` games, oldest first."""
    return results_by_date(games, team)[-count:]


def current_streak(games: Iterable[Game], team: str) -> str:
    """Return the running streak like W3 or OTL1, '-' without games."""
    results = results_by_date(games, team)
    if not results:
        return "-"
    last = results[-1]
    return f"{last}{len(tuple(takewhile(lambda result: result == last, reversed(results))))}"


def margin(game: Game, team: str) -> int:
    """Goals for minus goals against from the team's point of view."""
    goals_for, goals_against = goals_for_and_against(game, team)
    return goals_for - goals_against


def overtime_games(games: Iterable[Game], team: str) -> tuple[Game, ...]:
    """Return the team's games decided in OT or SO."""
    return tuple(filter(lambda g: g.result_type in {"OT", "SO"}, games_of_team(games, team)))


def one_goal_games(games: Iterable[Game], team: str) -> tuple[Game, ...]:
    """Return the team's games decided by exactly one goal."""
    return tuple(filter(lambda g: abs(margin(g, team)) == 1, games_of_team(games, team)))


def count_shutouts(games: Iterable[Game], team: str) -> int:
    """Number of games in which the opponent did not score."""
    return len(tuple(filter(lambda g: goals_for_and_against(g, team)[1] == 0, games_of_team(games, team))))


def count_shutout_losses(games: Iterable[Game], team: str) -> int:
    """Number of games in which the team did not score."""
    return len(tuple(filter(lambda g: goals_for_and_against(g, team)[0] == 0, games_of_team(games, team))))


def biggest_win(games: Iterable[Game], team: str) -> Game | None:
    """Return the win with the largest margin (earliest one on a tie), or None."""
    wins = filter(lambda g: margin(g, team) > 0, sorted_by_date(games_of_team(games, team)))
    return max(wins, key=lambda g: margin(g, team), default=None)


def biggest_loss(games: Iterable[Game], team: str) -> Game | None:
    """Return the loss with the largest margin (earliest one on a tie), or None."""
    losses = filter(lambda g: margin(g, team) < 0, sorted_by_date(games_of_team(games, team)))
    return min(losses, key=lambda g: margin(g, team), default=None)


def opponent(game: Game, team: str) -> str:
    """Return the other team of the game."""
    return game.away_team if game.home_team == team else game.home_team


def head_to_head(games: Iterable[Game], team: str) -> tuple[tuple[str, TeamRecord], ...]:
    """Return (opponent, record against this opponent) for every opponent, sorted by name."""
    team_games = games_of_team(games, team)
    opponents = sorted(set(map(lambda g: opponent(g, team), team_games)))
    return tuple(
        map(
            lambda other: (other, record_from_games(filter(lambda g: opponent(g, team) == other, team_games), team)),
            opponents,
        )
    )


def log_entry(game: Game, team: str) -> GameLogEntry:
    """Describe one game from the team's point of view."""
    goals_for, goals_against = goals_for_and_against(game, team)
    return GameLogEntry(
        date=game.date,
        opponent=opponent(game, team),
        at_home=game.home_team == team,
        goals_for=goals_for,
        goals_against=goals_against,
        result=result_for_team(game, team),
        result_type=game.result_type,
    )


def game_log(games: Iterable[Game], team: str) -> tuple[GameLogEntry, ...]:
    """Return all games of the team, newest first."""
    return tuple(map(lambda g: log_entry(g, team), reversed(sorted_by_date(games_of_team(games, team)))))


def team_stats(games: Iterable[Game], team: str) -> TeamStats:
    """Collect all statistics of one team."""
    games = tuple(games)
    games_played = len(games_of_team(games, team))
    return TeamStats(
        team=team,
        games_played=games_played,
        record=team_record(games, team),
        home_record=team_record(home_games(games, team), team),
        away_record=team_record(away_games(games, team), team),
        avg_goals_for=average(total_goals_for(games, team), games_played),
        avg_goals_against=average(total_goals_against(games, team), games_played),
        highest_scoring_game=highest_scoring_game(games, team),
        longest_win_streak=longest_win_streak(games, team),
        current_streak=current_streak(games, team),
        form=form(games, team),
        overtime_record=record_from_games(overtime_games(games, team), team),
        one_goal_record=record_from_games(one_goal_games(games, team), team),
        shutouts=count_shutouts(games, team),
        shutout_losses=count_shutout_losses(games, team),
        biggest_win=biggest_win(games, team),
        biggest_loss=biggest_loss(games, team),
        head_to_head=head_to_head(games, team),
        game_log=game_log(games, team),
    )
