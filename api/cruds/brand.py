from sqlalchemy import select, case
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
        .order_by(
            case(
                (BrandModel.name.ilike(keyword), 1),  # Exact match
                (BrandModel.name.ilike(f"{keyword}%"), 2),  # Starts with
                else_=3  # Contains
            ),
            BrandModel.name
        )
        .limit(10)
    )
    return result.scalars().all()
