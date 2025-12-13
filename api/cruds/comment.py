from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from api.models.comment import Comment as CommentModel
from api.schemas.comment import CommentCreate
import uuid
from datetime import datetime
from typing import List

async def create_comment(
    db: AsyncSession, 
    comment_create: CommentCreate,
    item_id: str,
    user_id: str
) -> CommentModel:
    new_id = str(uuid.uuid4())
    current_time = datetime.now()
    
    comment = CommentModel(
        id=new_id,
        content=comment_create.content,
        item_id=item_id,
        user_id=user_id,
        created_at=current_time
    )
    
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    return await get_comment_by_id(db, new_id)

async def get_comments_by_item_id(db: AsyncSession, item_id: str) -> List[CommentModel]:
    result = await db.execute(
        select(CommentModel)
        .options(selectinload(CommentModel.user)) # ユーザー情報も一緒に！
        .filter(CommentModel.item_id == item_id)
        .order_by(CommentModel.created_at) # 古い順
    )
    return result.scalars().all()

async def get_comment_by_id(db: AsyncSession, comment_id: str) -> CommentModel | None:
    result = await db.execute(
        select(CommentModel)
        .options(selectinload(CommentModel.user))
        .filter(CommentModel.id == comment_id)
    )
    return result.scalars().first()

async def delete_comment(db: AsyncSession, original: CommentModel) -> None:
    await db.delete(original)
    await db.commit()
    return