import secrets

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, Security
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookies import clear_auth_cookies, clear_flow_cookie, set_auth_cookies, set_flow_cookie
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.repositories import AuthRepository
from app.schemas import ChangePasswordRequest, ForgotPasswordRequest, FullNameUpdate, LoginRequest, LoginResponse, MessageResponse, MFAStatusResponse, OAuthCompleteRequest, OAuthLinkRequest, OTPRequest, RegisterRequest, ResetPasswordRequest, UserResponse
from app.services import AuthService


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
mfa_router = APIRouter(prefix="/api/v1/mfa", tags=["Email OTP MFA"])
oauth_router = APIRouter(tags=["Google OAuth"])
bearer = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


def service(request: Request, db: Session = Depends(get_db)) -> AuthService:
    return AuthService(AuthRepository(db), request.app.state.http)


def require_internal_key(x_internal_api_key: str = Header(..., alias="X-Internal-API-Key",),) -> None:
    if not secrets.compare_digest(x_internal_api_key, settings.internal_api_key,):
        raise HTTPException(
            status_code=401,
            detail="Invalid internal API key",
        )


@router.post("/register", response_model=MessageResponse)
async def register(data: RegisterRequest, response: Response, svc: AuthService = Depends(service)):
    token = await svc.register(data)
    set_flow_cookie(response, settings.registration_otp_cookie_name, token)
    return MessageResponse(message="OTP sent successfully. Verify it within five minutes.")


@router.post("/verify-otp")
async def verify_registration(data: OTPRequest, response: Response, registration_token: str | None = Cookie(default=None, alias=settings.registration_otp_cookie_name), svc: AuthService = Depends(service)):
    if not registration_token:
        raise HTTPException(401, "Registration OTP cookie is missing")
    result = await svc.verify_registration(registration_token, data.otp)
    if not result["verified"]:
        error = JSONResponse(status_code=400, content={"detail": "Invalid OTP", "remaining_attempts": result["remaining_attempts"]})
        set_flow_cookie(error, settings.registration_otp_cookie_name, result["updated_token"])
        return error
    clear_flow_cookie(response, settings.registration_otp_cookie_name)
    return {"message": "Registration completed successfully", "user": UserResponse.model_validate(result["user"])}


@router.post("/resend-otp", response_model=MessageResponse)
async def resend_registration(response: Response, registration_token: str | None = Cookie(default=None, alias=settings.registration_otp_cookie_name), svc: AuthService = Depends(service)):
    if not registration_token:
        raise HTTPException(401, "Registration OTP cookie is missing")
    token, count = await svc.resend_registration_otp(registration_token)
    set_flow_cookie(response, settings.registration_otp_cookie_name, token)
    return MessageResponse(message="OTP resent successfully", resend_count=count)


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, request: Request, response: Response, svc: AuthService = Depends(service)):
    result = await svc.login(str(data.email), data.password, request.client.host if request.client else None, request.headers.get("user-agent"))
    if result["mfa_required"]:
        clear_auth_cookies(response)
        set_flow_cookie(response, settings.mfa_otp_cookie_name, result["mfa_token"])
        return LoginResponse(message="Password verified. Email OTP MFA verification is required.", user=UserResponse.model_validate(result["user"]), mfa_required=True)
    clear_flow_cookie(response, settings.mfa_otp_cookie_name)
    set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return LoginResponse(message="Login successful", user=UserResponse.model_validate(result["user"]), mfa_required=False)


