from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional
from app.models.enums import UserRole, UserStatus

class StudentRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    register_number: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str = Field(..., min_length=6, max_length=100)
    department: str = Field(..., min_length=2, max_length=100)
    year: int = Field(..., ge=1, le=5)
    section: str = Field(..., min_length=1, max_length=10)

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self

class TeacherRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    employee_id: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str = Field(..., min_length=6, max_length=100)
    department: str = Field(..., min_length=2, max_length=100)

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=100, description="College email, full name, or register number")
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str
    role: UserRole
    status: UserStatus

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=100)
    confirm_new_password: str = Field(..., min_length=6, max_length=100)

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.new_password != self.confirm_new_password:
            raise ValueError('Passwords do not match')
        return self

class VerifyEmailRequest(BaseModel):
    token: str

class MessageResponse(BaseModel):
    message: str
    success: bool = True
