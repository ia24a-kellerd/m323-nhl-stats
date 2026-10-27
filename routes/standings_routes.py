"""Routes for standings."""

from flask import Blueprint, current_app, render_template

from services.standings import calculate_standings

bp = Blueprint("standings", __name__, url_prefix="/standings")


@bp.get("/")
def standings():
    """Show standings for imported games."""
    standings_rows = calculate_standings(current_app.config["GAMES"])
    return render_template("standings.html", standings=standings_rows)
