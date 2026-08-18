from fastapi import HTTPException
from httpx import AsyncClient

from app.core.config import settings
from app.repositories import UserRepository


class UserService:
    def __init__(self, repo: UserRepository, http: AsyncClient):
        self.repo = repo
        self.http = http

    async def profile(self, user: dict):
        profile, account_settings = self.repo.ensure(user["id"])
        return {
            "user": {k: v for k, v in user.items() if not k.startswith("_")},
            "phone": profile.phone,
            "job_title": profile.job_title,
            "bio": profile.bio,
            "profile_image_url": profile.profile_image_url,
            "locale": profile.locale,
            "timezone": profile.timezone,
            "email_notifications": account_settings.email_notifications,
            "security_notifications": account_settings.security_notifications,
            "theme": account_settings.theme,
        }

    async def update_profile(self, data, user: dict):
        values = data.model_dump(exclude_unset=True)
        full_name = values.pop("full_name", None)
        if full_name is not None:
            response = await self.http.patch(f"{settings.auth_service_url}/api/v1/auth/internal/users/{user['id']}/full-name", headers={"X-Internal-API-Key": settings.internal_api_key}, json={"full_name": full_name})
            if response.status_code >= 400:
                raise HTTPException(response.status_code, response.json().get("detail", "Unable to update user name"))
            user.update(response.json())
        self.repo.update_profile(user["id"], values)
        return await self.profile(user)

    async def update_settings(self, data, user: dict):
        self.repo.update_settings(user["id"], data.model_dump(exclude_unset=True))
        return await self.profile(user)

    async def dashboard(self, user: dict):
        profile = await self.profile(user)
        response = await self.http.get(f"{settings.auth_service_url}/api/v1/auth/internal/users/{user['id']}/oauth-providers", headers={"X-Internal-API-Key": settings.internal_api_key})
        providers = response.json().get("oauth_providers", []) if response.status_code == 200 else []
        tenant_context = None
        tenant_response = await self.http.get(f"{settings.tenant_admin_service_url}/api/v1/internal/memberships/by-user/{user['id']}", headers={"X-Internal-API-Key": settings.internal_api_key})
        if tenant_response.status_code == 200:
            tenant_context = tenant_response.json()
        return {"profile": profile, "session_storage": "http_only_cookies", "last_login_at": user.get("last_login_at"), "oauth_providers": providers, "organization_membership": tenant_context}

    async def change_password(self, data, user: dict):
        response = await self.http.post(f"{settings.auth_service_url}/api/v1/auth/change-password", headers={"Authorization": f"Bearer {user['_validated_access_token']}"}, json=data.model_dump())
        if response.status_code >= 400:
            raise HTTPException(response.status_code, response.json().get("detail", "Password change failed"))
        return response.json()
