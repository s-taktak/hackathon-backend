from fastapi import Depends,APIRouter
from typing import List
import api.schemas.users as users_schema
import api.schemas.item as item_schema
import api.schemas.history as history_schema
from api.deps import get_current_user
import uuid
from uuid import UUID
from datetime import datetime
from typing import Annotated
from api.deps import get_current_user


router = APIRouter()

@router.get("/users/me",response_model=users_schema.User)
async def get_my_profile(
    current_user: Annotated[users_schema.User, Depends(get_current_user)],
):     
    return current_user

@router.get("/users/me/items",response_model=List[item_schema.ItemResponse])
async def get_my_listings():
    return [
        item_schema.ItemResponse(
            id=uuid.uuid1(),
            name="あいう",
            price=1000,
            description="あいう",
            seller_id=1,
            status='on_sale',
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        item_schema.ItemResponse(
            id=uuid.uuid1(),
            name="aiu",
            price=5000,
            description="euo",
            seller_id=2,
            status='on_sale',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]


@router.post("/users/me/history",response_model=history_schema.HistoryResponse)
async def record_item_view(item_id:UUID):
    return history_schema.HistoryResponse()

