"""Routes for game list."""

from datetime import date

from flask import Blueprint, current_app, render_template, request

bp = Blueprint("games", __name__, url_prefix="/games")


@bp.get("/")
def list_games():
    """Show imported games, filtered by the query parameters."""
    team = request.args.get("team", "").strip().upper()
    season = request.args.get("season", "").strip()
    result_type = request.args.get("result_type", "").strip().upper()
    date_from_text = request.args.get("date_from", "").strip()
    date_to_text = request.args.get("date_to", "").strip()

    error_message = None
    date_from = None
    date_to = None
    try:
        if date_from_text:
            date_from = date.fromisoformat(date_from_text)
        if date_to_text:
            date_to = date.fromisoformat(date_to_text)
    except ValueError:
        error_message = "Dates must have the format YYYY-MM-DD."

    filtered_games = []
    for game in current_app.config["GAMES"]:
        if not team or game.home_team == team or game.away_team == team:
            if not season or game.season == season:
                if not result_type or game.result_type == result_type:
                    if not date_from or game.date >= date_from:
                        if not date_to or game.date <= date_to:
                            filtered_games.append(game)

    return render_template(
        "games.html",
        games=filtered_games,
        filters={
            "team": team,
            "season": season,
            "result_type": result_type,
            "date_from": date_from_text,
            "date_to": date_to_text,
        },
        error_message=error_message,
    )
