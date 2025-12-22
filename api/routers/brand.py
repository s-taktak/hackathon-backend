from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from api.db import get_db
from api.cruds.brand import find_brands
from api.schemas.brand import Brand

router = APIRouter()

@router.get("/brands/search", response_model=List[Brand], operation_id="searchBrands", tags=["brand"])
async def search_brands(keyword: str, db: AsyncSession = Depends(get_db)):
    return await find_brands(db, keyword=keyword)
