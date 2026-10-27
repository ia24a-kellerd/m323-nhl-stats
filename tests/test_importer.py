from services.importer import import_games_from_csv, validate_row


def test_validate_row_valid_data():
    row = {
        "date": "2025-10-01",
        "season": "2025-26",
        "home_team": "TOR",
        "away_team": "MTL",
        "home_goals": "4",
        "away_goals": "2",
        "result_type": "REG",
    }

    game, error = validate_row(row)

    assert error is None
    assert game is not None
    assert game.home_team == "TOR"


def test_validate_row_rejects_tied_score():
    row = {
        "date": "2025-10-01",
        "season": "2025-26",
        "home_team": "TOR",
        "away_team": "MTL",
        "home_goals": "3",
        "away_goals": "3",
        "result_type": "REG",
    }

    game, error = validate_row(row)

    assert game is None
    assert error == "tied score is not allowed"


def test_validate_row_rejects_invalid_result_type():
    row = {
        "date": "2025-10-01",
        "season": "2025-26",
        "home_team": "TOR",
        "away_team": "MTL",
        "home_goals": "3",
        "away_goals": "2",
        "result_type": "XYZ",
    }

    game, error = validate_row(row)

    assert game is None
    assert error == "invalid result_type"


def test_validate_row_rejects_missing_fields():
    row = {
        "date": "2025-10-01",
        "season": "2025-26",
        "home_team": "",
        "away_team": "MTL",
        "home_goals": "3",
        "away_goals": "2",
        "result_type": "REG",
    }

    game, error = validate_row(row)

    assert game is None
    assert error == "missing fields: home_team"


def test_import_games_from_csv_rejects_row_with_too_few_columns():
    csv_text = (
        "date,season,home_team,away_team,home_goals,away_goals,result_type\n"
        "2025-10-01,2025-26,TOR\n"
    )

    accepted, rejected = import_games_from_csv(csv_text)

    assert accepted == []
    assert rejected[0]["error"] == "missing fields: away_team, home_goals, away_goals, result_type"
