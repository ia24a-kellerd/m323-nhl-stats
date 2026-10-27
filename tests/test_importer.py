from datetime import date

from models import Game
from services.importer import (
    RowError,
    RowResult,
    import_games_from_csv,
    import_row,
    parse_row,
    read_rows,
    to_game,
    validate,
)

HEADER = "date,season,home_team,away_team,home_goals,away_goals,result_type\n"
RAW = {
    "date": "2025-10-01",
    "season": "2025-26",
    "home_team": "tor",
    "away_team": "MTL",
    "home_goals": "4",
    "away_goals": "2",
    "result_type": "reg",
}
TOR_MTL = Game(date(2025, 10, 1), "2025-26", "TOR", "MTL", 4, 2, "REG")


def raw_row(**changes) -> RowResult:
    return RowResult(2, {**RAW, **changes})


def errors_of(csv_text: str) -> tuple[RowError, ...]:
    return import_games_from_csv(csv_text)[1]


# --- single pipeline steps ---


def test_read_rows_keeps_real_line_numbers_with_blank_lines():
    header, rows = read_rows(HEADER + "2025-10-01,2025-26,TOR,MTL,4,2,REG\n\n2025-10-02,2025-26,BOS,TOR,1,2,REG\n")

    assert header[0] == "date"
    assert [row.line for row in rows] == [2, 4]


def test_parse_row_converts_types_and_normalizes():
    value = parse_row(raw_row()).value

    assert value["date"] == date(2025, 10, 1)
    assert value["home_goals"] == 4
    assert value["home_team"] == "TOR"
    assert value["result_type"] == "REG"


def test_validate_passes_valid_row_unchanged():
    parsed = parse_row(raw_row())

    assert validate(parsed) == parsed


def test_to_game_creates_game():
    assert to_game(validate(parse_row(raw_row()))).value == TOR_MTL


def test_failed_row_skips_later_steps():
    failed = RowResult(5, None, "some error")

    assert parse_row(failed) is failed
    assert validate(failed) is failed
    assert to_game(failed) is failed


def test_import_row_is_composition_of_all_steps():
    assert import_row(raw_row()) == RowResult(2, TOR_MTL)


# --- whole file and edge cases ---


def test_valid_file():
    games, errors = import_games_from_csv(HEADER + "2025-10-01,2025-26,TOR,MTL,4,2,REG\n")

    assert games == (TOR_MTL,)
    assert errors == ()


def test_empty_file():
    assert import_games_from_csv("") == ((), (RowError(1, "file is empty"),))


def test_header_only():
    assert import_games_from_csv(HEADER) == ((), (RowError(1, "file contains no games"),))


def test_missing_column_in_header():
    csv_text = "date,season,home_team,away_team,home_goals,away_goals\n2025-10-01,2025-26,TOR,MTL,4,2\n"

    assert errors_of(csv_text) == (RowError(1, "missing columns: result_type"),)


def test_missing_value_in_row():
    assert errors_of(HEADER + "2025-10-01,2025-26,,MTL,4,2,REG\n") == (RowError(2, "missing fields: home_team"),)


def test_row_with_too_few_columns():
    assert errors_of(HEADER + "2025-10-01,2025-26,TOR\n") == (
        RowError(2, "missing fields: away_team, home_goals, away_goals, result_type"),
    )


def test_invalid_date():
    assert errors_of(HEADER + "2025-13-01,2025-26,TOR,MTL,4,2,REG\n") == (
        RowError(2, "invalid date '2025-13-01' (expected YYYY-MM-DD)"),
    )


def test_non_numeric_goals():
    assert errors_of(HEADER + "2025-10-01,2025-26,TOR,MTL,four,2,REG\n") == (
        RowError(2, "goals must be whole numbers"),
    )


def test_decimal_goals_are_rejected():
    assert errors_of(HEADER + "2025-10-01,2025-26,TOR,MTL,4.0,2,REG\n") == (
        RowError(2, "goals must be whole numbers"),
    )


def test_negative_goals():
    assert errors_of(HEADER + "2025-10-01,2025-26,TOR,MTL,-1,2,REG\n") == (
        RowError(2, "goals must not be negative"),
    )


def test_tied_score():
    assert errors_of(HEADER + "2025-10-01,2025-26,TOR,MTL,3,3,REG\n") == (RowError(2, "tied score is not allowed"),)


def test_invalid_result_type():
    assert errors_of(HEADER + "2025-10-01,2025-26,TOR,MTL,3,2,XYZ\n") == (RowError(2, "invalid result_type"),)


def test_same_home_and_away_team():
    assert errors_of(HEADER + "2025-10-01,2025-26,TOR,tor,3,2,REG\n") == (
        RowError(2, "home and away team are the same"),
    )


def test_ot_game_with_goal_difference_larger_than_one():
    assert errors_of(HEADER + "2025-10-01,2025-26,TOR,MTL,5,2,OT\n") == (
        RowError(2, "OT/SO game must be won by exactly one goal"),
    )


def test_so_game_with_one_goal_difference_is_valid():
    games, errors = import_games_from_csv(HEADER + "2025-10-01,2025-26,TOR,MTL,2,3,SO\n")

    assert len(games) == 1
    assert errors == ()


def test_duplicate_game_in_file_keeps_first_line():
    csv_text = HEADER + "2025-10-01,2025-26,TOR,MTL,4,2,REG\n" + "2025-10-01,2025-26,TOR,MTL,1,0,REG\n"

    games, errors = import_games_from_csv(csv_text)

    assert games == (TOR_MTL,)
    assert errors == (RowError(3, "duplicate of line 2"),)


def test_game_already_imported_is_rejected():
    games, errors = import_games_from_csv(HEADER + "2025-10-01,2025-26,TOR,MTL,4,2,REG\n", existing=[TOR_MTL])

    assert games == ()
    assert errors == (RowError(2, "game was already imported"),)


def test_valid_and_invalid_rows_are_reported_per_line():
    csv_text = (
        HEADER
        + "2025-10-01,2025-26,TOR,MTL,4,2,REG\n"
        + "2025-10-02,2025-26,BOS,TOR,3,3,REG\n"
        + "2025-10-03,2025-26,MTL,BOS,2,1,XX\n"
    )

    games, errors = import_games_from_csv(csv_text)

    assert games == (TOR_MTL,)
    assert errors == (RowError(3, "tied score is not allowed"), RowError(4, "invalid result_type"))
