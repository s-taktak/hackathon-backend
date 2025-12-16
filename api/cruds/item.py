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
    VECTOR_FIELDS = [
    "title", 
    "description", 
    "price", 
    "category_id", 
    "brand_id", 
    "condition_id"
]
    item = await get_item(db, item_id)
    if item is None:
        return None

    update_data = item_update.model_dump(exclude_unset=True)

    item_was_modified = False
    
    # 変更フラグをチェックするためのセット
    vector_fields_modified = False

    for key, value in update_data.items():
        # ベクトル生成に関わるフィールドが変更されたかチェック
        if key in VECTOR_FIELDS and getattr(item, key) != value:
            vector_fields_modified = True
            
        # モデルの属性を更新
        setattr(item, key, value)

    item.updated_at = datetime.now()
    
    # --- ★ベクトル更新ロジックの追加★ ---
    if vector_fields_modified and core.search_engine:
        print(f"🔄 Vector update triggered for item ID: {item_id}")
        
        # 1. 新しいベクトル生成に必要な情報を準備
        item_dict = {
            "title": item.title,
            "price": item.price,
            "brand_id": item.brand_id,
            "category_id": item.category_id,
            "condition_id": item.condition_id
        }
        
        try:
            # 2. ベクトルを再生成
            new_embedding_list = core.search_engine.encode_single_item(item_dict)
            
            if new_embedding_list:
                print("✅ New vector generated. Updating DB.")
                
                # 3. 既存の ItemVector レコードを取得・更新（または新規作成）
                # ItemModel.vector リレーションシップが定義されている前提
                # ItemVectorテーブルからitem_idで検索
                existing_vector = await db.execute(
                    select(ItemVector).filter(ItemVector.item_id == item_id)
                )
                current_vector = existing_vector.scalars().first()
                
                if current_vector:
                    # 更新
                    current_vector.embedding = new_embedding_list
                    db.add(current_vector)
                else:
                    # 万が一、ベクトルが登録されていなかった場合（新規作成）
                    new_vector = ItemVector(
                        item_id=item_id, 
                        embedding=new_embedding_list
                    )
                    db.add(new_vector)
            else:
                 print("⚠️ New vector generation failed (empty list returned). Skipping vector update.")

        except Exception as e:
            print(f"❌ Vector re-encoding failed during update: {e}")
            # ベクトル更新に失敗しても、アイテム自体の更新は続ける

    # --- DBへの書き込み ---
    db.add(item)
    await db.commit()
    await db.refresh(item)

    # selectinload 付きで再取得
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