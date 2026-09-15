import argparse

from fpl_db.config import get_database_url
from fpl_db.loaders import (
    upsert_player_id_map,
    upsert_players,
    upsert_team_id_map,
    upsert_teams,
)
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from myfpl.constants import SEASONS
from myfpl.db_population import (
    load_players_raw,
    load_team_catalogue,
    to_players,
    to_teams,
)


def populate(
    seasons: list[str], engine: Engine | None = None, database_url: str | None = None
) -> dict[str, int]:
    engine = engine or create_engine(database_url or get_database_url())
    counts: dict[str, int] = {}

    with Session(engine) as session:
        try:
            teams, team_maps = to_teams(load_team_catalogue(seasons))
            counts["teams"] = upsert_teams(session, teams)
            session.flush()
            counts["team_id_map"] = upsert_team_id_map(session, team_maps)
            session.flush()

            players, player_maps = to_players(load_players_raw(seasons))
            counts["players"] = upsert_players(session, players)
            session.flush()
            counts["player_id_map"] = upsert_player_id_map(session, player_maps)

            session.commit()
        except Exception:
            session.rollback()
            raise

    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Populate the teams/players tables from vastaav historical data."
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Override the database URL (defaults to fpl_db.config.get_database_url()).",
    )
    args = parser.parse_args()

    seasons: list[str] = list(SEASONS)
    counts = populate(seasons, database_url=args.database_url)
    for name, count in counts.items():
        print(f"{name}: {count}")
