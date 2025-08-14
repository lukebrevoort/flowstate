# SQLAlchemy User model removed - now using Supabase
# The User table is now managed by Supabase with the schema in database/supabase_schema.sql

from pydantic import BaseModel, EmailStr
import uuid

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
