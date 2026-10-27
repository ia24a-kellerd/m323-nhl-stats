"""Standings calculation service."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from functools import reduce
from types import MappingProxyType
from typing import Literal

from models import POINTS, Game, TeamRecord

Result = Literal["W", "L", "OTL"]
StandingsRow = Mapping[str, int | str]

RESULT_FIELDS: dict[str, str] = {"W": "w", "L": "l", "OTL": "otl"}


def teams_in(games: Iterable[Game]) -> tuple[str, ...]:
    """Return all teams in order of their first appearance (home before away)."""
    return tuple(dict.fromkeys(team for game in games for team in (game.home_team, game.away_team)))


def games_of_team(games: Iterable[Game], team: str) -> tuple[Game, ...]:
    """Return all games the team played at home or away."""
    return tuple(game for game in games if team in (game.home_team, game.away_team))


def goals_for_and_against(game: Game, team: str) -> tuple[int, int]:
    """Return (goals scored, goals conceded) from the team's point of view."""
    if team == game.home_team:
        return game.home_goals, game.away_goals
    if team == game.away_team:
        return game.away_goals, game.home_goals
    raise ValueError(f"{team} did not play in this game")


def result_for_team(game: Game, team: str) -> Result:
    """Return W, OTL (lost in OT/SO) or L (lost in regulation) for the team."""
    goals_for, goals_against = goals_for_and_against(game, team)
    if goals_for > goals_against:
        return "W"
    if game.result_type in {"OT", "SO"}:
        return "OTL"
    return "L"


def points_for(result: Result) -> int:
    """Return the standings points for a result: W = 2, OTL = 1, L = 0."""
    return POINTS[result]


def add_game(record: TeamRecord, game: Game, team: str) -> TeamRecord:
    """Return a new record with the game added; the given record is not changed."""
    result_field = RESULT_FIELDS[result_for_team(game, team)]
    goals_for, goals_against = goals_for_and_against(game, team)
    return replace(
        record,
        gp=record.gp + 1,
        gf=record.gf + goals_for,
        ga=record.ga + goals_against,
        **{result_field: getattr(record, result_field) + 1},
    )


def team_record(games: Iterable[Game], team: str) -> TeamRecord:
    """Fold all games of the team into one TeamRecord with reduce."""
    return reduce(
        lambda record, game: add_game(record, game, team),
        games_of_team(games, team),
        TeamRecord(),
    )


def ranking_key(entry: tuple[str, TeamRecord]) -> tuple[int, int, int]:
    """Sort key: points, then goal difference, then goals for."""
    _, record = entry
    return record.pts, record.diff, record.gf


def to_row(team: str, record: TeamRecord) -> StandingsRow:
    """Convert a TeamRecord into a read-only row for the template."""
    return MappingProxyType(
        {
            "TEAM": team,
            "GP": record.gp,
            "W": record.w,
            "L": record.l,
            "OTL": record.otl,
            "PTS": record.pts,
            "GF": record.gf,
            "GA": record.ga,
            "DIFF": record.diff,
        }
    )


def calculate_standings(games: Iterable[Game]) -> tuple[StandingsRow, ...]:
    """Calculate the standings sorted by points, goal difference and goals for."""
    games = tuple(games)
    entries = map(lambda team: (team, team_record(games, team)), teams_in(games))
    ranked = sorted(entries, key=ranking_key, reverse=True)
    return tuple(map(lambda entry: to_row(*entry), ranked))
