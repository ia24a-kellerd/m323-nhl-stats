"""Standings calculation service."""

from models import Game


def calculate_standings(games: list[Game]) -> list[dict[str, int | str]]:
    """Calculate standings using imperative dictionary mutation."""
    records: dict[str, dict[str, int | str]] = {}

    for game in games:
        for team in (game.home_team, game.away_team):
            if team not in records:
                records[team] = {
                    "TEAM": team,
                    "GP": 0,
                    "W": 0,
                    "L": 0,
                    "OTL": 0,
                    "PTS": 0,
                    "GF": 0,
                    "GA": 0,
                    "DIFF": 0,
                }

        home = records[game.home_team]
        away = records[game.away_team]

        home["GP"] += 1
        away["GP"] += 1

        home["GF"] += game.home_goals
        home["GA"] += game.away_goals
        away["GF"] += game.away_goals
        away["GA"] += game.home_goals

        home_won = game.home_goals > game.away_goals

        if home_won:
            home["W"] += 1
            home["PTS"] += 2
            if game.result_type in {"OT", "SO"}:
                away["OTL"] += 1
                away["PTS"] += 1
            else:
                away["L"] += 1
        else:
            away["W"] += 1
            away["PTS"] += 2
            if game.result_type in {"OT", "SO"}:
                home["OTL"] += 1
                home["PTS"] += 1
            else:
                home["L"] += 1

    for record in records.values():
        record["DIFF"] = record["GF"] - record["GA"]

    return sorted(records.values(), key=lambda row: (row["PTS"], row["DIFF"], row["GF"]), reverse=True)
