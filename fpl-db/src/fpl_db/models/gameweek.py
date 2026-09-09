from sqlalchemy.orm import Mapped, mapped_column

from fpl_db.base import Base


class Gameweek(Base):
    __tablename__ = "gameweeks"
    id: Mapped[int] = mapped_column(primary_key=True)
    season: Mapped[int] = mapped_column(foreign_key="seasons.id", nullable=False)
