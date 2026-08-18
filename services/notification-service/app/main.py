from fastapi import FastAPI
from app.routers.api import router
app=FastAPI(title="ECWF Notification Service",version="2.0.0")
app.include_router(router)
@app.get("/health",tags=["System"])
def health():return {"status":"healthy","service":"notification-service","shared_database":"ecwf_db"}
