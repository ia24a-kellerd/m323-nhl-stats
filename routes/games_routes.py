"""Routes for game list."""

from flask import Blueprint, current_app, render_template, request

from services.filters import (
    date_error,
    filter_games,
    filter_options,
    newest_first,
    read_filter_values,
    to_filter_params,
)

bp = Blueprint("games", __name__, url_prefix="/games")


@bp.get("/")
def list_games():
    """Show imported games, filtered by the query parameters (newest first)."""
    all_games = current_app.config["GAMES"]
    values = read_filter_values(request.args)
    games = newest_first(filter_games(all_games, to_filter_params(values)))

    return render_template(
        "games.html",
        games=games,
        total_count=len(all_games),
        filters=values,
        options=filter_options(all_games),
        error_message=date_error(values),
    )
