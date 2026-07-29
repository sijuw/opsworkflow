from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.url import build_mysql_url

load_dotenv()

DATABASE_URL = build_mysql_url("TX_DB")

transaction_engine = create_engine(DATABASE_URL)

TransactionSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=transaction_engine,
)
