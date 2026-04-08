from pydantic import BaseModel, EmailStr, field_validator, model_validator  
from typing import Optional
import re

# Định nghĩa DTO cho đăng ký
class RegisterRequest(BaseModel): 
    full_name: str
    phone: str
    email: EmailStr
    username: str
    password: str
    confirm_password: str   

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name is required")
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3 or len(v) > 30:
            raise ValueError("Username must be between 3 and 30 characters")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username must contain only letters, numbers, and underscores")
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        errors = []
        if len(v) < 6:
            errors.append("Password must be at least 6 characters")
        if not re.search(r"[A-Z]", v):
            errors.append("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            errors.append("Password must contain at least one digit")
        if not re.search(r"[@$!%*?&]", v):
            errors.append("Password must contain at least one special character (@$!%*?&)")
        if errors:
            raise ValueError(" ".join(errors))
        return v
    
    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

# Định nghĩa DTO cho đăng nhập
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResendVerificationRequest(BaseModel):
    email: EmailStr

# Định nghĩa DTO cho reset password
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        errors = []
        if len(v) < 14:
            errors.append("Password must be at least 14 characters")
        if not re.search(r"[A-Z]", v):
            errors.append("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            errors.append("Password must contain at least one digit")
        if not re.search(r"[@$!%*?&]", v):
            errors.append("Password must contain at least one special character (@$!%*?&)")
        if errors:
            raise ValueError(" ".join(errors))
        return v

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self
    
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError('Mật khẩu nhập lại không khớp')
        return self