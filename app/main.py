from fastapi import FastAPI

from app.db.database import Base, engine

# Import models so SQLAlchemy registers them
from app.models import Institution
from app.api.institution import router as institution_router
from app.api.email import router as email_router
# from fastapi.middleware.cors import CORSMiddleware
from app.api.response_code import router as response_code_router


app = FastAPI(
    title="OpsFlow API",
    version="1.0.0",
)
app.include_router(institution_router)
app.include_router(email_router)
app.include_router(response_code_router)
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Welcome to OpsFlow 🚀"}