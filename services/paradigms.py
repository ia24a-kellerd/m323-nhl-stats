"""The same task in three paradigms: the points of one team.

Only for comparison (portfolio A1A). The app uses the functional version in services/standings.py.
"""

from __future__ import annotations

from collections.abc import Iterable

from models import Game
from services.standings import team_record


# --- object-oriented: state and behavior together in an object, state is changed ---


class TeamSeason:
    """Mutable season of one team that collects its games."""

    def __init__(self, team: str) -> None:
        self.team = team
        self.wins = 0
        self.losses = 0
        self.ot_losses = 0

    def add_game(self, game: Game) -> None:
        """Count the game for this team; games of other teams are ignored."""
        if self.team == game.home_team:
            own_goals, other_goals = game.home_goals, game.away_goals
        elif self.team == game.away_team:
            own_goals, other_goals = game.away_goals, game.home_goals
        else:
            return

        if own_goals > other_goals:
            self.wins += 1
        elif game.result_type in {"OT", "SO"}:
            self.ot_losses += 1
        else:
            self.losses += 1

    def points(self) -> int:
        """Standings points: W = 2, OTL = 1, L = 0."""
        return self.wins * 2 + self.ot_losses


def points_object_oriented(games: Iterable[Game], team: str) -> int:
    """Calculate the points with a TeamSeason object."""
    season = TeamSeason(team)
    for game in games:
        season.add_game(game)
    return season.points()


# --- procedural: one function, step by step with a loop and local variables ---


def points_procedural(games: Iterable[Game], team: str) -> int:
    """Calculate the points with a loop and local variables."""
    points = 0
    for game in games:
        if game.home_team == team:
            won = game.home_goals > game.away_goals
        elif game.away_team == team:
            won = game.away_goals > game.home_goals
        else:
            continue

        if won:
            points += 2
        elif game.result_type == "OT" or game.result_type == "SO":
            points += 1
    return points


# --- functional: existing pure functions, reduce over immutable TeamRecords ---


def points_functional(games: Iterable[Game], team: str) -> int:
    """Calculate the points with team_record (reduce + add_game) from services/standings.py."""
    return team_record(games, team).pts
