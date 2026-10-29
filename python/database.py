import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = (
    "postgresql+psycopg://"
    f"{os.environ['PGUSER']}:"
    f"{os.environ['PGPASSWORD']}@"
    f"{os.getenv('PGHOST', 'localhost')}:"
    f"{os.getenv('PGPORT', '5432')}/"
    f"{os.environ['PGDATABASE']}"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

