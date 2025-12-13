from fastapi import APIRouter,Depends,HTTPException, status
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from api.models.comment import Comment as CommentModel
import api.schemas.comment as comment_schema
import api.schemas.users as users_schema
import api.cruds.comment as comment_crud
from api.routers.auth import get_current_user
import uuid
from uuid import UUID
from datetime import datetime
from typing import List
from api.db import get_db

router = APIRouter()

@router.post("/item/{item_id}/comments",response_model=comment_schema.CommentResponse)
async def post_comment(
    item_id:UUID,
    comment_body:comment_schema.CommentCreate,
    current_user: Annotated[users_schema.UserMeResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    ):
    return await comment_crud.create_comment(db, comment_body, str(item_id), str(current_user.id))

@router.delete("/comments/{comment_id}", response_model=None)
async def delete_comment(
    comment_id: UUID,
    current_user: Annotated[users_schema.UserMeResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    # 1. 消したいコメントをDBから探す
    comment = await comment_crud.get_comment_by_id(db, str(comment_id))
    
    # 2. コメントが存在しない場合
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # 3. 権限チェック：他人のコメントは消せないようにする！
    # (発展: 商品の出品者(seller)も消せるようにするとより親切です)
    if comment.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You can only delete your own comments"
        )

    # 4. 削除実行
    await comment_crud.delete_comment(db, original=comment)
    return

@router.get("/item/{item_id}/comments", response_model=List[comment_schema.CommentResponse])
async def get_comments(
    item_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # UUIDを文字列にしてCRUDに渡す
    return await comment_crud.get_comments_by_item_id(db, str(item_id))