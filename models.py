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

    @property
    def pct(self) -> float:
        """Points percentage: points / maximum possible points (0.0 without games)."""
        return self.pts / (self.gp * POINTS["W"]) if self.gp else 0.0


@dataclass(frozen=True)
class GameLogEntry:
    """One game from the point of view of a team."""

    date: date
    opponent: str
    at_home: bool
    goals_for: int
    goals_against: int
    result: str
    result_type: str


@dataclass(frozen=True)
class TeamStats:
    """Statistics of one team for the team page."""

    team: str
    games_played: int
    record: TeamRecord
    home_record: TeamRecord
    away_record: TeamRecord
    avg_goals_for: float
    avg_goals_against: float
    highest_scoring_game: Game | None
    longest_win_streak: int
    current_streak: str
    form: tuple[str, ...]
    overtime_record: TeamRecord
    one_goal_record: TeamRecord
    shutouts: int
    shutout_losses: int
    biggest_win: Game | None
    biggest_loss: Game | None
    head_to_head: tuple[tuple[str, TeamRecord], ...]
    game_log: tuple[GameLogEntry, ...]


@dataclass(frozen=True)
class LeagueStats:
    """Statistics over all games for the overview page."""

    games: int
    teams: int
    seasons: tuple[str, ...]
    first_date: date | None
    last_date: date | None
    goals_per_game: float
    home_win_pct: float
    ot_pct: float
    so_pct: float
    shutouts: int
    highest_scoring_game: Game | None
    biggest_win: Game | None
    top_points: tuple[tuple[str, int], ...]
    top_offense: tuple[tuple[str, float], ...]
    top_defense: tuple[tuple[str, float], ...]
    top_streaks: tuple[tuple[str, int], ...]
