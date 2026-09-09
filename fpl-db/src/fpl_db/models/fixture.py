from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from fpl_db.base import Base


class Fixture(Base):
    __tablename__ = "fixtures"
    id: Mapped[int] = mapped_column(primary_key=True)
    gameweek_id: Mapped[int] = mapped_column(ForeignKey("gameweeks.id"), nullable=False)
    home_team_code: Mapped[int] = mapped_column(ForeignKey("teams.code"), nullable=False)
    away_team_code: Mapped[int] = mapped_column(ForeignKey("teams.code"), nullable=False)
    kickoff_time: Mapped[datetime] = mapped_column(nullable=False)
    finished: Mapped[bool] = mapped_column(nullable=False)
    home_team_score: Mapped[int | None] = mapped_column(nullable=True)
    away_team_score: Mapped[int | None] = mapped_column(nullable=True)
