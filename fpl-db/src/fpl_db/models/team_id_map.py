from sqlalchemy.orm import Mapped, mapped_column

from fpl_db.base import Base


class TeamIDMap(Base):
    __tablename__ = "team_id_map"
    code: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    season: Mapped[int] = mapped_column(foreign_key="seasons.id", nullable=False)
    fpl_team_id: Mapped[int] = mapped_column(nullable=False)
