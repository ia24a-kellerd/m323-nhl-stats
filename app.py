"""Flask application factory."""

from flask import Flask, redirect, url_for

from routes.games_routes import bp as games_bp
from routes.import_routes import bp as import_bp
from routes.standings_routes import bp as standings_bp


def create_app() -> Flask:
    """Create and configure the Flask app."""
    app = Flask(__name__)
    app.config["GAMES"] = []

    app.register_blueprint(import_bp)
    app.register_blueprint(games_bp)
    app.register_blueprint(standings_bp)

    @app.get("/")
    def index():
        return redirect(url_for("games.list_games"))

    return app


if __name__ == "__main__":
    create_app().run()
