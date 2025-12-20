from fastapi import APIRouter, Depends
from api.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from api.cruds.category import get_category
from .api.utils.function import Tools
from openai import OpenAI
import json

client = OpenAI()
router = APIRouter()

@router.post("/api/ai/chat")
async def chat_with_ai(payload: dict, db: AsyncSession = Depends(get_db)):
    user_message = payload.get("message")
    
    # 1. 最初の問い合わせ
    messages = [
        {"role": "system", "content": "あなたはフリマアプリのアシスタントです。ユーザーの要望に合う商品を検索ツールを使って提案してください。"},
        {"role": "user", "content": user_message}
    ]

    response = client.chat.completions.create(
        model="gpt-4o", # 現在はgpt-4oが主流です
        messages=messages,
        tools=Tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # 2. AIが「ツールを使いたい」と言った場合の処理
    if tool_calls:
        # メッセージ履歴にAIの指示を追加
        messages.append(response_message)

        for tool_call in tool_calls:
            if tool_call.function.name == "search_items":
                # 引数をパース
                args = json.loads(tool_call.function.arguments)
                
                # ★ ここで佐藤さんが作ったベクトル検索ロジックを実行！
                # 前の回答で作った search_by_specs 関数を呼び出すイメージです
                items = await search_by_specs(args, db) 

                # 検索結果を履歴に追加
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "search_items",
                    "content": json.dumps(items) # 商品リストを文字列にして渡す
                })

        # 3. 検索結果を含めて、AIに最終回答を作らせる
        final_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        
        return {
            "reply": final_response.choices[0].message.content,
            "items": items # フロントエンドでカード表示するために商品データも返す
        }

    # ツールを使わなかった場合はそのまま返答
    return {"reply": response_message.content, "items": []}