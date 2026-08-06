from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
)


class NotificationRepository:

    @staticmethod
    def create_notification(
        db: Session,
        notification: NotificationCreate,
    ):
        db_notification = Notification(**notification.model_dump())
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
        return db_notification

    @staticmethod
    def get_notification_by_id(
        db: Session,
        notification_id: int,
    ):
        return (
            db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )

    @staticmethod
    def get_all_notifications(db: Session):
        return db.query(Notification).all()

    @staticmethod
    def update_notification(
        db: Session,
        db_notification: Notification,
        notification: NotificationUpdate,
    ):
        update_data = notification.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(db_notification, key, value)

        db.commit()
        db.refresh(db_notification)
        return db_notification

    @staticmethod
    def delete_notification(
        db: Session,
        db_notification: Notification,
    ):
        db.delete(db_notification)
        db.commit()