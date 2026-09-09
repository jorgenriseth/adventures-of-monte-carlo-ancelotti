from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from fpl_db.base import Base


class Team(Base):
    __tablename__ = "teams"
    code: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
