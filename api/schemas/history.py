from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional
import api.schemas.item as item_schema


class HistoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    viewed_at: datetime

    item: Optional[item_schema.ItemSimpleResponse] = None
    class Config:
        from_attributes = True