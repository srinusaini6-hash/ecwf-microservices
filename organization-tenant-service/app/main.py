from fastapi import FastAPI

from app.database.database import Base, engine
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.routers.organization import router as organization_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Organization and Tenant Service",
    description="Organization and Tenant Management Microservice",
    version="1.0.0",
)

# Register router
app.include_router(organization_router)


@app.get("/")
def root():
    return {
        "message": "Organization and Tenant Service is ready"
    }