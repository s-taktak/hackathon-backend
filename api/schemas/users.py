from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from enum import Enum

class Gender(str, Enum):
    MALE = 'male'
    FEMALE = 'female'
    UNDEFINED = 'undefined'

class UserBase(BaseModel):
    username: Optional[str] = Field(None, example="佐藤太郎")
    gender: Gender = Gender.UNDEFINED

class UserCreate(UserBase):
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., min_length=8, example="secret_password")
    birth_date: Optional[date] = Field(None, example="2000-01-01")

class UserInDB(UserBase):
    email: EmailStr
    hashed_password: str

class UserResponse(UserBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True

class UserMeResponse(UserResponse):
    email: EmailStr 
    birth_date: Optional[date] 

    class Config:
        from_attributes = True
        use_enum_values = True