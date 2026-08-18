import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


PERSONAL_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"}


def validate_password_strength(value: str) -> str:
    if (not value[0].isalnum() and value[0] != "_"):
        raise ValueError(
            "Password cannot start with a special character "
            "except underscore (_)"
        )

    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one digit")

    if not re.search(r"[^A-Za-z0-9]", value):
        raise ValueError("Password must contain at least one special character")

    return value


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=16)
    confirm_password: str = Field(min_length=8, max_length=16)
    account_type: Literal["individual", "organization"]

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @model_validator(mode="after")
    def validate_registration(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password must match")
        domain = str(self.email).rsplit("@", 1)[1].lower()
        if self.account_type == "individual" and domain not in PERSONAL_EMAIL_DOMAINS:
            raise ValueError("Individual accounts must use a supported personal email address")
        if self.account_type == "organization" and domain in PERSONAL_EMAIL_DOMAINS:
            raise ValueError("Organization accounts must use an official business email address")
        return self


class OTPRequest(BaseModel):
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=16)
    confirm_password: str = Field(min_length=8, max_length=16)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Password and confirm password must match")
        return self


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=16)
    confirm_password: str = Field(min_length=8, max_length=16)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.new_password != self.confirm_password:
            raise ValueError("New password and confirm password must match")
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from current password")
        return self


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    account_type: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    message: str = "Login successful"
    user: UserResponse | None = None
    mfa_required: bool = False


class MessageResponse(BaseModel):
    message: str
    remaining_attempts: int | None = None
    resend_count: int | None = None


class MFAStatusResponse(BaseModel):
    mfa_enabled: bool
    method: str | None = None
    email: EmailStr


class FullNameUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)

class OAuthCompleteRequest(BaseModel):
    provider_subject: str
    email: EmailStr
    full_name: str
    email_verified: bool


class OAuthLinkRequest(OAuthCompleteRequest):
    pass


class OAuthUnlinkRequest(BaseModel):
    pass
