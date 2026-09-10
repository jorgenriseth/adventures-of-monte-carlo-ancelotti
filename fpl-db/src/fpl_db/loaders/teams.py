from collections.abc import Iterable

from sqlalchemy.orm import Session

from fpl_db.models import Team, TeamIDMap


def upsert_teams(session: Session, teams: Iterable[Team]) -> int:
    count = 0
    for team in teams:
        session.merge(team)
        count += 1
    return count


def upsert_team_id_map(session: Session, mappings: Iterable[TeamIDMap]) -> int:
    count = 0
    for mapping in mappings:
        session.merge(mapping)
        count += 1
    return count
