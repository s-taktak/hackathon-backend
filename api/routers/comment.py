from fastapi import APIRouter
import api.schemas.comment as comment_schema
import uuid
from uuid import UUID
from datetime import datetime

router = APIRouter()

@router.post("/item/{item_id}/comments",response_model=comment_schema.CommentResponse)
async def post_comment(item_id:UUID,comment_body:comment_schema.CommentCreate):
    return comment_schema.CommentResponse(comment_id=uuid.uuid1(),item_id=item_id,user_id=uuid.uuid1(),created_at=datetime.now(),**comment_body.dict())

@router.delete("/item/{item_id}/comments",response_model=None)
async def delete_comment(comment_id:UUID):
    return 