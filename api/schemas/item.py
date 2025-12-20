from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from enum import Enum
import api.schemas.users as user_schema

class ItemStatus(str, Enum):
    ON_SALE = 'on_sale'
    SOLD_OUT = 'sold_out'
    DRAFT = 'draft'

class Brand(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class Category(BaseModel):
    id: int
    name: str
    depth: int

    class Config:
        from_attributes = True

class CategorySearchResponse(BaseModel):
    id: int
    name: str
    depth: int
    parent: Optional[Category] = None

    class Config:
        from_attributes = True

class Condition(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class ImageResponse(BaseModel):
    id: UUID
    image_url: str

    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, example="Nintendo Switch2")
    price: int = Field(None, example=30000)
    description: Optional[str] = Field(None, example="これは今大人気のゲーム機です！")
    
class ItemCreate(ItemBase):
    category_id: Optional[int] = Field(None, example=102)
    brand_id: Optional[int] = Field(None, example=5)
    condition_id: Optional[int] = Field(None, example=1)

class ItemUpdate(BaseModel):
    title: Optional[str] = Field(None)
    price: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field(None)
    category_id: Optional[int] = Field(None)
    brand_id: Optional[int] = Field(None)
    status: Optional[ItemStatus] = Field(None)

class ItemResponse(ItemBase):
    id: UUID
    seller: user_schema.UserResponse
    status: ItemStatus
    brand: Optional[Brand] = None 
    category: Optional[Category] = None
    condition: Optional[Condition] = None  
    images: List[ImageResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ItemSimpleResponse(BaseModel):
    id: UUID
    seller_id: UUID

    class Config:
        from_attributes = True