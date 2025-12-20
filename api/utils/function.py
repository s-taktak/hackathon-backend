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
            "description": "指定されたカテゴリーIDと特徴から商品を推薦します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "category_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "price": {"type": "number"},
                    "condition_id": {"type": "integer"}
                },
                "required": ["category_id", "name"]
            }
        }
    }
]