from fastapi import APIRouter, Depends
from api.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import api.cruds.category as category_crud
import api.cruds.item as item_crud
from api.utils.function import TOOLS
import api.core as core
from openai import OpenAI
import json

client = OpenAI()
router = APIRouter()

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

@router.post("/aiSearch")
async def aiSearch(
    payload: dict,
    db: AsyncSession = Depends(get_db)
    ):
    messages = payload.get("history", [])
    messages.append({"role": "user", "content": payload.get("message")})
    
    if not any(m["role"] == "system" for m in messages):
        messages.insert(0, {
            "role": "system", 
            "content": "あなたはフリマアプリでお客様の要望を聞き出し、おすすめの商品を出力する。まずfind_category_idで正確なID(depth 1)を特定し、次にそのIDで商品を検索してください。"
        })

    for _ in range(4):  
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS
        )
        response_msg = response.choices[0].message
        
        if not response_msg.tool_calls:
            return {"reply": response_msg.content, "history": messages}

        messages.append(response_msg)

        for tool_call in response_msg.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if func_name == "find_category_id":
                result = await category_crud.search_depth2(db, args["keyword"])
                content = json.dumps(result)

            elif func_name == "search_similar_items":
                items = await item_crud.search(db, **args)
                content = json.dumps(items)

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": func_name,
                "content": content
            })