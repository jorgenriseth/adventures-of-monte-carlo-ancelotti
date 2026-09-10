import pytest
from sqlalchemy.exc import IntegrityError

from fpl_db.enums import Position
from fpl_db.loaders import (
    upsert_player_id_map,
    upsert_players,
    upsert_team_id_map,
    upsert_teams,
)
from fpl_db.models import Player, PlayerIDMap, Team, TeamIDMap


def test_upsert_teams_inserts_and_updates(session):
    upsert_teams(session, [Team(code=3, name="Arsenal")])
    session.commit()

    upsert_teams(session, [Team(code=3, name="Arsenal FC")])
    session.commit()

    teams = session.query(Team).all()
    assert len(teams) == 1
    assert teams[0].code == 3
    assert teams[0].name == "Arsenal FC"


def test_upsert_players_inserts_and_updates(session):
    upsert_players(
        session,
        [
            Player(
                code=1,
                web_name="Salah",
                full_name="Mohamed Salah",
                position=Position.MID,
            )
        ],
    )
    session.commit()

    upsert_players(
        session,
        [
            Player(
                code=1,
                web_name="M.Salah",
                full_name="Mohamed Salah",
                position=Position.FWD,
            )
        ],
    )
    session.commit()

    players = session.query(Player).all()
    assert len(players) == 1
    assert players[0].web_name == "M.Salah"
    assert players[0].position == Position.FWD


def test_team_id_map_requires_existing_team(session):
    upsert_team_id_map(
        session, [TeamIDMap(season="2025-26", team_code=999, fpl_team_id=1)]
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_team_id_map_upsert_against_existing_team(session):
    upsert_teams(session, [Team(code=3, name="Arsenal")])
    session.flush()

    upsert_team_id_map(
        session, [TeamIDMap(season="2025-26", team_code=3, fpl_team_id=1)]
    )
    session.commit()

    mappings = session.query(TeamIDMap).all()
    assert len(mappings) == 1
    assert mappings[0].fpl_team_id == 1


def test_player_id_map_requires_existing_player(session):
    upsert_player_id_map(
        session, [PlayerIDMap(season="2025-26", player_code=999, fpl_player_id=1)]
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_player_id_map_upsert_against_existing_player(session):
    upsert_players(
        session,
        [
            Player(
                code=1,
                web_name="Salah",
                full_name="Mohamed Salah",
                position=Position.MID,
            )
        ],
    )
    session.flush()

    upsert_player_id_map(
        session, [PlayerIDMap(season="2025-26", player_code=1, fpl_player_id=201)]
    )
    session.commit()

    mappings = session.query(PlayerIDMap).all()
    assert len(mappings) == 1
    assert mappings[0].fpl_player_id == 201
