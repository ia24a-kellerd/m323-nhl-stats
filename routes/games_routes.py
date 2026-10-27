"""Routes for game list."""

from flask import Blueprint, current_app, render_template

bp = Blueprint("games", __name__, url_prefix="/games")


@bp.get("/")
def list_games():
    """Show all imported games."""
    return render_template("games.html", games=current_app.config["GAMES"])
