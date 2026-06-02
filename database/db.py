from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL


class Base(DeclarativeBase):
    pass


_connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False)
Session = sessionmaker(bind=engine)


def init_db():
    """Create all tables if they don't exist yet."""
    from database.models import Email, Tonnage, CargoVC, CargoTC  # noqa: F401
    Base.metadata.create_all(engine)


def get_session():
    return Session()
