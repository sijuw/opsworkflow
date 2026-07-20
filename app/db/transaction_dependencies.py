from app.db.transaction_database import TransactionSessionLocal


def get_transaction_db():
    db = TransactionSessionLocal()
    try:
        yield db
    finally:
        db.close()