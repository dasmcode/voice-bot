from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import urllib.parse

database = os.getenv("database")
password = urllib.parse.quote_plus(os.getenv("password"))
username = urllib.parse.quote_plus(os.getenv("username"))
server = os.getenv("server")

DATABASE_URL = f"postgresql+psycopg2://{username}:{password}@{server}:5432/{database}"
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
