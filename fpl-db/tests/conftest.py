import pytest
from fpl_db import models  # noqa: F401  # registers tables on Base.metadata
from fpl_db.base import Base
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    event.listen(
        engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON")
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    db_session: Session = session_local()
    try:
        yield db_session
    finally:
        db_session.close()
        engine.dispose()
