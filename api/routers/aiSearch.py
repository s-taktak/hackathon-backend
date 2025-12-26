from fastapi import APIRouter, Depends
from api.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import api.cruds.category as category_crud
import api.cruds.item as item_crud
import api.cruds.brand as brand_crud
from api.utils.function import TOOLS
from api.schemas.chat import AiSearchRequest,ChatMessage,AiSearchResponse
from api.schemas.predict import PredictRequest, PredictResponse
import api.core as core
from openai import OpenAI
import json

client = OpenAI()
router = APIRouter()

SYSTEM_PROMPT = """
あなたはフリマアプリの専門家です。
1. ユーザーの要望から「商品名」「予算」「状態」を読み取ってください。
2. カテゴリー特定（find_category_id）のコツ：
   - ユーザーが「MacBook」と言ったら「Laptop」や「Computer」のように、
     具体的な商品名を「一般的な英語のカテゴリー名」に変換して検索してください。
   - 必ず英語のキーワードを使用してください。
3. ブランド特定（find_brand_id）のコツ：
   - 商品名からブランド名が分かる場合、そのブランド名（英語）で検索してください。
4. 商品検索（search_similar_items）を行う際：
   - 価格(price)が「〜円くらい」と言われたらその数値を指定してください。
   - 状態(condition)が「新品」なら 1、「中古」や「気にしない」なら 3 程度を割り当ててください。
   - 明確な指定がないパラメータは、デフォルト値（price=0, condition_id=1）を使用してください。
"""

async def search_similar_items(
    db: AsyncSession,
    category_id: int,
    name: str,
    price: float =0.0,
    condition_id: int = 1
):
    
    item_data = {
        "title": name,
        "price": price,
        "category_id": category_id,
        "brand_id": 0,
        "condition_id": condition_id
    }

    target_vectors = await item_crud.get_all_vectors(db)
    
    if not target_vectors:
        return []

    query_vector = core.search_engine.encode_single_item(item_data)

    top_item_ids = core.search_engine.sort_by_similarity(
        query_vector, 
        target_vectors, 
        top_k=3
    )
    return await item_crud.get_items_by_ids(db, top_item_ids)

@router.post("/aiSearch", response_model=AiSearchResponse)
async def ai_search_endpoint(payload: AiSearchRequest, db: AsyncSession = Depends(get_db)):

    messages = [m.model_dump(exclude_none=True) for m in payload.history]
    
    messages.append({"role": "user", "content": payload.message})

    if not any(m["role"] == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    final_reply = ""
    recommended_items = []


    for _ in range(10):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS
        )
        response_msg = response.choices[0].message
        
        if response_msg.content and not response_msg.tool_calls:
            final_reply = response_msg.content
            messages.append({"role": "assistant", "content": final_reply})
            break

        messages.append(response_msg.model_dump(exclude_none=True))

        for tool_call in response_msg.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            content = "" 

            if func_name == "find_category_id":
                result = await category_crud.find_category_id(db, args["keyword"])
                content = json.dumps(result)

            elif func_name == "search_similar_items":
                valid_params = ["category_id", "name", "price", "condition_id"]
                filtered_args = {k: v for k, v in args.items() if k in valid_params}
                
                recommended_items = await search_similar_items(db, **filtered_args)
                content = json.dumps([{"id": i.id, "title": i.title} for i in recommended_items])
            
            elif func_name == "find_brand_id":
                result = await brand_crud.find_brands(db, args["keyword"])
                content = json.dumps([{"id": b.id, "name": b.name} for b in result])

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": func_name,
                "content": content
            })
            
    if not final_reply:
        final_reply = "条件に合う商品を検索しました。結果をご確認ください。"

    return AiSearchResponse(
        reply=final_reply,
        history=messages, 
        items=recommended_items
    )

