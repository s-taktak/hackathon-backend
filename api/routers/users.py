from fastapi import APIRouter
from typing import List
import api.schemas.users as users_schema
import api.schemas.item as item_schema
import uuid
from uuid import UUID
from datetime import datetime

router = APIRouter()

@router.get("/users/{user_id}",response_model=users_schema.UserResponse)
async def get_user_profile(user_id:UUID):
    return users_schema.UserResponse(id=user_id,userusername="佐藤",gender='male')

@router.get("/users/{user_id}/items",response_model=List[item_schema.ItemResponse])
async def get_users_listings(user_id: UUID):
    return [
        item_schema.ItemResponse(
            id=uuid.uuid1(),
            username="あいう",
            price=1000,
            description="あいう",
            seller_id=1,
            status='on_sale',
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        item_schema.ItemResponse(
            id=uuid.uuid1(),
            username="aiu",
            price=5000,
            description="euo",
            seller_id=2,
            status='on_sale',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
