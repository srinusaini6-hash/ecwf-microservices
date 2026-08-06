from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


class AuthRepository:

    @staticmethod
    def get_by_email(
        db: Session,
        email: str,
    ) -> User | None:
        stmt = select(User).where(User.email == email)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_id(
        db: Session,
        user_id: int,
    ) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(
        db: Session,
        user: UserCreate,
        password_hash: str,
    ) -> User:

        db_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone_number=user.phone_number,
            organization_id=user.organization_id,
            password_hash=password_hash,
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def update(
        db: Session,
        db_user: User,
    ) -> User:
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete(
        db: Session,
        db_user: User,
    ) -> None:
        db.delete(db_user)
        db.commit()