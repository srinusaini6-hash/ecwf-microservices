from pydantic import BaseModel, Field


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    job_title: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=2000)
    profile_image_url: str | None = Field(default=None, max_length=500)
    locale: str | None = Field(default=None, max_length=20)
    timezone: str | None = Field(default=None, max_length=60)


class AccountSettingsUpdate(BaseModel):
    email_notifications: bool | None = None
    security_notifications: bool | None = None
    theme: str | None = Field(default=None, pattern=r"^(system|light|dark)$")

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
