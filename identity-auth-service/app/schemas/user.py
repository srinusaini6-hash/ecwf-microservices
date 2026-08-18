from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    first_name: str = Field(
        ...,
        max_length=100,
    )

    last_name: str = Field(
        ...,
        max_length=100,
    )

    email: EmailStr

    phone_number: str = Field(
        ...,
        max_length=20,
    )


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
    )

    # Will be set internally by Identity Service
    organization_id: int | None = None


class UserUpdate(BaseModel):
    first_name: str | None = Field(
        default=None,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        max_length=100,
    )

    phone_number: str | None = Field(
        default=None,
        max_length=20,
    )


class UserResponse(UserBase):
    id: int
    organization_id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )