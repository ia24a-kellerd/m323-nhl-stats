"""Declarative game filters built from small predicate factories."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import date

from models import Game

Predicate = Callable[[Game], bool]
DateRange = tuple[date | None, date | None]

DATE_ERROR = "Dates must have the format YYYY-MM-DD."


def by_team(team: str) -> Predicate:
    """Match games where the team played at home or away."""
    return lambda game: team in (game.home_team, game.away_team)


def by_season(season: str) -> Predicate:
    """Match games of one season."""
    return lambda game: game.season == season


def by_result_type(result_type: str) -> Predicate:
    """Match games that ended in REG, OT or SO."""
    return lambda game: game.result_type == result_type


def by_date_range(date_range: DateRange) -> Predicate:
    """Match games between two dates (both inclusive, None means open)."""
    date_from, date_to = date_range
    return lambda game: (date_from is None or game.date >= date_from) and (
        date_to is None or game.date <= date_to
    )


FILTERS: dict[str, Callable[..., Predicate]] = {
    "team": by_team,
    "season": by_season,
    "result_type": by_result_type,
    "date_range": by_date_range,
}


def read_filter_values(args: Mapping[str, str]) -> dict[str, str]:
    """Read and normalize the raw filter values from query parameters."""
    return {
        "team": args.get("team", "").strip().upper(),
        "season": args.get("season", "").strip(),
        "result_type": args.get("result_type", "").strip().upper(),
        "date_from": args.get("date_from", "").strip(),
        "date_to": args.get("date_to", "").strip(),
    }


def try_parse_date(text: str) -> date | None:
    """Parse a YYYY-MM-DD date, return None for empty or invalid text."""
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def date_error(values: Mapping[str, str]) -> str | None:
    """Return an error message if a non-empty date value is invalid."""
    texts = (values["date_from"], values["date_to"])
    invalid = any(map(lambda text: bool(text) and try_parse_date(text) is None, texts))
    return DATE_ERROR if invalid else None


def to_filter_params(values: Mapping[str, str]) -> dict[str, object]:
    """Convert normalized values into the parameters used by FILTERS."""
    date_range = (try_parse_date(values["date_from"]), try_parse_date(values["date_to"]))
    return {
        "team": values["team"],
        "season": values["season"],
        "result_type": values["result_type"],
        "date_range": date_range if any(date_range) else None,
    }


def build_predicates(params: Mapping[str, object]) -> tuple[Predicate, ...]:
    """Build one predicate per active (non-empty) filter parameter."""
    active = filter(lambda item: item[0] in FILTERS and item[1], params.items())
    return tuple(map(lambda item: FILTERS[item[0]](item[1]), active))


def matches_all(predicates: Iterable[Predicate]) -> Predicate:
    """Combine predicates into one that is true only if all are true."""
    predicates = tuple(predicates)
    return lambda game: all(predicate(game) for predicate in predicates)


def filter_games(games: Iterable[Game], params: Mapping[str, object]) -> tuple[Game, ...]:
    """Return the games that match all active filters."""
    return tuple(filter(matches_all(build_predicates(params)), games))
