from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from api.models.brand import Brand as BrandModel

async def find_brands(
    db: AsyncSession,
    keyword: str
) -> List[BrandModel]:
    result = await db.execute(
        select(BrandModel)
        .where(BrandModel.name.ilike(f"%{keyword}%"))
        .limit(10)
    )
    return result.scalars().all()
