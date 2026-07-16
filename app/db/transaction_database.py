import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = (
    f"mysql+pymysql://"
    f"{os.getenv('TX_DB_USER')}:"
    f"{os.getenv('TX_DB_PASSWORD')}@"
    f"{os.getenv('TX_DB_HOST')}:"
    f"{os.getenv('TX_DB_PORT')}/"
    f"{os.getenv('TX_DB_NAME')}"
)

transaction_engine = create_engine(DATABASE_URL)

TransactionSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=transaction_engine,
)
