from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.internal_auth import verify_internal_api_key
from app.database.database import get_db

from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)

from app.services.notification_service import NotificationService

router = APIRouter(
    prefix="/notification",
    tags=["Notification"],
)


# =====================================
# Notification APIs
# =====================================

@router.post(
    "/",
    response_model=NotificationResponse,
)
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_api_key),
):
    return NotificationService.create_notification(
        db,
        notification,
    )


@router.get(
    "/",
    response_model=list[NotificationResponse],
)
def get_all_notifications(
    db: Session = Depends(get_db),
):
    return NotificationService.get_all_notifications(
        db,
    )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
):
    return NotificationService.get_notification(
        db,
        notification_id,
    )


@router.put(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def update_notification(
    notification_id: int,
    notification: NotificationUpdate,
    db: Session = Depends(get_db),
):
    return NotificationService.update_notification(
        db,
        notification_id,
        notification,
    )


@router.delete(
    "/{notification_id}",
)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
):
    return NotificationService.delete_notification(
        db,
        notification_id,
    )