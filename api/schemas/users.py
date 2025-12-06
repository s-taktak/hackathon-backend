from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

class Gender(str,Enum):
    MALE ='male'
    FEMALE = 'female'
    UNDEFINED ='undefined'

class UserBase(BaseModel):
    username: Optional[str] = Field(None,example="佐藤太郎")
    #gender: Gender = Field('undefined',example="male")


class UserCreate(UserBase):
    email: EmailStr = Field(None,example ="user@example.com")
    password: str = Field(None,min_length=8,example="secret_password")

class UserInDB(UserBase):
    email: EmailStr
    hashed_password: str

class User(UserBase):
    email: EmailStr = Field(None,example ="user@example.com")

class UserResponse(UserBase):
    id: UUID

    class Config:
        from_attributes = True

class UserMeResponse(UserBase):
    id: UUID
    email: EmailStr = Field(None,example ="user@example.com")

    class Config:
        from_attributes = True

