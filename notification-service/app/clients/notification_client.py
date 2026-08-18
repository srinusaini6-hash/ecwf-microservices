import httpx

NOTIFICATION_SERVICE_URL = "http://127.0.0.1:8002/notification/"


class NotificationClient:

    @staticmethod
    def send_welcome_notification(user):
        payload = {
            "user_id": user.id,
            "title": "Welcome",
            "message": f"Welcome {user.first_name}! Your account has been created.",
            "notification_type": "EMAIL",
        }

        response = httpx.post(
            NOTIFICATION_SERVICE_URL,
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

        return response.json()