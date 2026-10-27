"""Routes for standings."""

from flask import Blueprint, Response, current_app, render_template

from services.export import standings_to_csv
from services.standings import calculate_standings

bp = Blueprint("standings", __name__, url_prefix="/standings")


@bp.get("/")
def standings():
    """Show standings for imported games."""
    standings_rows = calculate_standings(current_app.config["GAMES"])
    return render_template("standings.html", standings=standings_rows)


@bp.get("/export.csv")
def export_csv():
    """Download the current standings as a CSV file."""
    csv_text = standings_to_csv(calculate_standings(current_app.config["GAMES"]))
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=standings.csv"},
    )
