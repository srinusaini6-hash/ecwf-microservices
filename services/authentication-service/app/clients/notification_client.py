from httpx import AsyncClient
from app.core.config import settings


class NotificationClient:
    def __init__(self,http:AsyncClient): self.http=http
    async def send_otp(self,email:str,otp:str,purpose:str):
        response=await self.http.post(f"{settings.notification_service_url}/api/v1/notifications/internal/email",headers={"X-Internal-API-Key":settings.internal_api_key},json={"to":email,"subject":f"ECWF {purpose.replace('_',' ').title()} OTP","body":f"Your ECWF OTP is {otp}. It expires in {settings.otp_expire_minutes} minutes.","template":purpose})
        response.raise_for_status()
