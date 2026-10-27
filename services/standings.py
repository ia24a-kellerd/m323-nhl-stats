"""Standings calculation service."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from models import Game

Result = Literal["W", "L", "OTL"]

POINTS: dict[str, int] = {"W": 2, "OTL": 1, "L": 0}


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


def calculate_standings(games: list[Game]) -> list[dict[str, int | str]]:
    """Calculate standings by looping over teams and their games."""
    records: list[dict[str, int | str]] = []

    for team in teams_in(games):
        record: dict[str, int | str] = {
            "TEAM": team,
            "GP": 0,
            "W": 0,
            "L": 0,
            "OTL": 0,
            "PTS": 0,
            "GF": 0,
            "GA": 0,
            "DIFF": 0,
        }

        for game in games_of_team(games, team):
            result = result_for_team(game, team)
            goals_for, goals_against = goals_for_and_against(game, team)

            record["GP"] += 1
            record[result] += 1
            record["PTS"] += points_for(result)
            record["GF"] += goals_for
            record["GA"] += goals_against

        record["DIFF"] = record["GF"] - record["GA"]
        records.append(record)

    return sorted(records, key=lambda row: (row["PTS"], row["DIFF"], row["GF"]), reverse=True)
