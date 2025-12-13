from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from api.db import get_db
import api.schemas.item as item_schema
import api.cruds.item as item_crud
import api.core as core

router = APIRouter()

@router.get("/search", response_model=List[item_schema.ItemResponse], tags=["Search"])
async def search_items(
    q: str = Query(..., min_length=1, max_length=100, description="検索キーワード"),
    db: AsyncSession = Depends(get_db)
):
    """
    AIベクトル検索を行うエンドポイント
    """
    # 1. 検索エンジンが準備できているか確認
    if not core.search_engine:
        # 準備できていない場合はエラーではなく空リストを返す（または503エラー）
        print("⚠️ Search engine is not loaded.")
        return []

    # 2. キーワードをベクトルに変換 (Pythonリスト)
    query_vector = core.search_engine.encode_query(q)
    
    if not query_vector:
        return []

    # 3. MySQLからベクトル検索を実行 (CRUD呼び出し)
    # ここで「全件スキャン＆類似度計算」が走ります
    items = await item_crud.search_items_by_vector(db, query_vector, top_k=20)

    return items