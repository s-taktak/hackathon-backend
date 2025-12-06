from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional
import users as user_schema
import item as item_schema

class OrderBase(BaseModel):
    item_id: UUID
    
class OrderCreate(OrderBase):
    payment_method_id: str
    #shipping_address_id: UUID

class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    seller: user_schema.UserResponse
    item: item_schema.ItemResponse