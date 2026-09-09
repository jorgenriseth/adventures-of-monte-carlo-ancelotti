from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from fpl_db.base import Base


class TeamIDMap(Base):
    __tablename__ = "team_id_map"
    season: Mapped[str] = mapped_column(String(7), primary_key=True)
    team_code: Mapped[int] = mapped_column(ForeignKey("teams.code"), primary_key=True)
    fpl_team_id: Mapped[int] = mapped_column(nullable=False)
