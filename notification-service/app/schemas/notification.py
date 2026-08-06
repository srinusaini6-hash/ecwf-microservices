from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    user_id: int

    title: str = Field(
        ...,
        max_length=255,
    )

    message: str

    notification_type: str = Field(
        ...,
        max_length=50,
    )


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=255,
    )

    message: str | None = None

    notification_type: str | None = Field(
        default=None,
        max_length=50,
    )

    status: str | None = Field(
        default=None,
        max_length=50,
    )

    is_read: bool | None = None


class NotificationResponse(NotificationBase):
    id: int
    status: str
    is_read: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )