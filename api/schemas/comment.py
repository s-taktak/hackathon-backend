from pydantic import BaseModel, Field
from uuid import UUID 
from datetime import datetime
from typing import Optional
from api.schemas.item import ItemSimpleResponse

class CommentBase(BaseModel):
    content: str = Field(min_length=1,max_length=1000,example="値下げ可能ですか？")

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id : UUID
    item_id : UUID
    username: str
    isSeller: bool
    created_at: datetime

    class Config:
        from_attributes = True