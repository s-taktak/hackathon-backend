TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_category_id",
            "description": "商品に最適なカテゴリーIDを特定します。引数のキーワードは必ず【英語】で入力してください（例: 'laptop', 'sneakers', 'camera'）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string", 
                        "description": "英語の検索キーワード（depth 1の特定用）"
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_similar_items",
            "description": "カテゴリーIDと商品名、価格などで類似商品を検索します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "category_id": {"type": "integer", "description": "find_category_idで取得したID"},
                    "name": {"type": "string", "description": "英語の商品名キーワード"},
                    "price": {
                        "type": "number", 
                        "description": "ユーザーが希望する価格（数値のみ）。特に指定がない場合は 0 を入力してください。"
                    },
                    "condition_id": {
                        "type": "integer",
                        "description": "商品の状態。1:新品、2:未使用に近い、3:目立った傷なし、4:やや傷あり、5:傷や汚れあり"
                    }
                },
                "required": ["category_id", "name"]
            }
        }
    }
]