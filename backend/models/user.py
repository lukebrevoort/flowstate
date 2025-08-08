from sqlalchemy import Boolean, Column, String, Integer, DateTime, Index
from sqlalchemy.sql import func
from db import Base
from pydantic import BaseModel, EmailStr
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
    notion_connected = Column(Boolean, default=False)
    google_calendar_connected = Column(Boolean, default=False)

    __table_args__ = (
        Index('ix_user_email_active', 'email', 'is_active'),  # ✅ Composite index
    )

# Pydantic models for request validation
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    notion_connected: bool = False
    google_calendar_connected: bool = False

    class Config:
        from_attributes = True
