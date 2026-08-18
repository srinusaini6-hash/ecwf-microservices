from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer

from app.core.config import settings


bearer=HTTPBearer(auto_error=False,scheme_name="BearerAuth")


async def current_user(
    request:Request,
    credentials:HTTPAuthorizationCredentials|None=Security(bearer),
):
    token = credentials.credentials if credentials else request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            401,
            "Authentication required. Login first; the HttpOnly access_token cookie is used automatically. For manual Swagger testing, you may copy the cookie value into Authorize.",
        )

    response=await request.app.state.http.post(
        f"{settings.auth_service_url}/api/v1/auth/internal/validate-token",
        headers={
            "Authorization":f"Bearer {token}",
            "X-Internal-API-Key":settings.internal_api_key,
        },
    )

    if response.status_code!=200:
        detail="Invalid access token"
        try:
            detail=response.json().get("detail",detail)
        except Exception:
            pass
        raise HTTPException(response.status_code,detail)

    user=response.json()
    user["_validated_access_token"]=token
    return user
