from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
)


class NotificationService:

    @staticmethod
    def create_notification(
        db: Session,
        notification: NotificationCreate,
    ):
        return NotificationRepository.create_notification(
            db,
            notification,
        )

    @staticmethod
    def get_notification(
        db: Session,
        notification_id: int,
    ):
        notification = NotificationRepository.get_notification_by_id(
            db,
            notification_id,
        )

        if not notification:
            raise HTTPException(
                status_code=404,
                detail="Notification not found",
            )

        return notification

    @staticmethod
    def get_all_notifications(db: Session):
        return NotificationRepository.get_all_notifications(db)

    @staticmethod
    def update_notification(
        db: Session,
        notification_id: int,
        notification: NotificationUpdate,
    ):
        db_notification = NotificationRepository.get_notification_by_id(
            db,
            notification_id,
        )

        if not db_notification:
            raise HTTPException(
                status_code=404,
                detail="Notification not found",
            )

        return NotificationRepository.update_notification(
            db,
            db_notification,
            notification,
        )

    @staticmethod
    def delete_notification(
        db: Session,
        notification_id: int,
    ):
        db_notification = NotificationRepository.get_notification_by_id(
            db,
            notification_id,
        )

        if not db_notification:
            raise HTTPException(
                status_code=404,
                detail="Notification not found",
            )

        NotificationRepository.delete_notification(
            db,
            db_notification,
        )

        return {
            "message": "Notification deleted successfully"
        }