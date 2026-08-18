import os
import httpx

NOTIFICATION_SERVICE_URL = os.getenv(
    "NOTIFICATION_SERVICE_URL",
    "http://127.0.0.1:8002/notification/",
)

INTERNAL_API_KEY = os.getenv(
    "INTERNAL_API_KEY",
    "ecwf-internal-key",
)


class NotificationClient:

    @staticmethod
    async def send_welcome_notification(user):
        payload = {
            "user_id": user.id,
            "title": "Welcome",
            "message": f"Welcome {user.first_name}! Your account has been created.",
            "notification_type": "EMAIL",
        }

        headers = {
            "X-Internal-API-Key": INTERNAL_API_KEY,
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                NOTIFICATION_SERVICE_URL,
                json=payload,
                headers=headers,
            )

        response.raise_for_status()

        return response.json()