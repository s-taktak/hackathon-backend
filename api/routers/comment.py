from fastapi import APIRouter, Depends, HTTPException, status
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

@router.post("/item/{item_id}/comments", response_model=comment_schema.CommentResponse, operation_id="postComment", tags=["Comment"])
async def post_comment(
    item_id: UUID,
    comment_body: comment_schema.CommentCreate,
    current_user: Annotated[users_schema.UserMeResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    new_comment = await comment_crud.create_comment(db, comment_body, str(item_id), str(current_user.id))

    return comment_schema.CommentResponse(
        id=new_comment.id,
        item_id=new_comment.item_id,
        content=new_comment.content,
        username=current_user.username,
        isSeller=False,
        created_at=new_comment.created_at
    )

@router.get("/item/{item_id}/comments", response_model=List[comment_schema.CommentResponse], operation_id="getComment", tags=["Comment"])
async def get_comments(
    item_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    comments_data = await comment_crud.get_comments_by_item_id(db, str(item_id))

    response_list = []
    for comment in comments_data:
        user_name = comment.user.username if comment.user else "Unknown"
        is_seller = False
        if comment.item and comment.user_id == comment.item.user_id:
            is_seller = True

        response_obj = comment_schema.CommentResponse(
            id=comment.id,
            item_id=comment.item_id,
            content=comment.content,
            username=user_name,
            isSeller=is_seller,
            created_at=comment.created_at
        )
        response_list.append(response_obj)

    return response_list