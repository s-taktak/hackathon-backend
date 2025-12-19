from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from api.models import Category as CategoryModel

async def get_category(
    db: AsyncSession, 
    parent_id: int =None
) -> List[CategoryModel]:
    result = await db.execute(
        select(CategoryModel)
        .filter(CategoryModel.parent_id==parent_id)
    )
    return result.scalars().all()