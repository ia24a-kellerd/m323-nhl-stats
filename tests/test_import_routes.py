from io import BytesIO

from app import create_app

CSV_TEXT = (
    "date,season,home_team,away_team,home_goals,away_goals,result_type\n"
    "2025-10-01,2025-26,TOR,MTL,3,2,REG\n"
)


def post_csv(app, content: bytes):
    client = app.test_client()
    return client.post(
        "/import/",
        data={"csv_file": (BytesIO(content), "games.csv")},
        content_type="multipart/form-data",
    )


def test_import_accepts_utf8_file_with_bom():
    app = create_app()

    response = post_csv(app, CSV_TEXT.encode("utf-8-sig"))

    assert response.status_code == 200
    assert len(app.config["GAMES"]) == 1


def test_import_shows_error_for_non_utf8_file():
    app = create_app()

    response = post_csv(app, b"\xff\xfe invalid")

    assert response.status_code == 200
    assert "The file must be UTF-8 encoded." in response.get_data(as_text=True)
    assert app.config["GAMES"] == []
