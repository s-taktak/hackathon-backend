from sqlalchemy import select
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
            )
        .filter(ItemModel.seller_id == user_id)
    )
    return result.scalars().all()

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

async def search_items_by_vector(
    db: AsyncSession, 
    query_vector: list[float],
    top_k: int = 20
) -> List[ItemModel]:
    
    # 1. ベクトルテーブルだけを全件取得（軽い！）
    # select(ItemVector.item_id, ItemVector.embedding)
    result = await db.execute(select(ItemVector))
    rows = result.scalars().all()

    if not rows:
        return []

    # 2. 計算 (Pythonメモリ上)
    db_vectors = [row.embedding for row in rows]
    db_ids = [row.item_id for row in rows] # item_idを取り出す

    # [N, 128] の行列にする
    tensor_db = torch.tensor(db_vectors) 
    tensor_query = torch.tensor(query_vector).unsqueeze(0) # [1, 128]

    # 3. コサイン類似度計算 (一括計算なので速い)
    # 正規化されている前提なら内積(matmul)でOK
    # 正規化されていないなら F.cosine_similarity を使う
    scores = torch.matmul(tensor_query, tensor_db.T).squeeze(0)

    # 4. 上位K件を取得
    # スコアが高い順にインデックスを取得
    top_k = min(top_k, len(db_ids))
    top_scores, top_indices = torch.topk(scores, k=top_k)

    # 3. ヒットしたIDの商品情報を取得
    target_ids = [db_ids[i] for i in top_indices.cpu().numpy()]
    
    items = await get_item(db, target_ids)
    # 7. ★重要: 検索スコア順(target_idsの順)に並べ直す
    # DBからの取得順は保証されないため、Python側で並べ替えが必要
    item_map = {item.id: item for item in items}
    sorted_items = []
    for tid in target_ids:
        if tid in item_map:
            sorted_items.append(item_map[tid])
            
    return sorted_items

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