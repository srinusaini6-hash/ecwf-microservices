import hashlib
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExternalIdentity, MFAConfiguration, OAuthState, User


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def user_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def user_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def create_user(self, email: str, full_name: str, password_hash: str, account_type: str, role: str, verified: bool = True) -> User:
        user = User(email=email.lower(), full_name=full_name, password_hash=password_hash, account_type=account_type, role=role, is_active=True, is_verified=verified)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()

    def update_password(self, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        user.token_version += 1
        self.db.commit()
        self.db.refresh(user)

    def update_full_name(self, user: User, full_name: str) -> User:
        user.full_name = full_name
        self.db.commit()
        self.db.refresh(user)
        return user

    def increment_version(self, user: User) -> None:
        user.token_version += 1
        self.db.commit()

    def mfa(self, user_id: int) -> MFAConfiguration | None:
        return self.db.get(MFAConfiguration, user_id)

    def enable_email_mfa(self, user_id: int) -> MFAConfiguration:
        obj = self.mfa(user_id)
        if not obj:
            obj = MFAConfiguration(user_id=user_id, method="email", is_enabled=True)
            self.db.add(obj)
        else:
            obj.method = "email"
            obj.is_enabled = True
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def disable_email_mfa(self, user_id: int) -> MFAConfiguration | None:
        obj = self.mfa(user_id)
        if obj:
            obj.is_enabled = False
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def external_by_subject(self, provider: str, subject: str) -> ExternalIdentity | None:
        return self.db.scalar(select(ExternalIdentity).where(ExternalIdentity.provider == provider, ExternalIdentity.provider_subject == subject))

    def external_for_user(self, user_id: int, provider: str) -> ExternalIdentity | None:
        return self.db.scalar(select(ExternalIdentity).where(ExternalIdentity.user_id == user_id, ExternalIdentity.provider == provider))

    def link_external(self, user_id: int, provider: str, subject: str, email: str, verified: bool) -> ExternalIdentity:
        obj = ExternalIdentity(user_id=user_id, provider=provider, provider_subject=subject, provider_email=email, email_verified=verified)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def unlink_external(self, obj: ExternalIdentity) -> None:
        self.db.delete(obj)
        self.db.commit()

    def create_oauth_state(self, raw_state: str, mode: str, user_id: int | None, expires_at: datetime) -> None:
        state_hash = hashlib.sha256(raw_state.encode()).hexdigest()
        self.db.add(OAuthState(state_hash=state_hash, mode=mode, user_id=user_id, expires_at=expires_at, used=False))
        self.db.commit()

    def consume_oauth_state(self, raw_state: str) -> OAuthState | None:
        state_hash = hashlib.sha256(raw_state.encode()).hexdigest()
        obj = self.db.get(OAuthState, state_hash)
        if not obj or obj.used or obj.expires_at <= datetime.utcnow():
            return None
        obj.used = True
        self.db.commit()
        self.db.refresh(obj)
        return obj
