from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from fpl_db.base import Base


class Gameweek(Base):
    __tablename__ = "gameweeks"
    __table_args__ = (UniqueConstraint("season", "gameweek"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    season: Mapped[str] = mapped_column(String(7))
    gameweek: Mapped[int] = mapped_column(Integer)
