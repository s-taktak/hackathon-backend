from pydantic import BaseModel
from typing import List, Optional
from api.schemas.item import ItemResponse 

class ChatMessage(BaseModel):
    role: str 
    content: Optional[str] = None
    name: Optional[str] = None 
    tool_call_id: Optional[str] = None 

class AiSearchRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class AiSearchResponse(BaseModel):
    reply: str
    history: List[ChatMessage]
    items: Optional[List[ItemResponse]] = []

class AiPredictRequest(BaseModel):
    title: str

class AiPredictResponse(BaseModel):
    category_id: Optional[int] = None
    brand_id: Optional[int] = None