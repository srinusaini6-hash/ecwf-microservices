from fastapi import FastAPI

from app.database.database import Base, engine
from app.models.notification import Notification
from app.routers.notification import router as notification_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Notification Service",
    description="Notification Management Microservice",
    version="1.0.0",
)

app.include_router(notification_router)


@app.get("/")
def root():
    return {
        "message": "Notification Service is ready"
    }