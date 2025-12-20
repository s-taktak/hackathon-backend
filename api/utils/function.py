tools = [
    {
        "type": "function",
        "function": {
            "name": "find_category_id",
            "description": "ユーザーが探している商品に最適なカテゴリーIDを見つけるために、キーワードで検索します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "検索キーワード（例：'shoes', 'electronics', 'toys'）"
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
                    "price": {"type": "number"}
                },
                "required": ["category_id", "name"]
            }
        }
    }
]