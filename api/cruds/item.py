from sqlalchemy import select,desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List
from api.models.item import Item as ItemModel
from api.models.transaction import Transaction as TransactionModel
from api.models.category import Category as CategoryModel
from api.schemas.item import ItemCreate
from api.schemas.item import ItemResponse
from api.schemas.item import ItemUpdate
from api.models.item_image import ItemImage
import api.core as core
from api.models.embedding import ItemVector
import torch
from uuid import UUID
import uuid
from datetime import datetime

async def get_items_list(db: AsyncSession, skip:int, limit: int):
    result = await db.execute(
        select(ItemModel)
        .options(
            selectinload(ItemModel.seller),
            selectinload(ItemModel.category),
            selectinload(ItemModel.brand),       # ブランド情報
            selectinload(ItemModel.condition),
            selectinload(ItemModel.images),
            )
        .order_by(desc(ItemModel.updated_at))
        )
    
    return result.scalars().all()


async def get_item(db: AsyncSession, item_id: str) -> ItemModel | None:
    result = await db.execute(
        select(ItemModel)
        .options(
            selectinload(ItemModel.seller),
            selectinload(ItemModel.category),
            selectinload(ItemModel.brand),       # ブランド情報
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
            # 必要なリレーションを全部読み込む
            selectinload(ItemModel.seller),
            selectinload(ItemModel.category),
            selectinload(ItemModel.brand),
            selectinload(ItemModel.condition),
            selectinload(ItemModel.images),
        )
        .filter(ItemModel.id.in_(item_ids)) # ★重要: IN句を使う
        .order_by(desc(ItemModel.updated_at))
    )
    return result.scalars().all()

async def get_items_by_user_id(db: AsyncSession, user_id: str) -> List[ItemModel]:
    result = await db.execute(
        select(ItemModel)
        .options(
            selectinload(ItemModel.seller),
            selectinload(ItemModel.category),
            selectinload(ItemModel.brand),       # ブランド情報
            selectinload(ItemModel.condition),
            selectinload(ItemModel.images),
            )
        .filter(ItemModel.seller_id == user_id)
        .order_by(desc(ItemModel.updated_at))
    )
    return result.scalars().all()

async def get_items_by_ids(db: AsyncSession, item_ids: List[str]):
    """IDリストから商品詳細情報を取得し、元のID順に並べて返す"""
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
        .filter(ItemModel.id.in_(item_ids))
    )
    items = result.scalars().all()
    
    # DB取得順はバラバラなので、指定されたID順に並べ直す
    items_map = {item.id: item for item in items}
    sorted_items = [items_map[id] for id in item_ids if id in items_map]
    
    return sorted_items

async def delete_item(db: AsyncSession, original: ItemModel) -> None:
    await db.delete(original)
    await db.commit()
    return

async def create_item(
        db: AsyncSession, item_create:ItemCreate,user_id: UUID
) -> ItemModel:
    print("\n" + "="*30)
    print("🚀 create_item started")
    
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

    embedding_list = None
    if core.search_engine is None:
        print("❌ ERROR: core.search_engine is None! (main.pyのlifespanが動いていないか、初期化に失敗しています)")
    else:
        print("✅ core.search_engine is alive.")
        # チェック2: モデルはロードされているか？
        if core.search_engine.model is None:
            print("❌ ERROR: search_engine.model is None! (モデルファイルの読み込みに失敗しています)")
        else:
            print("✅ search_engine.model is loaded.")
            print(f"🔄 Encoding item: {item_create.title}")
    try:
        # 必要な情報を辞書化
        item_dict = {
            "title": item_create.title,
            "price": item_create.price,
            "brand_id": item_create.brand_id,
            "category_id": item_create.category_id,
            "condition_id": item_create.condition_id
        }
        # search_engine.encode_item(item_dict) のような関数を searcher.py に作っておく
        # 戻り値は Pythonの list である必要があります (例: [0.123, 0.456, ...])
        embedding_list = core.search_engine.encode_single_item(item_dict)
                
                # チェック3: 結果は空じゃないか？
        if not embedding_list:
            print("⚠️ Warning: encode_single_item returned empty list []")
        else:
            print(f"✅ Vector generated! Size: {len(embedding_list)}")
    except Exception as e:
        print(f"⚠️ Vector encoding failed: {e}")

    if embedding_list:
        new_vector = ItemVector(
            item_id=new_uuid,  # 同じIDを使う
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
    item = await get_item(db, item_id)
    if item is None:
        return None

    update_data = item_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(item, key, value)

    item.updated_at = datetime.now()

    db.add(item)
    await db.commit()
    await db.refresh(item)

    return await get_item(db, item_id)

# api/cruds/item.py

async def get_all_vectors(db: AsyncSession):
    """全商品のベクトルを取得する（計算はしない）"""
    result = await db.execute(select(ItemVector))
    return result.scalars().all()


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
        buyer_id=buyer_id,          # 引数で受け取った「買った人」
        seller_id=item.seller_id,   # 商品情報にある「売った人」
        transaction_price=item.price, # 今の価格を記録
        created_at=datetime.now()
    )

    db.add(item)
    db.add(transaction)

    await db.commit()
    await db.refresh(item)

    return await get_item(db, item_id)