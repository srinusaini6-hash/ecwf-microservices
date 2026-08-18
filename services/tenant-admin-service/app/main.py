from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.core.config import settings
from app.routers.api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    timeout = httpx.Timeout(settings.http_timeout_seconds, connect=settings.http_connect_timeout_seconds)
    app.state.http = httpx.AsyncClient(timeout=timeout)
    try:
        yield
    finally:
        await app.state.http.aclose()


app = FastAPI(title=settings.app_name, version="3.0.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health", tags=["System"])
def health():
    return {"status": "healthy", "service": "tenant-admin-service", "shared_database": "ecwf_db"}
