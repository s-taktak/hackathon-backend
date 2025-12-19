from fastapi import APIRouter, Depends
from api.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from api.cruds.category import get_category

router = APIRouter()

@router.get("/categories", tag=["category"])
def get_categories(parent_id: int = None, db: AsyncSession = Depends(get_db)):
    return get_category(parent_id=parent_id)