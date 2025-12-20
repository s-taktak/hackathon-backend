from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List
from api.models.item import Item as ItemModel
from api.models.transaction import Transaction as TransactionModel
from api.models.category import Category as CategoryModel
from api.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from api.models.item_image import ItemImage
import api.core as core
from api.models.embedding import ItemVector
from uuid import UUID
import uuid
from datetime import datetime

async def get_items_list(db: AsyncSession, skip: int, limit: int):
    result = await db.execute(
        select(ItemModel)
        .options(
            selectinload(ItemModel.seller),
            selectinload(ItemModel.category),
            selectinload(ItemModel.brand),
            selectinload(ItemModel.condition),
            selectinload(ItemModel.images),
        )
        .filter(ItemModel.status == "on_sale")
        .order_by(desc(ItemModel.updated_at))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_item(db: AsyncSession, item_id: str) -> ItemModel | None:
    result = await db.execute(
        select(ItemModel)
        .options(
            selectinload(ItemModel.seller),
            selectinload(ItemModel.category),
            selectinload(ItemModel.brand),
            selectinload(ItemModel.condition),
            selectinload(ItemModel.images),
        )
        .filter(ItemModel.id == item_id)
    )
    return result.scalars().first()

async def get_items_by_ids(db: AsyncSession, item_ids: List[str]) -> List[ItemModel]:
    if not item_ids:
        return []

    result = await db.execute(
        select(ItemModel)
        .options(
            selectinload(ItemModel.seller),
            selectinload(ItemModel.category),
            selectinload(ItemModel.brand),
            selectinload(ItemModel.condition),
            selectinload(ItemModel.images)
        )
        .filter(ItemModel.status == "on_sale")
        .filter(ItemModel.id.in_(item_ids))
    )
    items = result.scalars().all()
    
    items_map = {item.id: item for item in items}
    sorted_items = [items_map[id] for id in item_ids if id in items_map]
    
    return sorted_items

async def get_items_by_user_id(db: AsyncSession, user_id: str) -> List[ItemModel]:
    result = await db.execute(
        select(ItemModel)
        .options(
            selectinload(ItemModel.seller),
            selectinload(ItemModel.category),
            selectinload(ItemModel.brand),
            selectinload(ItemModel.condition),
            selectinload(ItemModel.images),
        )
        .filter(ItemModel.seller_id == user_id)
        .order_by(desc(ItemModel.updated_at))
    )
    return result.scalars().all()

async def delete_item(db: AsyncSession, original: ItemModel) -> None:
    await db.delete(original)
    await db.commit()
    return

async def create_item(
        db: AsyncSession, item_create: ItemCreate, user_id: UUID, image_urls: List[str]
) -> ItemModel:
    new_uuid = str(uuid.uuid4())
    current_time = datetime.now()

    item = ItemModel(
        id=new_uuid,
        seller_id=user_id,
        title=item_create.title,
        price=item_create.price,
        description=item_create.description,
        category_id=item_create.category_id,
        brand_id=item_create.brand_id,
        condition_id=item_create.condition_id,
        status="on_sale",
        created_at=current_time,
        updated_at=current_time
    )

    for url in image_urls:
        new_image = ItemImage(
            id=str(uuid.uuid4()),
            item_id=new_uuid,
            image_url=url,
            created_at=current_time
        )
        db.add(new_image)

    embedding_list = None
    if core.search_engine and core.search_engine.model:
        try:
            item_dict = {
                "title": item_create.title,
                "price": item_create.price,
                "brand_id": item_create.brand_id,
                "category_id": item_create.category_id,
                "condition_id": item_create.condition_id
            }
            embedding_list = await core.search_engine.encode_single_item(item_dict)
        except Exception as e:
            print(f"❌ ERROR in create_item (encoding): {e}")

    if embedding_list:
        new_vector = ItemVector(
            item_id=new_uuid,
            embedding=embedding_list
        )
        db.add(new_vector)
    
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return await get_item(db, new_uuid)

async def update_item(
    db: AsyncSession, item_id: str, item_update: ItemUpdate
) -> ItemModel | None:
    VECTOR_FIELDS = ["title", "description", "price", "category_id", "brand_id", "condition_id"]
    item = await get_item(db, item_id)
    if item is None:
        return None

    update_data = item_update.model_dump(exclude_unset=True)
    vector_fields_modified = False

    for key, value in update_data.items():
        if key in VECTOR_FIELDS and getattr(item, key) != value:
            vector_fields_modified = True
        setattr(item, key, value)

    item.updated_at = datetime.now()
    
    if vector_fields_modified and core.search_engine:
        try:
            item_dict = {
                "title": item.title,
                "price": item.price,
                "brand_id": item.brand_id,
                "category_id": item.category_id,
                "condition_id": item.condition_id
            }
            new_embedding_list = core.search_engine.encode_single_item(item_dict)
            
            if new_embedding_list:
                existing_vector = await db.execute(
                    select(ItemVector).filter(ItemVector.item_id == item_id)
                )
                current_vector = existing_vector.scalars().first()
                
                if current_vector:
                    current_vector.embedding = new_embedding_list
                    db.add(current_vector)
                else:
                    new_vector = ItemVector(
                        item_id=item_id, 
                        embedding=new_embedding_list
                    )
                    db.add(new_vector)
        except Exception:
            pass

    db.add(item)
    await db.commit()
    await db.refresh(item)
    return await get_item(db, item_id)

async def get_purchased_items_by_user(db: AsyncSession, user_id: str) -> List[ItemModel]:
    result = await db.execute(
        select(ItemModel)
        .join(TransactionModel, ItemModel.id == TransactionModel.item_id)
        .filter(TransactionModel.buyer_id == user_id)
        .options(
            selectinload(ItemModel.seller),
            selectinload(ItemModel.category),
            selectinload(ItemModel.brand),
            selectinload(ItemModel.condition),
            selectinload(ItemModel.images),
        )
        .order_by(desc(TransactionModel.created_at)) 
    )
    return result.scalars().all()

async def get_all_vectors(db: AsyncSession):
    result = await db.execute(select(ItemVector))
    return result.scalars().all()

async def get_vector_by_id(db: AsyncSession, item_id: str):
    result = await db.execute(
        select(ItemVector)
        .filter(ItemVector.item_id == item_id)
    )
    return result.scalars().first()

async def purchase_item(
    db: AsyncSession, 
    item_id: str,
    buyer_id: str,
    tx_id: str,
) -> ItemModel | None:
    item = await get_item(db, item_id)
    if item is None:
        return None

    item.status = "sold_out"
    item.updated_at = datetime.now()

    transaction = TransactionModel(
        id=tx_id,
        item_id=item.id,
        buyer_id=buyer_id,
        seller_id=item.seller_id,
        transaction_price=item.price,
        created_at=datetime.now()
    )

    db.add(item)
    db.add(transaction)
    await db.commit()
    await db.refresh(item)
    return await get_item(db, item_id)