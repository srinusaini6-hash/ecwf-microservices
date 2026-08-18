import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import settings


_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def create_token(payload: dict, expires: timedelta) -> str:
    data = payload.copy()
    data.update({"iss": settings.jwt_issuer, "aud": settings.jwt_audience, "exp": datetime.now(timezone.utc) + expires})
    return jwt.encode(data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm], audience=settings.jwt_audience, issuer=settings.jwt_issuer)
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


def create_access_token(user_id: int, version: int) -> str:
    return create_token({"sub": str(user_id), "type": "access", "ver": version}, timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(user_id: int, version: int) -> str:
    return create_token({"sub": str(user_id), "type": "refresh", "ver": version}, timedelta(days=settings.refresh_token_expire_days))


def create_otp_token(email: str, otp: str, purpose: str, extra: dict | None = None, retry_count: int = 0, resend_count: int = 0) -> str:
    return create_token({"sub": email, "type": "otp", "otp": otp, "purpose": purpose, "retry_count": retry_count, "resend_count": resend_count, "extra": extra or {}}, timedelta(minutes=settings.otp_token_expire_minutes))
