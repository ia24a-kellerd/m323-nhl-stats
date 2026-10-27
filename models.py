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


POINTS: dict[str, int] = {"W": 2, "OTL": 1, "L": 0}


@dataclass(frozen=True)
class TeamRecord:
    """Season record of one team: games played, wins, losses, OT/SO losses and goals."""

    gp: int = 0
    w: int = 0
    l: int = 0
    otl: int = 0
    gf: int = 0
    ga: int = 0

    @property
    def pts(self) -> int:
        """Standings points: W = 2, OTL = 1, L = 0."""
        return self.w * POINTS["W"] + self.otl * POINTS["OTL"] + self.l * POINTS["L"]

    @property
    def diff(self) -> int:
        """Goal difference (goals for minus goals against)."""
        return self.gf - self.ga
