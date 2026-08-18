from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TenantBase(BaseModel):
    organization_id: int

    name: str = Field(
        ...,
        max_length=255,
    )

    domain: str = Field(
        ...,
        max_length=255,
    )

    email: EmailStr

    phone_number: str | None = Field(
        default=None,
        max_length=20,
    )


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    organization_id: int | None = None

    name: str | None = Field(
        default=None,
        max_length=255,
    )

    domain: str | None = Field(
        default=None,
        max_length=255,
    )

    email: EmailStr | None = None

    phone_number: str | None = Field(
        default=None,
        max_length=20,
    )

    is_active: bool | None = None


class TenantResponse(TenantBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )