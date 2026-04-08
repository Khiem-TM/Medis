from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, AuthProvider 

# DTO cho các chức năng admin/user_search/.... --> tóm lại là trả về thông tin user
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    phone: Optional[str]
    date_of_birth: Optional[datetime]
    gender: Optional[str]
    address: Optional[str]
    occupation: Optional[str]
    avatar_url: Optional[str]
    role: UserRole
    auth_provider: AuthProvider
    is_active: bool
    created_at: datetime

    # Pydantic v2: tự convert SQLAlchemy model → dict
    model_config = {"from_attributes": True}

class  UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None