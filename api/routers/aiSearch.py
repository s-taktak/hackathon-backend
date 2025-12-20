from fastapi import APIRouter, Depends
from api.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import api.cruds.category as category_crud
import api.cruds.item as item_crud
from api.utils.function import TOOLS
from api.schemas.chat import AiSearchRequest,ChatMessage,AiSearchResponse
import api.core as core
from openai import OpenAI
import json

client = OpenAI()
router = APIRouter()

SYSTEM_PROMPT = """
あなたはフリマアプリのプロ。
【重要】カテゴリーデータはすべて「英語」で管理されています。
1. ユーザーの要望を聞いたら、キーワードを英語に翻訳してください（例：「パソコン」→「Laptop」や「PC」）。
2. find_category_id を呼び出す際は、その英語キーワードを使って ID (depth 1) を特定してください。
3. 特定した ID を使って商品を検索してください。
"""

async def search_similar_items(
    db: AsyncSession,
    category_id: int,
    name: str,
    price: float,
    condition_id: int = 1
):
    
    item_data = {
        "name": name,
        "price": price,
        "category_id": category_id,
        "brand_id": 0,
        "condition_id": condition_id
    }

    target_vectors = await item_crud.get_all_vectors(db)
    
    if not target_vectors:
        return []

    query_vector = await core.search_engine.encode_single_item(item_data)

    top_item_ids = core.search_engine.sort_by_similarity(
        query_vector, 
        target_vectors, 
        top_k=3
    )
    return await item_crud.get_items_by_ids(db, top_item_ids)

@router.post("/aiSearch", response_model=AiSearchResponse, tags=["aiSearch"])
async def ai_search_endpoint(payload: AiSearchRequest, db: AsyncSession = Depends(get_db)):
    
    messages = [m.model_dump(exclude_none=True) for m in payload.history]
    
    messages.append({"role": "user", "content": payload.message})

    
    if not any(m["role"] == "system" for m in messages):
        messages.insert(0, {
            "role": "system", 
            "content": SYSTEM_PROMPT
        })

    recommended_items = []

    for _ in range(4):  
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS
        )
        response_msg = response.choices[0].message
        
        if not response_msg.tool_calls:
            final_reply = response_msg.content
            break

        messages.append(response_msg)

        for tool_call in response_msg.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if func_name == "find_category_id":
                result = await category_crud.find_category_id(db, args["keyword"])
                content = json.dumps(result)

            elif func_name == "search_similar_items":
                recommended_items = await search_similar_items(db, args)
                content = json.dumps([{"id": i.id, "title": i.title} for i in recommended_items])

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": func_name,
                "content": content
            })
    else:
        final_reply = "条件に合う商品を検索しました。"

    return AiSearchResponse(
        reply=final_reply,
        history=messages, 
        items=recommended_items
    )