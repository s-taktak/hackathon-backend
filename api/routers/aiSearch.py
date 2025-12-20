from fastapi import APIRouter, Depends
from api.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from api.cruds.category import get_category
from .api.utils.function import TOOLS
from openai import OpenAI
import json

client = OpenAI()
router = APIRouter()

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

    for _ in range(3):  # 最大3回までツール呼び出しを許可
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS
        )
        response_msg = response.choices[0].message
        
        # ツール呼び出しがない場合は、最終的な返答として終了
        if not response_msg.tool_calls:
            return {"reply": response_msg.content, "history": messages}

        # AIの指示を履歴に追加
        messages.append(response_msg)

        # ツール呼び出しの処理
        for tool_call in response_msg.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if func_name == "find_category_id":
                # カテゴリーDBからdepth 2を検索 
                result = await category_crud.search_depth2(db, args["keyword"])
                content = json.dumps(result)

            elif func_name == "search_similar_items":
                # TwoTowerModelを使用したベクトル検索 
                items = await recommendation_service.search(db, **args)
                content = json.dumps(items)

            # 実行結果を履歴に追加してAIに返す
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": func_name,
                "content": content
            })