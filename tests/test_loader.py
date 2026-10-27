from datetime import date

from app import DEFAULT_GAMES_DIR, create_app
from models import Game
from services.importer import RowError
from services.loader import FileImport, csv_files, import_files, load_games_folder

HEADER = "date,season,home_team,away_team,home_goals,away_goals,result_type\n"
TOR_MTL = "2025-10-01,2025-26,TOR,MTL,4,2,REG\n"
BOS_TOR = "2025-10-02,2025-26,BOS,TOR,1,2,OT\n"


def test_csv_files_sorted_and_only_csv(tmp_path):
    (tmp_path / "b.csv").write_text(HEADER)
    (tmp_path / "a.csv").write_text(HEADER)
    (tmp_path / "notes.txt").write_text("ignore me")

    assert [path.name for path in csv_files(tmp_path)] == ["a.csv", "b.csv"]


def test_csv_files_of_missing_folder_is_empty(tmp_path):
    assert csv_files(tmp_path / "missing") == ()


def test_import_files_treats_games_of_earlier_files_as_duplicates():
    games, reports = import_files([("a.csv", HEADER + TOR_MTL), ("b.csv", HEADER + TOR_MTL + BOS_TOR)])

    assert [(g.home_team, g.away_team) for g in games] == [("TOR", "MTL"), ("BOS", "TOR")]
    assert reports == (
        FileImport("a.csv", 1, ()),
        FileImport("b.csv", 1, (RowError(2, "game was already imported"),)),
    )


def test_import_files_reports_non_utf8_file():
    games, reports = import_files([("bad.csv", None)])

    assert games == ()
    assert reports == (FileImport("bad.csv", 0, (RowError(1, "file must be UTF-8 encoded"),)),)


def test_load_games_folder_reads_all_files(tmp_path):
    (tmp_path / "1.csv").write_text(HEADER + TOR_MTL, encoding="utf-8")
    (tmp_path / "2.csv").write_bytes(("﻿" + HEADER + BOS_TOR).encode("utf-8"))  # Excel BOM
    (tmp_path / "3.csv").write_bytes(b"\xff\xfe broken")

    games, reports = load_games_folder(tmp_path)

    assert games[0] == Game(date(2025, 10, 1), "2025-26", "TOR", "MTL", 4, 2, "REG")
    assert len(games) == 2
    assert [(r.name, r.accepted, len(r.errors)) for r in reports] == [("1.csv", 1, 0), ("2.csv", 1, 0), ("3.csv", 0, 1)]


def test_app_loads_real_games_from_data_folder():
    app = create_app()

    assert app.config["GAMES_DIR"] == DEFAULT_GAMES_DIR
    assert len(app.config["GAMES"]) == 1312
    assert all(not report.errors for report in app.config["FOLDER_IMPORTS"])


def test_app_without_folder_starts_empty():
    assert create_app(games_dir=None).config["GAMES"] == []


def test_reload_folder_replaces_games(tmp_path):
    (tmp_path / "a.csv").write_text(HEADER + TOR_MTL, encoding="utf-8")
    app = create_app(games_dir=tmp_path)
    assert len(app.config["GAMES"]) == 1

    (tmp_path / "b.csv").write_text(HEADER + BOS_TOR, encoding="utf-8")
    response = app.test_client().post("/import/reload")

    assert response.status_code == 302
    assert len(app.config["GAMES"]) == 2
    assert [r.name for r in app.config["FOLDER_IMPORTS"]] == ["a.csv", "b.csv"]


def test_all_pages_render_with_real_data():
    client = create_app().test_client()

    for url in ("/", "/standings/", "/games/", "/games/?team=TOR&result_type=OT", "/teams/TOR", "/teams/XYZ", "/import/"):
        assert client.get(url).status_code == 200, url
