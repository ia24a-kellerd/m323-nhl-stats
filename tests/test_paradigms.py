from datetime import date
from pathlib import Path

import pytest

from models import Game
from services.importer import import_games_from_csv
from services.paradigms import TeamSeason, points_functional, points_object_oriented, points_procedural
from services.standings import teams_in

SAMPLE_CSV = Path(__file__).resolve().parents[1] / "data" / "sample_games.csv"
SAMPLE_GAMES, _ = import_games_from_csv(SAMPLE_CSV.read_text(encoding="utf-8"))

PARADIGMS = (points_object_oriented, points_procedural, points_functional)


@pytest.mark.parametrize("team", teams_in(SAMPLE_GAMES))
def test_all_paradigms_return_same_points_for_every_sample_team(team):
    results = {paradigm.__name__: paradigm(SAMPLE_GAMES, team) for paradigm in PARADIGMS}

    assert len(set(results.values())) == 1, results


def test_sample_csv_has_eight_teams():
    assert len(teams_in(SAMPLE_GAMES)) == 8


@pytest.mark.parametrize("paradigm", PARADIGMS)
def test_win_ot_loss_and_regulation_loss(paradigm):
    games = (
        Game(date(2025, 10, 1), "2025-26", "TOR", "MTL", 4, 2, "REG"),  # TOR W  -> 2
        Game(date(2025, 10, 2), "2025-26", "BOS", "TOR", 3, 2, "SO"),  # TOR OTL -> 1
        Game(date(2025, 10, 3), "2025-26", "TOR", "NYR", 1, 3, "REG"),  # TOR L  -> 0
        Game(date(2025, 10, 4), "2025-26", "MTL", "BOS", 5, 1, "REG"),  # not TOR
    )

    assert paradigm(games, "TOR") == 3


@pytest.mark.parametrize("paradigm", PARADIGMS)
def test_team_without_games_has_zero_points(paradigm):
    assert paradigm(SAMPLE_GAMES, "EDM") == 0


def test_team_season_object_changes_its_state():
    season = TeamSeason("TOR")

    season.add_game(Game(date(2025, 10, 1), "2025-26", "TOR", "MTL", 4, 2, "REG"))
    season.add_game(Game(date(2025, 10, 2), "2025-26", "BOS", "MTL", 4, 2, "REG"))

    assert (season.wins, season.losses, season.ot_losses) == (1, 0, 0)
    assert season.points() == 2
