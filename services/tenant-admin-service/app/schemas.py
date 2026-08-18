from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=200)
    primary_domain: str = Field(min_length=3, max_length=255)
    organization_type: str = "enterprise"
    industry: str | None = None


class OrganizationProfileUpdate(BaseModel):
    name: str | None = None
    legal_name: str | None = None
    industry: str | None = None
    phone: str | None = None
    website: str | None = None
    logo_url: str | None = None
    address: str | None = None
    postal_code: str | None = None


class TenantSettingsUpdate(BaseModel):
    timezone: str = "Asia/Kolkata"
    currency: str = "INR"
    data_region: str = "India"
    storage_plan: str = "standard"
    user_limit: int = 500
    security_policy: str = "standard"
    require_mfa: bool = False
    session_timeout_minutes: int = 60
    max_concurrent_sessions: int = 3
    allowed_domains: list[str] = Field(default_factory=list)


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=2, max_length=50)
    parent_id: int | None = None
    head_membership_id: int | None = None
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    parent_id: int | None = None
    head_membership_id: int | None = None
    description: str | None = None


class DepartmentStatusUpdate(BaseModel):
    is_active: bool


class InvitationCreate(BaseModel):
    email: EmailStr
    department_id: int | None = Field(default=None, gt=0)
    role_code: Literal["tenant_admin", "tenant_user"] = "tenant_user"


class InvitationAction(BaseModel):
    token: str = Field(min_length=20, max_length=500)


class InvitationResponse(BaseModel):
    id: int
    tenant_id: int
    email: EmailStr
    department_id: int | None
    role_code: str
    status: str
    expires_at: datetime
    created_at: datetime
    last_sent_at: datetime
    accepted_at: datetime | None
    rejected_at: datetime | None
    cancelled_at: datetime | None
    resend_count: int
    model_config = ConfigDict(from_attributes=True)


class MembershipUpdate(BaseModel):
    department_id: int | None = None
    role_code: Literal["tenant_admin", "tenant_user"] | None = None
    status: Literal["active", "inactive"] | None = None
