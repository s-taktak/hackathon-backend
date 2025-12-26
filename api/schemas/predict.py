from pydantic import BaseModel
from typing import Optional, List
from api.schemas.brand import Brand
import api.schemas.item as item_schema

class PredictRequest(BaseModel):
    title: str
    description: Optional[str] = None

class PredictResponse(BaseModel):
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    category_path: Optional[List[item_schema.Category]] = None
    brand: Optional[Brand] = None
