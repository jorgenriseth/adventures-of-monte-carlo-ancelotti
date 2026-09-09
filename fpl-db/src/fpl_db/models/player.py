from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from fpl_db.base import Base
from fpl_db.enums import Position
from fpl_db.types import PositionType


class Player(Base):
    __tablename__ = "players"
    code: Mapped[int] = mapped_column(Integer, primary_key=True)
    web_name: Mapped[str] = mapped_column(String(64), nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    position: Mapped[Position] = mapped_column(PositionType, nullable=False)
