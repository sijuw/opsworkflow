import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.db.url import build_mysql_url

load_dotenv()

DATABASE_URL = build_mysql_url("DB")


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    # Was unconditionally True, which logs every statement in production.
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)
