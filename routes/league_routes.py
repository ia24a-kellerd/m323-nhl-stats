"""Route for the league overview (start page)."""

from flask import Blueprint, current_app, render_template

from services.league_stats import league_stats

bp = Blueprint("league", __name__)


@bp.get("/")
def overview():
    """Show statistics over all games."""
    return render_template("league.html", stats=league_stats(current_app.config["GAMES"]))
