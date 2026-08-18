from fastapi import Cookie, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings


bearer = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


async def current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Security(bearer), access_token: str | None = Cookie(default=None, alias="access_token")):
    token = credentials.credentials if credentials else access_token
    if not token:
        raise HTTPException(401, "Authentication required. Login first or use Swagger Authorize with the access-token cookie value.")
    response = await request.app.state.http.post(f"{settings.auth_service_url}/api/v1/auth/internal/validate-token", headers={"Authorization": f"Bearer {token}", "X-Internal-API-Key": settings.internal_api_key})
    if response.status_code != 200:
        detail = "Invalid access token"
        try:
            detail = response.json().get("detail", detail)
        except Exception:
            pass
        raise HTTPException(response.status_code, detail)
    user = response.json()
    user["_validated_access_token"] = token
    return user
