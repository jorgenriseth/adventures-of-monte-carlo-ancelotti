from sqlalchemy.orm import Mapped, mapped_column

from fpl_db.base import Base


class PlayerPerformance(Base):
    __tablename__ = "player_performances"
    id: Mapped[int] = mapped_column(primary_key=True)
    player_code: Mapped[int] = mapped_column(foreign_key="players.code", nullable=False)
    fixture_id: Mapped[int] = mapped_column(foreign_key="fixtures.id", nullable=False)
    points_scored: Mapped[int] = mapped_column(nullable=False)
    player_started: Mapped[bool] = mapped_column(nullable=False)
    minutes_played: Mapped[int] = mapped_column(nullable=False)
