"""Routes for CSV import."""

from flask import Blueprint, current_app, render_template, request

from services.importer import RowError, import_games_from_csv

bp = Blueprint("import", __name__, url_prefix="/import")


@bp.route("/", methods=["GET", "POST"])
def import_games():
    """Upload and import game results from CSV."""
    imported_games = current_app.config["GAMES"]
    accepted_count = None
    errors: tuple[RowError, ...] = ()
    error_message = None

    if request.method == "POST":
        uploaded_file = request.files.get("csv_file")
        if not uploaded_file or not uploaded_file.filename:
            error_message = "Please select a CSV file."
        else:
            try:
                content = uploaded_file.read().decode("utf-8-sig")
            except UnicodeDecodeError:
                error_message = "The file must be UTF-8 encoded."
            else:
                accepted_games, errors = import_games_from_csv(content, existing=imported_games)
                imported_games.extend(accepted_games)
                accepted_count = len(accepted_games)

    return render_template(
        "import.html",
        imported_count=len(imported_games),
        accepted_count=accepted_count,
        errors=errors,
        error_message=error_message,
    )
