from sqlalchemy.orm import Session

from app.clients.organization_client import OrganizationClient
from app.clients.notification_client import NotificationClient

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)

from app.repositories.auth_repository import AuthRepository

from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    ChangePasswordRequest,
)

from app.schemas.user import (
    UserCreate,
    UserUpdate,
)


class AuthService:

    @staticmethod
    async def register_user(
        db: Session,
        user: UserCreate,
    ):
        existing_user = AuthRepository.get_by_email(
            db,
            user.email,
        )

        if existing_user:
            raise ValueError(
                "Email already registered"
            )

        # Create organization
        organization = await OrganizationClient.create_organization(
            user,
        )

        # Save organization id
        user.organization_id = organization["id"]

        # Hash password
        password_hash = hash_password(
            user.password,
        )

        # Create user
        db_user = AuthRepository.create(
            db=db,
            user=user,
            password_hash=password_hash,
        )

        # Send welcome notification
        await NotificationClient.send_welcome_notification(
            db_user,
        )

        return db_user

    @staticmethod
    def login_user(
        db: Session,
        login_data: LoginRequest,
    ) -> TokenResponse:

        user = AuthRepository.get_by_email(
            db,
            login_data.email,
        )

        if not user:
            raise ValueError(
                "Invalid email or password"
            )

        if not verify_password(
            login_data.password,
            user.password_hash,
        ):
            raise ValueError(
                "Invalid email or password"
            )

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
            }
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )

    @staticmethod
    def login_user(
        db: Session,
        login_data: LoginRequest,
    ) -> TokenResponse:

        user = AuthRepository.get_by_email(
            db,
            login_data.email,
        )

        if not user:
            raise ValueError("Invalid email or password")

        if not verify_password(
            login_data.password,
            user.password_hash,
        ):
            raise ValueError("Invalid email or password")

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
            }
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )

    @staticmethod
    def get_user_by_email(
        db: Session,
        email: str,
    ):
        return AuthRepository.get_by_email(
            db,
            email,
        )

    @staticmethod
    def get_user_by_id(
        db: Session,
        user_id: int,
    ):
        return AuthRepository.get_by_id(
            db,
            user_id,
        )

    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        user_update: UserUpdate,
    ):
        db_user = AuthRepository.get_by_id(
            db,
            user_id,
        )

        if not db_user:
            raise ValueError("User not found")

        update_data = user_update.model_dump(
            exclude_unset=True,
        )

        for key, value in update_data.items():
            setattr(
                db_user,
                key,
                value,
            )

        return AuthRepository.update(
            db,
            db_user,
        )

    @staticmethod
    def change_password(
        db: Session,
        current_user,
        password_data: ChangePasswordRequest,
    ):
        # Fetch the user using the SAME session
        db_user = AuthRepository.get_by_id(
            db,
            current_user.id,
        )

        if not db_user:
            raise ValueError("User not found")

        if not verify_password(
            password_data.current_password,
            db_user.password_hash,
        ):
            raise ValueError(
                "Current password is incorrect"
            )

        db_user.password_hash = hash_password(
            password_data.new_password,
        )

        AuthRepository.update(
            db,
            db_user,
        )

        return {
            "message": "Password changed successfully"
        }
    @staticmethod
    def forgot_password(
        db: Session,
        email: str,
    ):
        user = AuthRepository.get_by_email(
            db,
            email,
        )

        if not user:
            raise ValueError("User not found")

        return {
            "message": "Password reset request accepted"
        }

    @staticmethod
    def reset_password(
        db: Session,
        email: str,
        new_password: str,
    ):
        user = AuthRepository.get_by_email(
            db,
            email,
        )

        if not user:
            raise ValueError("User not found")

        user.password_hash = hash_password(
            new_password,
        )

        AuthRepository.update(
            db,
            user,
        )

        return {
            "message": "Password reset successfully"
        }

    @staticmethod
    def logout():
        return {
            "message": "Logout successful"
        }

    @staticmethod
    def delete_user(
        db: Session,
        user_id: int,
    ):
        user = AuthRepository.get_by_id(
            db,
            user_id,
        )

        if not user:
            raise ValueError("User not found")

        AuthRepository.delete(
            db,
            user,
        )

        return {
            "message": "User deleted successfully"
        }