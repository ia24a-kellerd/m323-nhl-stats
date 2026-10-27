"""Flask application factory."""

from pathlib import Path

from flask import Flask

from routes.games_routes import bp as games_bp
from routes.import_routes import bp as import_bp
from routes.league_routes import bp as league_bp
from routes.standings_routes import bp as standings_bp
from routes.teams_routes import bp as teams_bp
from services.loader import load_games_folder

DEFAULT_GAMES_DIR = Path(__file__).resolve().parent / "data" / "games"


def create_app(games_dir: Path | None = DEFAULT_GAMES_DIR) -> Flask:
    """Create and configure the Flask app; all CSV files in games_dir are loaded at startup."""
    app = Flask(__name__)
    games, reports = load_games_folder(games_dir) if games_dir else ((), ())
    app.config["GAMES_DIR"] = games_dir
    app.config["GAMES"] = list(games)
    app.config["FOLDER_IMPORTS"] = reports

    app.register_blueprint(league_bp)
    app.register_blueprint(import_bp)
    app.register_blueprint(games_bp)
    app.register_blueprint(standings_bp)
    app.register_blueprint(teams_bp)

    return app


if __name__ == "__main__":
    create_app().run()
