"""Domain models for NHL statistics."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Game:
    """Represents a played NHL game."""

    date: date
    season: str
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    result_type: str
