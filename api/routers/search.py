from fastapi import APIRouter,Query
import api.schemas.item as item_schema
from typing import List
from uuid import UUID
import uuid
from datetime import datetime

router = APIRouter()

@router.get("/search",response_model=List[item_schema.ItemResponse])
async def search_items(prompt:str=Query(...,min_length=1,max_length=50)):
    return [
        item_schema.ItemResponse(
            id=uuid.uuid1(),
            name=f"{prompt}の関連商品A",
            price=1000,
            description=f"{prompt}に関連する素晴らしい商品です。",
            seller_id=1,
            status='on_sale',
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        item_schema.ItemResponse(
            id=uuid.uuid1(),
            name=f"{prompt}の関連商品B",
            price=5000,
            description=f"{prompt}のデラックス版です。",
            seller_id=2,
            status='on_sale',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
