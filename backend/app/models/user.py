from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum, Text
)
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship
import enum

class AuthProvider(str, enum.Enum):
    local = "local"
    google = "google"

class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, unique=True, primary_key=True)  # UUID hoặc Google sub
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable nếu là Google OAuth
    full_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(10), nullable=True)  # male/female/other
    address = Column(Text, nullable=True)
    occupation = Column(String(100), nullable=True) # nghề nghiệp
    avatar_url = Column(String(500), nullable=True)
    auth_provider = Column(Enum(AuthProvider), default=AuthProvider.local, nullable=False)
    google_id = Column(String(255), nullable=True)  # Chỉ dùng nếu auth_provider = google
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    # Relationships — sẽ thêm dần khi có các bảng liên quan
    # prescriptions = relationship("Prescription", back_populates="user")
    # health_profiles = relationship("HealthProfile", back_populates="user")


    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role,
            "auth_provider": self.auth_provider,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"