from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from fpl_db.base import Base


class PlayerMatchPerformance(Base):
    __tablename__ = "player_performances"
    __table_args__ = (UniqueConstraint("player_code", "fixture_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    player_code: Mapped[int] = mapped_column(ForeignKey("players.code"), nullable=False)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"), nullable=False)
    points_scored: Mapped[int] = mapped_column(nullable=False)
    player_started: Mapped[bool] = mapped_column(nullable=False)
    minutes_played: Mapped[int] = mapped_column(nullable=False)
