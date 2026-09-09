from sqlalchemy.orm import Mapped, mapped_column

from fpl_db.base import Base


class Season(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    season: Mapped[str] = mapped_column(nullable=False)
