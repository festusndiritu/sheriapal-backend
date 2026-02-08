from sqlmodel import create_engine, SQLModel, Session
from typing import Generator
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./sheriapal.db")
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else None)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

