from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from fpl_db.base import Base


class PlayerIDMap(Base):
    __tablename__ = "player_id_map"
    season: Mapped[str] = mapped_column(String(7), primary_key=True)
    player_code: Mapped[int] = mapped_column(
        ForeignKey("players.code"), primary_key=True
    )
    fpl_player_id: Mapped[int] = mapped_column(nullable=False)
