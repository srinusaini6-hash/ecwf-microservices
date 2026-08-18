import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

from fastapi import HTTPException
from httpx import AsyncClient

from app.core.config import settings
from app.core.security import create_access_token, create_otp_token, create_refresh_token, decode_token, generate_otp, hash_password, verify_password
from app.repositories import AuthRepository


class AuthService:
    def __init__(self, repo: AuthRepository, http: AsyncClient):
        self.repo = repo
        self.http = http

    async def register(self, data):
        if self.repo.user_by_email(str(data.email)):
            raise HTTPException(409, "Email is already registered")
        otp = generate_otp()
        role = "tenant_admin" if data.account_type == "organization" else "individual_user"
        extra = {
            "full_name": data.full_name,
            "password_hash": hash_password(data.password),
            "account_type": data.account_type,
            "role": role,
        }
        token = create_otp_token(str(data.email), otp, "registration", extra)
        await self._send_otp(str(data.email), otp, "registration")
        return token

    async def verify_registration(self, token: str, submitted_otp: str):
        payload = self._otp_payload(token, "registration")
        self._validate_retry_limit(payload)
        if submitted_otp != payload["otp"]:
            retries = int(payload.get("retry_count", 0)) + 1
            return {"verified": False, "updated_token": self._updated_otp(payload, retries), "remaining_attempts": max(settings.otp_max_retries - retries, 0)}
        email = str(payload["sub"]).lower()
        if self.repo.user_by_email(email):
            raise HTTPException(409, "Email is already registered")
        data = payload["extra"]
        user = self.repo.create_user(email, data["full_name"], data["password_hash"], data["account_type"], data["role"], True)
        try:
            await self._ensure_user_profile(user.id)
        except Exception:
            self.repo.delete_user(user)
            raise
        await self._send_welcome(user.email, user.full_name)
        return {"verified": True, "user": user}

    async def resend_registration_otp(self, token: str):
        payload = self._otp_payload(token, "registration")
        count = int(payload.get("resend_count", 0))
        if count >= settings.otp_max_resends:
            raise HTTPException(429, "Maximum OTP resend limit exceeded")
        otp = generate_otp()
        new_token = create_otp_token(str(payload["sub"]), otp, "registration", payload.get("extra"), resend_count=count + 1)
        await self._send_otp(str(payload["sub"]), otp, "registration")
        return new_token, count + 1

    async def login(self, email: str, password: str, ip_address: str | None = None, user_agent: str | None = None):
        user = self.repo.user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(401, "Invalid email or password")
        if not user.is_active or not user.is_verified:
            raise HTTPException(403, "Account is inactive or not verified")
        mfa = self.repo.mfa(user.id)
        if mfa and mfa.is_enabled and mfa.method == "email":
            otp = generate_otp()
            token = create_otp_token(user.email, otp, "mfa_login", {"user_id": user.id})
            await self._send_otp(user.email, otp, "mfa_login")
            return {"mfa_required": True, "mfa_token": token, "user": user}
        return self._complete_login(user, ip_address, user_agent)

    def refresh(self, refresh_token: str):
        payload = self._decode_or_401(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Invalid refresh token")
        user = self.repo.user_by_id(int(payload["sub"]))
        if not user or not user.is_active or user.token_version != int(payload.get("ver", -1)):
            raise HTTPException(401, "Refresh token is invalid or revoked")
        return create_access_token(user.id, user.token_version), create_refresh_token(user.id, user.token_version)

    def logout(self, refresh_token: str | None):
        if not refresh_token:
            return
        try:
            payload = decode_token(refresh_token)
            user = self.repo.user_by_id(int(payload["sub"]))
        except (ValueError, KeyError, TypeError):
            return
        if user and payload.get("type") == "refresh" and user.token_version == int(payload.get("ver", -1)):
            self.repo.increment_version(user)

    async def forgot_password(self, email: str):
        user = self.repo.user_by_email(email)
        if not user:
            return None
        otp = generate_otp()
        token = create_otp_token(user.email, otp, "password_reset", {"user_id": user.id, "nonce": secrets.token_urlsafe(24)})
        await self._send_otp(user.email, otp, "password_reset")
        return token

    async def verify_reset_otp(self, token: str, submitted_otp: str):
        payload = self._otp_payload(token, "password_reset")
        self._validate_retry_limit(payload)
        if submitted_otp != payload["otp"]:
            retries = int(payload.get("retry_count", 0)) + 1
            return {"verified": False, "updated_token": self._updated_otp(payload, retries), "remaining_attempts": max(settings.otp_max_retries - retries, 0)}
        verified = create_otp_token(str(payload["sub"]), "verified", "password_reset_verified", payload.get("extra"))
        return {"verified": True, "verified_token": verified}

    async def resend_password_reset_otp(self, token: str):
        payload = self._otp_payload(token, "password_reset")
        count = int(payload.get("resend_count", 0))
        if count >= settings.otp_max_resends:
            raise HTTPException(429, "Maximum OTP resend limit exceeded")
        otp = generate_otp()
        new_token = create_otp_token(str(payload["sub"]), otp, "password_reset", payload.get("extra"), resend_count=count + 1)
        await self._send_otp(str(payload["sub"]), otp, "password_reset")
        return new_token, count + 1

    def reset_password(self, token: str, new_password: str):
        payload = self._otp_payload(token, "password_reset_verified")
        user = self.repo.user_by_id(int(payload["extra"]["user_id"]))
        if not user:
            raise HTTPException(404, "User not found")
        if verify_password(new_password, user.password_hash):
            raise HTTPException(400, "New password cannot be the current password")
        self.repo.update_password(user, hash_password(new_password))

    def change_password(self, user, current_password: str, new_password: str):
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(400, "Current password is incorrect")
        if verify_password(new_password, user.password_hash):
            raise HTTPException(400, "New password cannot be the current password")
        self.repo.update_password(user, hash_password(new_password))

    def mfa_status(self, user):
        config = self.repo.mfa(user.id)
        enabled = bool(config and config.is_enabled and config.method == "email")
        return {"mfa_enabled": enabled, "method": "email" if enabled else None, "email": user.email}

    async def setup_mfa(self, user):
        config = self.repo.mfa(user.id)
        if config and config.is_enabled and config.method == "email":
            raise HTTPException(409, "Email OTP MFA is already enabled")
        otp = generate_otp()
        token = create_otp_token(user.email, otp, "mfa_setup", {"user_id": user.id})
        await self._send_otp(user.email, otp, "mfa_setup")
        return token

    def verify_mfa_setup(self, user, token: str, submitted_otp: str):
        payload = self._otp_payload(token, "mfa_setup")
        self._validate_retry_limit(payload)
        if int(payload["extra"].get("user_id", -1)) != user.id:
            raise HTTPException(403, "MFA setup belongs to another user")
        if submitted_otp != payload["otp"]:
            retries = int(payload.get("retry_count", 0)) + 1
            return {"verified": False, "updated_token": self._updated_otp(payload, retries), "remaining_attempts": max(settings.otp_max_retries - retries, 0)}
        self.repo.enable_email_mfa(user.id)
        return {"verified": True}

    def verify_mfa_login(self, token: str, submitted_otp: str):
        payload = self._otp_payload(token, "mfa_login")
        self._validate_retry_limit(payload)
        user = self.repo.user_by_id(int(payload["extra"]["user_id"]))
        if not user or not user.is_active or not user.is_verified:
            raise HTTPException(403, "Account is inactive or not verified")
        config = self.repo.mfa(user.id)
        if not config or not config.is_enabled or config.method != "email":
            raise HTTPException(400, "Email OTP MFA is not enabled")
        if submitted_otp != payload["otp"]:
            retries = int(payload.get("retry_count", 0)) + 1
            return {"verified": False, "updated_token": self._updated_otp(payload, retries), "remaining_attempts": max(settings.otp_max_retries - retries, 0)}
        return self._complete_login(user)

    async def resend_mfa_otp(self, token: str):
        payload = self._otp_payload_any(token, {"mfa_setup", "mfa_login"})
        count = int(payload.get("resend_count", 0))
        if count >= settings.otp_max_resends:
            raise HTTPException(429, "Maximum MFA OTP resend limit exceeded")
        user = self.repo.user_by_id(int(payload["extra"]["user_id"]))
        if not user or not user.is_active:
            raise HTTPException(403, "User is inactive or unavailable")
        otp = generate_otp()
        new_token = create_otp_token(user.email, otp, str(payload["purpose"]), payload.get("extra"), resend_count=count + 1)
        await self._send_otp(user.email, otp, str(payload["purpose"]))
        return new_token, count + 1

    def disable_mfa(self, user):
        config = self.repo.mfa(user.id)
        if not config or not config.is_enabled:
            raise HTTPException(404, "Email OTP MFA is not enabled")
        self.repo.disable_email_mfa(user.id)

    def validate_access(self, token: str):
        payload = self._decode_or_401(token)
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid access token")
        user = self.repo.user_by_id(int(payload["sub"]))
        if not user or not user.is_active or user.token_version != int(payload.get("ver", -1)):
            raise HTTPException(401, "Token is invalid or revoked")
        return user

    async def google_url(self, mode: str, user_id: int | None = None):
        if not settings.google_client_id or not settings.google_client_secret:
            raise HTTPException(503, "Google OAuth is not configured")
        state = secrets.token_urlsafe(32)
        self.repo.create_oauth_state(state, mode, user_id, datetime.utcnow() + timedelta(minutes=settings.oauth_state_expire_minutes))
        params = {"client_id": settings.google_client_id, "redirect_uri": settings.google_redirect_uri, "response_type": "code", "scope": "openid email profile", "state": state, "access_type": "offline", "prompt": "select_account"}
        return f"{settings.google_authorization_url}?{urlencode(params)}"

    async def google_callback(self, code: str, state: str):
        state_obj = self.repo.consume_oauth_state(state)
        if not state_obj:
            raise HTTPException(400, "Invalid or expired OAuth state")
        token_response = await self.http.post(settings.google_token_url, data={"code": code, "client_id": settings.google_client_id, "client_secret": settings.google_client_secret, "redirect_uri": settings.google_redirect_uri, "grant_type": "authorization_code"})
        if token_response.status_code != 200:
            raise HTTPException(502, "Google token exchange failed")
        google_token = token_response.json().get("access_token")
        user_response = await self.http.get(settings.google_userinfo_url, headers={"Authorization": f"Bearer {google_token}"})
        if user_response.status_code != 200:
            raise HTTPException(502, "Unable to retrieve Google user information")
        info = user_response.json()
        if not info.get("email_verified"):
            raise HTTPException(400, "Only verified Google accounts are accepted")
        if state_obj.mode == "link":
            user = self.repo.user_by_id(int(state_obj.user_id or 0))
            if not user:
                raise HTTPException(401, "Authenticated ECWF user is unavailable")
            self._link_google(user, info)
            return {"mode": "link", "message": "Google account linked successfully", "user": user}
        external = self.repo.external_by_subject("google", info["sub"])
        created = False
        if external:
            user = self.repo.user_by_id(external.user_id)
        else:
            user = self.repo.user_by_email(info["email"])
            if not user:
                user = self.repo.create_user(info["email"], info.get("name") or info["email"], hash_password(secrets.token_urlsafe(48)), "individual", "individual_user", True)
                await self._ensure_user_profile(user.id)
                created = True
            self._link_google(user, info)
        if not user or not user.is_active:
            raise HTTPException(403, "Inactive users cannot log in")
        result = self._complete_login(user)
        result.update({"mode": "login", "created": created})
        return result

    def unlink_google(self, user):
        identity = self.repo.external_for_user(user.id, "google")
        if not identity:
            raise HTTPException(404, "Google account is not linked")
        self.repo.unlink_external(identity)

    async def validate_federated_context(self, user_id: int, tenant_id: int):
        user = self.repo.user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(404, "User not found or inactive")
        response = await self.http.get(f"{settings.tenant_admin_service_url}/api/v1/internal/memberships/validate", params={"user_id": user_id, "tenant_id": tenant_id}, headers={"X-Internal-API-Key": settings.internal_api_key})
        if response.status_code >= 400:
            raise HTTPException(response.status_code, response.json().get("detail", "Membership validation failed"))
        return {"user": self._user_dict(user), "membership": response.json()}

    def _link_google(self, user, info):
        existing = self.repo.external_by_subject("google", info["sub"])
        if existing and existing.user_id != user.id:
            raise HTTPException(409, "Google account is linked to another ECWF account")
        already = self.repo.external_for_user(user.id, "google")
        if already:
            if already.provider_subject == info["sub"]:
                return
            raise HTTPException(409, "Google account is already linked")
        self.repo.link_external(user.id, "google", info["sub"], info["email"], True)

    def _complete_login(self, user, ip_address: str | None = None, user_agent: str | None = None):
        if not user or not user.is_active:
            raise HTTPException(403, "Inactive user")
        user.last_login_at = datetime.utcnow()
        self.repo.db.commit()
        access = create_access_token(user.id, user.token_version)
        refresh = create_refresh_token(user.id, user.token_version)
        return {"mfa_required": False, "access_token": access, "refresh_token": refresh, "user": user}

    def _decode_or_401(self, token: str):
        try:
            return decode_token(token)
        except ValueError as exc:
            raise HTTPException(401, str(exc)) from exc

    def _otp_payload(self, token: str, purpose: str):
        try:
            payload = decode_token(token)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        if payload.get("type") != "otp" or payload.get("purpose") != purpose:
            raise HTTPException(400, "Invalid flow token")
        return payload

    def _otp_payload_any(self, token: str, purposes: set[str]):
        try:
            payload = decode_token(token)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        if payload.get("type") != "otp" or payload.get("purpose") not in purposes:
            raise HTTPException(400, "Invalid flow token")
        return payload

    def _validate_retry_limit(self, payload: dict):
        if int(payload.get("retry_count", 0)) >= settings.otp_max_retries:
            raise HTTPException(429, "Maximum OTP verification attempts exceeded")

    def _updated_otp(self, payload: dict, retry_count: int):
        return create_otp_token(str(payload["sub"]), str(payload["otp"]), str(payload["purpose"]), payload.get("extra"), retry_count=retry_count, resend_count=int(payload.get("resend_count", 0)))

    async def _send_otp(self, email: str, otp: str, purpose: str):
        await self._notify(email, f"ECWF {purpose.replace('_', ' ').title()} OTP", f"Your OTP is {otp}. It expires in {settings.otp_token_expire_minutes} minutes.", purpose)

    async def _send_welcome(self, email: str, full_name: str):
        await self._notify(email, "Welcome to ECWF", f"Welcome {full_name}. Your ECWF account is ready.", "welcome")

    async def _notify(self, to: str, subject: str, body: str, template: str):
        if not settings.enable_external_services:
            return
        response = await self.http.post(f"{settings.notification_service_url}/api/v1/notifications/internal/email", headers={"X-Internal-API-Key": settings.internal_api_key}, json={"to": to, "subject": subject, "body": body, "template": template})
        if response.status_code >= 400:
            raise HTTPException(502, {"message": "Notification service failed", "service_response": response.text})

    async def _ensure_user_profile(self, user_id: int):
        if not settings.enable_external_services:
            return
        response = await self.http.post(f"{settings.user_service_url}/api/v1/internal/users/{user_id}/bootstrap", headers={"X-Internal-API-Key": settings.internal_api_key})
        if response.status_code >= 400:
            raise HTTPException(502, "User profile bootstrap failed")

    def _user_dict(user):
        return {"id": user.id, "email": user.email, "full_name": user.full_name, "account_type": user.account_type, "role": user.role, "is_active": user.is_active, "is_verified": user.is_verified, "created_at": user.created_at, "last_login_at": user.last_login_at}
