from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from fpl_db.base import Base


class Fixture(Base):
    __tablename__ = "fixtures"
    id: Mapped[int] = mapped_column(primary_key=True)
    gameweek_id: Mapped[int] = mapped_column(foreign_key="gameweeks.id", nullable=False)
    home_team: Mapped[int] = mapped_column(foreign_key="teams.id", nullable=False)
    away_team: Mapped[int] = mapped_column(foreign_key="teams.id", nullable=False)
    kickoff_time: Mapped[datetime] = mapped_column(nullable=False)
