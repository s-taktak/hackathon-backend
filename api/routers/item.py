from fastapi import APIRouter,Depends, HTTPException,status
from typing import Annotated
import api.schemas.item as item_schema
import api.cruds.item as item_crud
import api.schemas.users as users_schema
from api.routers.auth import get_current_user
import uuid
from uuid import UUID
from datetime import datetime
from api.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/item",response_model=item_schema.ItemResponse)
async def post_item(
    item_body: item_schema.ItemCreate,
    current_user: Annotated[users_schema.UserMeResponse, Depends(get_current_user)],
    db: AsyncSession= Depends(get_db)
    ):
    item = await item_crud.create_item(db,item_body,str(current_user.id))
    return item

@router.put("/item/{item_id}",response_model=item_schema.ItemResponse)
async def update_item(
    item_id: UUID,
    item_body: item_schema.ItemUpdate,
    current_user: Annotated[users_schema.UserMeResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    item = await item_crud.get_item(db, str(item_id))
    
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.seller_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission to update this item"
        )
    updated_item = await item_crud.update_item(db,str(item_id),item_body)
    
    return updated_item

@router.get("/item/{item_id}",response_model=item_schema.ItemResponse)
async def get_item_detail(
    item_id: UUID,
    db: AsyncSession = Depends(get_db)
    ):
    item = await item_crud.get_item(db, str(item_id))
    
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/item/{item_id}",response_model=None)
async def delete_item(
    item_id:UUID,
    db: AsyncSession = Depends(get_db),
    ):
    item = await item_crud.get_item(db, str(item_id))
    
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    await item_crud.delete_item(db, original=item)
    return

@router.post("/item/{item_id}/purchase",response_model=item_schema.ItemResponse)
async def purchase_item(
    item_id: UUID,
    current_user: Annotated[users_schema.UserMeResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    ):
    item = await item_crud.get_item(db, str(item_id))
    
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.status == "sold_out":
        raise HTTPException(status_code=400, detail="Item is already sold out")
    if item.seller_id == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot purchase your own item")
    
    tx_id = uuid.uuid4()
    purchased_item = await item_crud.purchase_item(db, str(item_id),buyer_id=str(current_user.id),tx_id=str(tx_id))
    return purchased_item
