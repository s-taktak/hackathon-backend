from fastapi import APIRouter, Depends
from api.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from api.cruds.category import get_category

router = APIRouter()

@router.get("/categories",operation_id="getCategories", tags=["category"])
async def get_categories(parent_id: int = None, db: AsyncSession = Depends(get_db)):
    return await get_category(db,parent_id=parent_id)