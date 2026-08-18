import os
import httpx

ORGANIZATION_SERVICE_URL = os.getenv(
    "ORGANIZATION_SERVICE_URL",
    "http://127.0.0.1:8001/organization/",
)

INTERNAL_API_KEY = os.getenv(
    "INTERNAL_API_KEY",
    "ecwf-internal-key",
)


class OrganizationClient:

    @staticmethod
    async def create_organization(user):
        payload = {
            "name": f"{user.first_name} {user.last_name} Organization",
            "description": "Created during user registration",
            "email": user.email,
            "phone_number": user.phone_number,
            "address": "Default Address",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                ORGANIZATION_SERVICE_URL,
                json=payload,
                headers={
                    "x-internal-api-key": INTERNAL_API_KEY,
                },
            )

        print("Status:", response.status_code)
        print("Response:", response.text)

        response.raise_for_status()

        return response.json()