from fastapi import FastAPI

from app.routers.auth import router as auth_router

app = FastAPI(
    title="Authentication & Registration Service",
    version="1.0.0",
)

app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "Authentication Service is running"
    }