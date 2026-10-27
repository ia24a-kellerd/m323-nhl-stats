from datetime import date

from models import Game
from services.standings import calculate_standings


def test_calculate_standings_includes_ot_loss_point():
    games = [
        Game(date(2025, 10, 1), "2025-26", "TOR", "MTL", 4, 3, "OT"),
        Game(date(2025, 10, 2), "2025-26", "MTL", "TOR", 2, 1, "REG"),
    ]

    standings = calculate_standings(games)
    by_team = {row["TEAM"]: row for row in standings}

    assert by_team["TOR"]["GP"] == 2
    assert by_team["TOR"]["W"] == 1
    assert by_team["TOR"]["L"] == 1
    assert by_team["TOR"]["OTL"] == 0
    assert by_team["TOR"]["PTS"] == 2

    assert by_team["MTL"]["GP"] == 2
    assert by_team["MTL"]["W"] == 1
    assert by_team["MTL"]["L"] == 0
    assert by_team["MTL"]["OTL"] == 1
    assert by_team["MTL"]["PTS"] == 3
