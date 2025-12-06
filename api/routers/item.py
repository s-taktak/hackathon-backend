from fastapi import APIRouter
import api.schemas.item as item_schema
import uuid
from uuid import UUID
from datetime import datetime

router = APIRouter()

@router.post("/item",response_model=item_schema.ItemResponse)
async def create_item(item_body: item_schema.ItemCreate):
    return item_schema.ItemResponse(id=uuid.uuid1(),seller_id=1,status='on_sale',created_at=datetime.now(),updated_at=datetime.now(),**item_body.dict())

@router.put("/item/{item_id}",response_model=item_schema.ItemResponse)
async def update_item(item_id: UUID,item_body: item_schema.ItemUpdate):
    return item_schema.ItemResponse(id=item_id,**item_body.dict())

@router.get("/item/{item_id}",response_model=item_schema.ItemResponse)
async def get_item_detail(item_id: UUID):
    return item_schema.ItemResponse(id=item_id,seller_id=1,status='on_sale',created_at=datetime.now(),updated_at=datetime.now())

@router.delete("/item/{item_id}",response_model=None)
async def delete_item(item_id:UUID):
    return

@router.post("/item/{item_id}/purchase",response_model=item_schema.ItemResponse)
async def purchase_item(item_id: UUID):
    return item_schema.ItemResponse(id=item_id,name="Purchased Item",price=1000,description="This is a dummy description", seller_id=1,status='sold_out',created_at=datetime.now(),updated_at=datetime.now())
