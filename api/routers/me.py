from fastapi import Depends, APIRouter
from api.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import api.schemas.users as users_schema
import api.schemas.item as item_schema
import api.schemas.history as history_schema
from api.routers.auth import get_current_user
import api.cruds.item as item_crud
import api.cruds.history as history_crud
import uuid
from uuid import UUID
from datetime import datetime
from typing import Annotated

router = APIRouter()

@router.get("/users/me", response_model=users_schema.UserMeResponse, operation_id="getMyProfile", tags=["Me"])
async def get_my_profile(
    current_user: Annotated[users_schema.UserMeResponse, Depends(get_current_user)],
): 
    return current_user

@router.get("/users/me/items", response_model=List[item_schema.ItemResponse], operation_id="getMyListing", tags=["Me"])
async def get_my_listings(
    current_user: Annotated[users_schema.UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    return await item_crud.get_items_by_user_id(db, str(current_user.id))

@router.get("/users/me/purchased", response_model=list[item_schema.ItemResponse], operation_id="getPurchasedItems", tags=["Me"])
async def get_purchased_items(
    current_user: Annotated[users_schema.UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    return await item_crud.get_purchased_items_by_user(db, user_id=str(current_user.id))

@router.get("/users/me/history", response_model=List[history_schema.HistoryResponse], operation_id="getHistory", tags=["Me"])
async def get_browsing_history(
    current_user: Annotated[users_schema.UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    return await history_crud.get_my_history(db, str(current_user.id))

@router.post("/history/{item_id}", response_model=None, operation_id="postHistory", tags=["Me"])
async def record_browsing_history(
    item_id: UUID,
    current_user: Annotated[users_schema.UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    await history_crud.record_history(db, str(current_user.id), str(item_id))
    return