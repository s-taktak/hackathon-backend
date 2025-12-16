from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import api.schemas.users as users_schema
import api.schemas.item as item_schema
import api.cruds.users as user_crud 
import api.cruds.item as item_crud
from api.db import get_db
import uuid
from uuid import UUID
from datetime import datetime

router = APIRouter()

@router.get("/users/{user_id}",response_model=users_schema.UserResponse,operation_id="getProfile", tags=["User"])
async def get_user_profile(
    user_id:UUID,
    db: AsyncSession = Depends(get_db)
    ):
    user = await user_crud.get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("/users/{user_id}/items",response_model=List[item_schema.ItemResponse],operation_id="getListing", tags=["User"])
async def get_users_listings(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
    ):
    items = await item_crud.get_items_by_user_id(db, str(user_id))
    return items
