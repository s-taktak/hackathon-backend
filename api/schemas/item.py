from typing import Optional

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from enum import Enum
import api.schemas.users as user_schema

class ItemStatus(str,Enum):
    ON_SALE = 'on_sale'
    SOLD_OUT = 'sold_out'
    DRAFT = 'draft'


class ItemBase(BaseModel):
    name: Optional[str] = Field(None,min_length=1, max_length=255,example="Nintendo Switch2")
    price: int = Field(None,example=30000)
    description: Optional[str] = Field(None,example="これは今大人気のゲーム機です！")
    category_id: int = Field(0, example=102)
    brand_id: Optional[int] = Field(0, example=5)
    condition_id: int = Field(0, example=1)

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int]= None
    description: Optional[str] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = 2
    status: Optional[ItemStatus] = None

class ItemResponse(ItemBase):
    id: UUID
    seller: user_schema.UserResponse
    status: ItemStatus
    created_at: datetime
    updated_at: datetime

    #images: List[str] = []

    class Config:
        from_attributes = True

