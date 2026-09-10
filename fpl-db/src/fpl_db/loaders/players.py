from collections.abc import Iterable

from sqlalchemy.orm import Session

from fpl_db.models import Player, PlayerIDMap


def upsert_players(session: Session, players: Iterable[Player]) -> int:
    count = 0
    for player in players:
        session.merge(player)
        count += 1
    return count


def upsert_player_id_map(session: Session, mappings: Iterable[PlayerIDMap]) -> int:
    count = 0
    for mapping in mappings:
        session.merge(mapping)
        count += 1
    return count
