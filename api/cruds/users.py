from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.users import User as UserModel
from api.schemas.users import UserCreate
from api.schemas.users import UserMeResponse
import uuid
from uuid import UUID
from datetime import datetime

async def get_user_by_email(db: AsyncSession,email:str) -> UserModel |None:
    result = await db.execute(select(UserModel).filter(UserModel.email == email))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: UUID) -> UserModel | None:
    result = await db.execute(select(UserModel).filter(UserModel.id == str(user_id)))
    return result.scalars().first()

async def create_user(
        db: AsyncSession, user_create:UserCreate,hashed_password
) -> UserModel:
    new_uuid = str(uuid.uuid4())
    current_time = datetime.now()

    user = UserModel(
        id=new_uuid,
        email=user_create.email,
        username=user_create.username,
        hashed_password=hashed_password,
        gender=user_create.gender.value if user_create.gender else "undefined",
        birth_date=user_create.birth_date,
        created_at=current_time
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user