@router.post("/refresh-token", response_model=MessageResponse)
@router.post("/refresh", response_model=MessageResponse, include_in_schema=False)
def refresh_token(response: Response, refresh_token_value: str | None = Cookie(default=None, alias=settings.refresh_cookie_name), svc: AuthService = Depends(service)):
    if not refresh_token_value:
        raise HTTPException(401, "Refresh-token cookie is missing")
    access, refresh = svc.refresh(refresh_token_value)
    set_auth_cookies(response, access, refresh)
    return MessageResponse(message="Session refreshed successfully")


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response, refresh_token_value: str | None = Cookie(default=None, alias=settings.refresh_cookie_name), svc: AuthService = Depends(service)):
    svc.logout(refresh_token_value)
    clear_auth_cookies(response)
    clear_flow_cookie(response, settings.mfa_otp_cookie_name)
    return MessageResponse(message="Logged out successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest, response: Response, svc: AuthService = Depends(service)):
    token = await svc.forgot_password(str(data.email))
    if token:
        set_flow_cookie(response, settings.password_reset_otp_cookie_name, token)
    return MessageResponse(message="If the account exists, an OTP has been sent.")


@router.post("/verify-forgot-otp")
@router.post("/verify-reset-otp", include_in_schema=False)
async def verify_forgot_otp(data: OTPRequest, response: Response, reset_token: str | None = Cookie(default=None, alias=settings.password_reset_otp_cookie_name), svc: AuthService = Depends(service)):
    if not reset_token:
        raise HTTPException(401, "Password-reset OTP cookie is missing")
    result = await svc.verify_reset_otp(reset_token, data.otp)
    if not result["verified"]:
        error = JSONResponse(status_code=400, content={"detail": "Invalid OTP", "remaining_attempts": result["remaining_attempts"]})
        set_flow_cookie(error, settings.password_reset_otp_cookie_name, result["updated_token"])
        return error
    clear_flow_cookie(response, settings.password_reset_otp_cookie_name)
    set_flow_cookie(response, settings.password_reset_verified_cookie_name, result["verified_token"])
    return MessageResponse(message="Password-reset OTP verified successfully")


@router.post("/resend-forgot-otp", response_model=MessageResponse)
async def resend_forgot_otp(response: Response, reset_token: str | None = Cookie(default=None, alias=settings.password_reset_otp_cookie_name), svc: AuthService = Depends(service)):
    if not reset_token:
        raise HTTPException(401, "Password-reset OTP cookie is missing")
    token, count = await svc.resend_password_reset_otp(reset_token)
    set_flow_cookie(response, settings.password_reset_otp_cookie_name, token)
    return MessageResponse(message="Password-reset OTP resent successfully", resend_count=count)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(data: ResetPasswordRequest, response: Response, verified_token: str | None = Cookie(default=None, alias=settings.password_reset_verified_cookie_name), svc: AuthService = Depends(service)):
    if not verified_token:
        raise HTTPException(401, "Verified password-reset cookie is missing")
    svc.reset_password(verified_token, data.new_password)
    clear_flow_cookie(response, settings.password_reset_verified_cookie_name)
    clear_auth_cookies(response)
    return MessageResponse(message="Password updated successfully")


@router.post("/change-password", response_model=MessageResponse)
def change_password(data: ChangePasswordRequest, response: Response, user=Depends(get_current_user), svc: AuthService = Depends(service)):
    svc.change_password(user, data.current_password, data.new_password)
    clear_auth_cookies(response)
    return MessageResponse(message="Password changed successfully. Please log in again.")


@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return user


@mfa_router.get("/status", response_model=MFAStatusResponse)
def mfa_status(user=Depends(get_current_user), svc: AuthService = Depends(service)):
    return svc.mfa_status(user)


@mfa_router.post("/setup/email", response_model=MessageResponse)
async def setup_email_mfa(response: Response, user=Depends(get_current_user), svc: AuthService = Depends(service)):
    token = await svc.setup_mfa(user)
    set_flow_cookie(response, settings.mfa_otp_cookie_name, token)
    return MessageResponse(message="Email OTP sent. Verify it to enable MFA.")


@mfa_router.post("/setup/email/verify", response_model=MessageResponse)
def verify_email_mfa_setup(data: OTPRequest, response: Response, mfa_token: str | None = Cookie(default=None, alias=settings.mfa_otp_cookie_name), user=Depends(get_current_user), svc: AuthService = Depends(service)):
    if not mfa_token:
        raise HTTPException(401, "MFA OTP cookie is missing")
    result = svc.verify_mfa_setup(user, mfa_token, data.otp)
    if not result["verified"]:
        error = JSONResponse(status_code=400, content={"detail": "Invalid MFA OTP", "remaining_attempts": result["remaining_attempts"]})
        set_flow_cookie(error, settings.mfa_otp_cookie_name, result["updated_token"])
        return error
    clear_flow_cookie(response, settings.mfa_otp_cookie_name)
    return MessageResponse(message="Email OTP MFA enabled successfully")


@mfa_router.post("/verify", response_model=LoginResponse)
def verify_login_mfa(data: OTPRequest, response: Response, mfa_token: str | None = Cookie(default=None, alias=settings.mfa_otp_cookie_name), svc: AuthService = Depends(service)):
    if not mfa_token:
        raise HTTPException(401, "MFA challenge cookie is missing")
    result = svc.verify_mfa_login(mfa_token, data.otp)
    if result.get("verified") is False:
        error = JSONResponse(status_code=400, content={"detail": "Invalid MFA OTP", "remaining_attempts": result["remaining_attempts"]})
        set_flow_cookie(error, settings.mfa_otp_cookie_name, result["updated_token"])
        return error
    clear_flow_cookie(response, settings.mfa_otp_cookie_name)
    set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return LoginResponse(message="MFA verified. Login successful.", user=UserResponse.model_validate(result["user"]), mfa_required=False)


@mfa_router.post("/resend", response_model=MessageResponse)
async def resend_mfa(response: Response, mfa_token: str | None = Cookie(default=None, alias=settings.mfa_otp_cookie_name), svc: AuthService = Depends(service)):
    if not mfa_token:
        raise HTTPException(401, "MFA OTP cookie is missing")
    token, count = await svc.resend_mfa_otp(mfa_token)
    set_flow_cookie(response, settings.mfa_otp_cookie_name, token)
    return MessageResponse(message="MFA OTP resent successfully", resend_count=count)


@mfa_router.delete("/email", response_model=MessageResponse)
def disable_mfa(response: Response, user=Depends(get_current_user), svc: AuthService = Depends(service)):
    svc.disable_mfa(user)
    clear_flow_cookie(response, settings.mfa_otp_cookie_name)
    return MessageResponse(message="Email OTP MFA disabled successfully")


@oauth_router.get("/auth/google/login")
async def google_login(svc: AuthService = Depends(service)):
    return RedirectResponse(await svc.google_url("login"))


@oauth_router.get("/auth/google/link")
async def google_link_start(user=Depends(get_current_user), svc: AuthService = Depends(service)):
    return RedirectResponse(await svc.google_url("link", user.id))


@oauth_router.get("/auth/google/callback")
async def google_callback(code: str, state: str, response: Response, svc: AuthService = Depends(service)):
    result = await svc.google_callback(code, state)
    if result["mode"] == "link":
        return {"message": result["message"]}
    set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return {"message": "Google login successful", "user": UserResponse.model_validate(result["user"]), "created": result["created"]}


@oauth_router.post("/auth/google/link", include_in_schema=True)
async def google_link_compat(code: str, state: str, response: Response, svc: AuthService = Depends(service)):
    result = await svc.google_callback(code, state)
    if result["mode"] != "link":
        raise HTTPException(400, "OAuth state is not a link flow")
    return {"message": result["message"]}


@oauth_router.delete("/auth/google/unlink", response_model=MessageResponse)
def google_unlink(user=Depends(get_current_user), svc: AuthService = Depends(service)):
    svc.unlink_google(user)
    return MessageResponse(message="Google account unlinked successfully")


@oauth_router.post("/auth/google/logout", response_model=MessageResponse)
def google_logout(response: Response):
    clear_auth_cookies(response)
    return MessageResponse(message="Logged out successfully")




@router.get("/internal/users/by-email", dependencies=[Depends(require_internal_key)])
def internal_user_by_email(email: str, db: Session = Depends(get_db)):
    user = AuthRepository(db).user_by_email(email)
    if not user:
        raise HTTPException(404, "Registered user not found")
    return _user_dict(user)

@router.get("/internal/users/{user_id}", dependencies=[Depends(require_internal_key)])
def internal_user(user_id: int, db: Session = Depends(get_db)):
    user = AuthRepository(db).user_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return _user_dict(user)

@router.get("/internal/users/{user_id}/oauth-providers", dependencies=[Depends(require_internal_key)])
def internal_oauth_providers(user_id: int, db: Session = Depends(get_db)):
    repo = AuthRepository(db)
    user = repo.user_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    providers = ["google"] if repo.external_for_user(user_id, "google") else []
    return {"user_id": user_id, "oauth_providers": providers}

@router.patch("/internal/users/{user_id}/full-name", dependencies=[Depends(require_internal_key)])
def internal_update_full_name(user_id: int, data: FullNameUpdate, db: Session = Depends(get_db)):
    repo = AuthRepository(db)
    user = repo.user_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return _user_dict(repo.update_full_name(user, data.full_name))


@router.post(
    "/internal/validate-token",
    dependencies=[
        Depends(require_internal_key)
    ],
    include_in_schema=False,
)

@router.post(
    "/internal/token/context",
    dependencies=[
        Depends(require_internal_key)
    ],
    include_in_schema=False,
)
def token_context(credentials: HTTPAuthorizationCredentials | None = Security(bearer), svc: AuthService = Depends(service),):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Bearer access token is required",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Bearer authentication is required",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    return _user_dict(
        svc.validate_access(
            credentials.credentials
        )
    )


@router.post("/internal/oauth/complete", dependencies=[Depends(require_internal_key)])
def internal_oauth_complete(data: OAuthCompleteRequest, response: Response, db: Session = Depends(get_db)):
    if not data.email_verified:
        raise HTTPException(400, "Only verified Google accounts are accepted")
    repo = AuthRepository(db)
    external = repo.external_by_subject("google", data.provider_subject)
    created = False
    if external:
        user = repo.user_by_id(external.user_id)
    else:
        user = repo.user_by_email(str(data.email))
        if not user:
            user = repo.create_user(str(data.email), data.full_name, hash_password(secrets.token_urlsafe(48)), "individual", "individual_user", True)
            created = True
        if not repo.external_for_user(user.id, "google"):
            repo.link_external(user.id, "google", data.provider_subject, str(data.email), True)
    if not user or not user.is_active:
        raise HTTPException(403, "Inactive users cannot log in")
    access = create_access_token(user.id, user.token_version)
    refresh = create_refresh_token(user.id, user.token_version)
    set_auth_cookies(response, access, refresh)
    return {"message": "OAuth login completed", "user": _user_dict(user), "created": created}


@router.post(
    "/internal/oauth/link",
    dependencies=[Depends(require_internal_key)],
    include_in_schema=False,
)
def internal_oauth_link(
    data: OAuthLinkRequest,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
    svc: AuthService = Depends(service),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Bearer access token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = svc.validate_access(credentials.credentials)

    if not data.email_verified:
        raise HTTPException(400, "Google email is not verified")

    info = {
        "sub": data.provider_subject,
        "email": str(data.email),
        "email_verified": True,
    }
    svc._link_google(user, info)

    return {"message": "Google account linked successfully"}


@router.delete(
    "/internal/oauth/unlink",
    dependencies=[Depends(require_internal_key)],
    include_in_schema=False,
)
def internal_oauth_unlink(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
    svc: AuthService = Depends(service),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Bearer access token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = svc.validate_access(credentials.credentials)
    identity = svc.repo.external_for_user(user.id, "google")

    if not identity:
        raise HTTPException(404, "Google account is not linked")

    svc.repo.unlink_external(identity)

    return {"message": "Google account unlinked successfully"}


async def _tenant_context(user_id: int, http: AsyncClient):
    response = await http.get(f"{settings.tenant_admin_service_url}/api/v1/internal/memberships/by-user/{user_id}", headers={"X-Internal-API-Key": settings.internal_api_key})
    if response.status_code >= 400:
        raise HTTPException(response.status_code, response.json().get("detail", "Organization membership required"))
    return response.json()


def _user_dict(user):
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "account_type": user.account_type, "role": user.role, "is_active": user.is_active, "is_verified": user.is_verified, "created_at": user.created_at}
