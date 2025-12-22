from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from api.db import get_db
import api.schemas.item as item_schema
import api.cruds.item as item_crud
import api.core as core
from uuid import UUID
import json

router = APIRouter()

@router.get("/recommend", response_model=List[item_schema.ItemResponse],operation_id="recommend", tags=["recommend"])
async def recommend_items(
    item_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    if not core.search_engine:
        return []

    item_vector = await item_crud.get_vector_by_id(db, str(item_id))
    
    if not item_vector:
        return []

    all_vectors = await item_crud.get_all_vectors(db)
    
    embedding = item_vector.embedding
    if isinstance(embedding, str):
        embedding = json.loads(embedding)
        
    top_item_ids = core.search_engine.sort_by_similarity(embedding, all_vectors,top_k=4)
    if not top_item_ids:
        return []

    items = await item_crud.get_items_by_ids(db, top_item_ids[1:])

    return items