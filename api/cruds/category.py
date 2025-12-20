from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
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

async def find_category_id(
        db: AsyncSession,
        keyword: str,
)-> List[CategoryModel]:
    result = await db.execute(
        select(CategoryModel)
        .where(
            CategoryModel.name.ilike(f"%{keyword}%"),
            CategoryModel.depth==1
        )
        .options(
            selectinload(CategoryModel.parent)
        )
        .limit(10)
    )
    categories = result.scalars().all()

    output = []
    for cat in categories:
        if cat.parent:
            path = f"{cat.parent.name} > {cat.name}"
        else:
            path = f"{cat.name}"
        output.append({"id": cat.id, "path": path})
        
    return output
