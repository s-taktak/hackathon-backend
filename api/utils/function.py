TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_category_id",
            "description": "Identify the optimal category ID for an item. The keyword must be in English (e.g., 'laptop', 'sneakers', 'camera').",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string", 
                        "description": "Search keyword in English (for finding depth 1 categories)"
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
            "description": "Search for similar items based on category ID, item name, price, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category_id": {"type": "integer", "description": "ID obtained from find_category_id"},
                    "name": {"type": "string", "description": "Product name keyword in English"},
                    "price": {
                        "type": "number", 
                        "description": "User's budget price. Use 0 if not specified."
                    },
                    "condition_id": {
                        "type": "integer",
                        "description": "Item condition. 1:New, 2:Like New, 3:No visible scratches, 4:Slightly scratched, 5:Scratched/Dirty"
                    }
                },
                "required": ["category_id", "name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_brands",
            "description": "Search for brand IDs based on a keyword. Input keyword must be in English.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string", 
                        "description": "Brand search keyword in English"
                    }
                },
                "required": ["keyword"]
            }
        }
    }
]