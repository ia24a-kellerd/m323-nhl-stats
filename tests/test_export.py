import csv
from datetime import date
from io import StringIO

from app import create_app
from models import Game
from services.export import standings_to_csv
from services.importer import import_games_from_csv
from services.standings import calculate_standings

GAMES = [
    Game(date(2025, 10, 1), "2025-26", "TOR", "MTL", 4, 3, "OT"),
    Game(date(2025, 10, 2), "2025-26", "MTL", "BOS", 1, 2, "REG"),
]
HEADER = "TEAM,GP,W,L,OTL,PTS,GF,GA,DIFF\n"


def test_standings_to_csv_writes_header_and_rows_in_rank_order():
    assert standings_to_csv(calculate_standings(GAMES)) == (
        # TOR before BOS: same PTS, W and DIFF, but more goals for
        HEADER + "TOR,1,1,0,0,2,4,3,1\n" + "BOS,1,1,0,0,2,2,1,1\n" + "MTL,2,0,1,1,1,4,6,-2\n"
    )


def test_standings_to_csv_without_records_has_only_header():
    assert standings_to_csv(()) == HEADER


def test_standings_to_csv_ignores_extra_keys_and_uses_column_order():
    record = {"DIFF": 1, "GA": 1, "GF": 2, "PTS": 2, "OTL": 0, "L": 0, "W": 1, "GP": 1, "TEAM": "BOS", "EXTRA": 9}

    assert standings_to_csv([record]) == HEADER + "BOS,1,1,0,0,2,2,1,1\n"


def test_exported_csv_can_be_read_back():
    rows = list(csv.DictReader(StringIO(standings_to_csv(calculate_standings(GAMES)))))

    assert [row["TEAM"] for row in rows] == ["TOR", "BOS", "MTL"]
    assert rows[2]["DIFF"] == "-2"


def test_export_route_returns_csv_download():
    app = create_app()
    app.config["GAMES"] = list(GAMES)

    response = app.test_client().get("/standings/export.csv")

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert response.headers["Content-Disposition"] == "attachment; filename=standings.csv"
    assert response.get_data(as_text=True) == standings_to_csv(calculate_standings(GAMES))


def test_export_route_without_games_returns_header_only():
    response = create_app().test_client().get("/standings/export.csv")

    assert response.get_data(as_text=True) == HEADER


def test_standings_page_links_to_export():
    app = create_app()
    app.config["GAMES"] = list(GAMES)

    html = app.test_client().get("/standings/").get_data(as_text=True)

    assert 'href="/standings/export.csv"' in html


def test_import_does_not_accept_exported_standings():
    # the export has other columns than the game import, so it must be rejected cleanly
    _, errors = import_games_from_csv(standings_to_csv(calculate_standings(GAMES)))

    assert errors[0].line == 1
    assert errors[0].reason.startswith("missing columns:")
