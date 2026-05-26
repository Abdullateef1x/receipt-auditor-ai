import os
from sqlmodel import SQLModel, create_engine, Session



def get_engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set.")
    return create_engine(url, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(get_engine())  # type: ignore[attr-defined]


def get_session():
    with Session(get_engine()) as session:
        yield session