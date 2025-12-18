from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from api.db import get_db
import api.schemas.item as item_schema
import api.cruds.item as item_crud
import api.core as core
from uuid import UUID

router = APIRouter()

@router.get("/recommend", response_model=List[item_schema.ItemResponse],operation_id="recommend", tags=["recommend"])
async def recommend_items(
    item_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    if not core.search_engine:
        # 準備できていない場合はエラーではなく空リストを返す（または503エラー）
        print("⚠️ Search engine is not loaded.")
        return []

    item_vector = await item_crud.get_vector_by_id(db,str(item_id))

    # 3. MySQLからベクトル検索を実行 (CRUD呼び出し)
    # ここで「全件スキャン＆類似度計算」が走ります
    all_vectors = await item_crud.get_all_vectors(db)
    top_item_ids = core.search_engine.sort_by_similarity(item_vector.embedding, all_vectors)
    if not top_item_ids:
        return []

    items = await item_crud.get_items_by_ids(db, top_item_ids[1:],top_k=3)

    return items