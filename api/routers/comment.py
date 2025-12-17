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

@router.post("/item/{item_id}/comments", response_model=comment_schema.CommentResponse, operation_id="postComment", tags=["Comment"])
async def post_comment(
    item_id: UUID,
    comment_body: comment_schema.CommentCreate,
    current_user: Annotated[users_schema.UserMeResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    # 1. DBに保存して、作成されたコメント(ORM)を受け取る
    new_comment = await comment_crud.create_comment(db, comment_body, str(item_id), str(current_user.id))

    # 2. ここでスキーマの形に詰め直す
    # (作成直後なので isSeller の判定は current_user.id と item_id から推測するか、別途Itemを引く必要がありますが、
    #  とりあえず投稿者は current_user なので username はすぐわかります)
    
    # ※ 厳密に isSeller を判定するには Item 情報が必要ですが、
    # 簡易的に「投稿直後のレスポンス」を作るなら以下のようにマッピングします
    
    return comment_schema.CommentResponse(
        id=new_comment.id,
        item_id=new_comment.item_id,
        content=new_comment.content,
        username=current_user.username,  # ログイン中のユーザー名を使用
        isSeller=False, # 作成直後は一旦Falseか、必要ならDBからItemを引いて判定
        created_at=new_comment.created_at
    )


@router.get("/item/{item_id}/comments", response_model=List[comment_schema.CommentResponse],operation_id="getComment", tags=["Comment"])
async def get_comments(
    item_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # 1. DBからコメントを取得（user と item の情報を一緒に取得するようCRUD側で調整が必要）
    # CRUD関数内で options(selectinload(CommentModel.user), selectinload(CommentModel.item)) している前提
    comments_data = await comment_crud.get_comments_by_item_id(db, str(item_id))

    # 2. 取得したデータを CommentResponse の形に変換する
    response_list = []
    for comment in comments_data:
        # ユーザー名を取得（リレーションが空の場合は "Unknown" とする安全策）
        user_name = comment.user.username if comment.user else "Unknown"
        
        # 出品者かどうか判定（itemリレーションがロードされている必要あり）
        # アイテムの出品者ID と コメントした人のID が一致するか確認
        is_seller = False
        if comment.item and comment.user_id == comment.item.user_id:
            is_seller = True

        # スキーマに詰め込む
        response_obj = comment_schema.CommentResponse(
            id=comment.id,
            item_id=comment.item_id,
            content=comment.content,
            username=user_name,     # ここで平坦化 (user.username -> username)
            isSeller=is_seller,     # ここで計算結果を入れる
            created_at=comment.created_at
        )
        response_list.append(response_obj)

    return response_list