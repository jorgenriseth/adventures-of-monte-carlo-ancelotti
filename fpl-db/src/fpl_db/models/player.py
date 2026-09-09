from sqlalchemy.orm import Mapped, mapped_column

from fpl_db.base import Base
from fpl_db.enums import Position
from fpl_db.types import PositionType


class Player(Base):
    __tablename__ = "players"
    code: Mapped[int] = mapped_column(primary_key=True)
    web_name: Mapped[str] = mapped_column(nullable=False)
    full_name: Mapped[str] = mapped_column(nullable=False)
    position: Mapped[Position] = mapped_column(PositionType, nullable=False)
