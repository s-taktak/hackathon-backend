from fastapi import APIRouter, Depends
from api.db import get_db
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from api.cruds.category import get_category,find_category_id
import api.schemas.item as category_schema

router = APIRouter()

@router.get("/categories",response_model=List[category_schema.Category],operation_id="getCategories", tags=["category"])
async def get_categories(parent_id: int = None, db: AsyncSession = Depends(get_db)):
    return await get_category(db,parent_id=parent_id)

@router.get("/categories/search",response_model=List[category_schema.CategorySearchResponse],operation_id="searchCategories", tags=["category"])
async def search_categories(keyword: str, db: AsyncSession = Depends(get_db)):
    return await find_category_id(db,keyword=keyword)