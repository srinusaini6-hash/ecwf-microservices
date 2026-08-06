from pydantic import BaseModel, EmailStr
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    message: str 

class ForgotPasswordRequest(BaseModel):
    email: EmailStr    

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=8)    

class MessageResponse(BaseModel):
    message: str    