import os

from fastapi import FastAPI

from app.api.institution import router as institution_router
from app.api.email import router as email_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.response_code import router as response_code_router
from app.api.connection import router as connection_router


app = FastAPI(
    title="OpsFlow API",
    version="1.0.0",
)
# Explicit origins: "*" with allow_credentials=True is rejected by browsers
# anyway, and the UI reaches the API through its own /api proxy.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(institution_router)
app.include_router(email_router)
app.include_router(response_code_router)
app.include_router(connection_router)

@app.get("/")
def root():
    return {"message": "Welcome to OpsFlow 🚀"}