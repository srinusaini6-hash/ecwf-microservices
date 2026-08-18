from fastapi import APIRouter,Depends,Header,HTTPException
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import get_db
from app.schemas import EmailCreate
from app.services import NotificationService
router=APIRouter(prefix="/api/v1/notifications",tags=["Notifications"])

@router.post("/internal/email")
def send_email(data:EmailCreate,x_internal_api_key:str=Header(...),db:Session=Depends(get_db)):
    if x_internal_api_key!=settings.internal_api_key:raise HTTPException(401,"Invalid internal API key")
    return NotificationService(db).send(data)
