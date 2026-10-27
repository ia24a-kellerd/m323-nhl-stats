"""Routes for game list."""

from flask import Blueprint, current_app, render_template, request

from services.filters import date_error, filter_games, read_filter_values, to_filter_params

bp = Blueprint("games", __name__, url_prefix="/games")


@bp.get("/")
def list_games():
    """Show imported games, filtered by the query parameters."""
    values = read_filter_values(request.args)
    games = filter_games(current_app.config["GAMES"], to_filter_params(values))

    return render_template(
        "games.html",
        games=games,
        filters=values,
        error_message=date_error(values),
    )
