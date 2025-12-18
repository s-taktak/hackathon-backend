from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from api.models.history import History as HistoryModel
import uuid
from datetime import datetime
from typing import List

async def record_history(db: AsyncSession, user_id: str, item_id: str) -> None:
    result = await db.execute(
        select(HistoryModel)
        .filter(HistoryModel.user_id == user_id, HistoryModel.item_id == item_id)
    )
    history = result.scalars().first()

    current_time = datetime.now()

    if history:
        history.viewed_at = current_time
    else:
        new_id = str(uuid.uuid4())
        history = HistoryModel(
            id=new_id,
            user_id=user_id,
            item_id=item_id,
            viewed_at=current_time
        )
        db.add(history)
    
    await db.commit()
    return

async def get_my_history(db: AsyncSession, user_id: str) -> List[HistoryModel]:
    result = await db.execute(
        select(HistoryModel)
        .options(selectinload(HistoryModel.item))
        .filter(HistoryModel.user_id == user_id)
        .order_by(HistoryModel.viewed_at.desc()) 
        .limit(30)
    )
    return result.scalars().all()