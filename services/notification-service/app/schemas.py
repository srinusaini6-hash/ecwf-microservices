from pydantic import BaseModel, EmailStr, Field


class EmailCreate(BaseModel):
    to: EmailStr
    subject: str
    body: str
    template: str = "generic"
    tenant_id: int | None = None
    actor_user_id: int | None = None
    event_context: dict = Field(default_factory=dict)
