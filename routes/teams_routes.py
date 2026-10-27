"""Routes for team statistics."""

from flask import Blueprint, current_app, render_template

from services.team_stats import format_record, team_stats

bp = Blueprint("teams", __name__, url_prefix="/teams")


@bp.get("/<abbr>")
def team_page(abbr: str):
    """Show statistics for one team."""
    stats = team_stats(current_app.config["GAMES"], abbr.strip().upper())
    return render_template("team.html", stats=stats, format_record=format_record)
