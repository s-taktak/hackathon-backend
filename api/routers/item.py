import os
from fastapi import APIRouter,Depends, HTTPException,status,File, UploadFile, Form
from typing import Annotated,List
import api.schemas.item as item_schema
import api.cruds.item as item_crud
import api.schemas.users as users_schema
from api.routers.auth import get_current_user
import uuid
from uuid import UUID
from datetime import datetime
from api.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from google.cloud import storage

BUCKET_NAME = "uttc-image"

router = APIRouter()

@router.post("/item",response_model=item_schema.ItemResponse,operation_id="postItem", tags=["Item"])
async def post_item(
    item_body: item_schema.ItemCreate,
    current_user: Annotated[users_schema.UserMeResponse, Depends(get_current_user)],
    files: List[UploadFile] = File(default=[]),
    db: AsyncSession= Depends(get_db)
    ):
    image_urls = []
    
    if files:
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(BUCKET_NAME)

            for file in files:
                extension = os.path.splitext(file.filename)[1]
                filename = f"{uuid.uuid4()}{extension}"
                blob = bucket.blob(filename)
                
                # アップロード
                blob.upload_from_file(file.file, content_type=file.content_type)
                
                # URLをリストに追加
                url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
                image_urls.append(url)
                
        except Exception as e:
            print(f"GCS Upload Error: {e}")
            raise HTTPException(status_code=500, detail="画像のアップロードに失敗しました")

    item = await item_crud.create_item(db,item_body,str(current_user.id),image_urls=image_urls)
    return item

@router.put("/item/{item_id}",response_model=item_schema.ItemResponse,operation_id="updateItem", tags=["Item"])
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

@router.get("/item",response_model=List[item_schema.ItemResponse],operation_id="getItemsList", tags=["Item"])
async def get_items_list(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
    ):
    item = await item_crud.get_items_list(db,skip,limit)
    
    return item

@router.get("/item/{item_id}",response_model=item_schema.ItemResponse,operation_id="getItemDetail", tags=["Item"])
async def get_item_detail(
    item_id: UUID,
    db: AsyncSession = Depends(get_db)
    ):
    item = await item_crud.get_item(db, str(item_id))
    
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/item/{item_id}",response_model=None,operation_id="deleteItem", tags=["Item"])
async def delete_item(
    item_id:UUID,
    db: AsyncSession = Depends(get_db),
    ):
    item = await item_crud.get_item(db, str(item_id))
    
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    await item_crud.delete_item(db, original=item)
    return

@router.post("/item/{item_id}/purchase",response_model=item_schema.ItemResponse,operation_id="purchaseItem", tags=["Item"])
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