PREDICT_SYSTEM_PROMPT = """
You are an expert listing assistant. Your task is to predict the `category_id` and `brand_id` for an item.

1. Analyze the item title.
2. CALL `find_category_id` and `find_brand_id` using ENGLISH keywords to get candidates.
3. The tools will return a list of candidates. YOU MUST CHOOSE THE BEST MATCH from the list.
   - **Consistency Check**: Ensure the chosen Category and Brand are logically compatible. 
     (e.g., If the category is "Computers", do NOT choose a brand like "Mac Cosmetics").
   - **Context Matters**: "Mac" in "MacBook" usually refers to "Apple" (Category: Laptop), not "Mac Cosmetics".
   - If multiple candidates are returned, pick the one that matches the item best. 
   - Do NOT return null if there are valid candidates in the tool output.
4. OUTPUT a JSON object with the elected IDs.
   Format: `{"category_id": <int>, "brand_id": <int>}`
5. Do NOT output any conversational text. Only the JSON object.
"""

@router.post("/ai/suggest", response_model=PredictResponse, operation_id="predict_attributes", tags=["AI"])
async def suggest_attributes(payload: PredictRequest, db: AsyncSession = Depends(get_db)):
    print(f"DEBUG: Analyzing item: {payload.title}")
    messages = [
        {"role": "system", "content": PREDICT_SYSTEM_PROMPT},
        {"role": "user", "content": f"Item Title: {payload.title}\nDescription: {payload.description or ''}"}
    ]
    
    suggest_tools = [t for t in TOOLS if t["function"]["name"] in ["find_category_id", "find_brand_id"]]
    
    final_response = PredictResponse()
    
    for i in range(5):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=suggest_tools,
                tool_choice="auto" 
            )
        except Exception as e:
            print(f"ERROR: OpenAI API call failed: {e}")
            break
        
        response_msg = response.choices[0].message
        
        if response_msg.tool_calls:
            print(f"DEBUG: Tool calls triggered: {[t.function.name for t in response_msg.tool_calls]}")
            messages.append(response_msg.model_dump(exclude_none=True))
            for tool_call in response_msg.tool_calls:
                func_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                    print(f"DEBUG: Tool '{func_name}' called with args: {args}")
                except json.JSONDecodeError:
                    print(f"ERROR: Failed to parse arguments for {func_name}")
                    continue

                content = ""
                
                if func_name == "find_category_id":
                    result = await category_crud.find_category_id(db, args["keyword"])
                    print(f"DEBUG: find_category_id found {len(result)} results for '{args.get('keyword')}'")
                    content = json.dumps(result)
                elif func_name == "find_brand_id":
                    result = await brand_crud.find_brands(db, args["keyword"])
                    print(f"DEBUG: find_brand_id found {len(result)} results for '{args.get('keyword')}'")
                    content = json.dumps([{"id": b.id, "name": b.name} for b in result])
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": func_name,
                    "content": content
                })
        else:
            if response_msg.content:
                txt = response_msg.content.strip()
                print(f"DEBUG: Model response (Attempt {i}): {txt}")
                
                # Try to extract JSON from code blocks or raw text
                json_str = txt
                if "```json" in txt:
                    json_str = txt.split("```json")[1].split("```")[0].strip()
                elif "```" in txt:
                    json_str = txt.split("```")[1].split("```")[0].strip()
                else:
                    # Attempt to find the first '{' and last '}'
                    start = txt.find("{")
                    end = txt.rfind("}")
                    if start != -1 and end != -1:
                        json_str = txt[start:end+1]

                try:
                    data = json.loads(json_str)
                    
                    cat_id = data.get("category_id")
                    br_id = data.get("brand_id")
                    
                    cat_path = []
                    brand_obj = None
                    
                    if cat_id:
                        cat_path = await category_crud.get_category_path(db, cat_id)
                        
                    if br_id:
                        brand_obj = await brand_crud.get_brand_by_id(db, br_id)

                    final_response = PredictResponse(
                        category_id=cat_id,
                        brand_id=br_id,
                        category_path=cat_path,
                        brand=brand_obj
                    )
                    print(f"DEBUG: Successfully parsed IDs: {final_response}")
                except json.JSONDecodeError:
                    print(f"ERROR: Failed to parse JSON from AI response: {txt}")
                    # If parsing guarantees failure, we might want to continue or retry? 
                    # For now, just break as we usually end here.
                    pass
            break
            
    return final_response