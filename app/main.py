from fastapi import FastAPI

app = FastAPI(
    title="OpsFlow API",
    version="1.0.0",
    description="Internal Operations & Stakeholder Communication Platform"
)

@app.get("/")
def root():
    return {
        "message": "Welcome to OpsFlow 🚀"
    }