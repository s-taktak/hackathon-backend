from pydantic import BaseModel
from typing import Optional

class PredictRequest(BaseModel):
    title: str
    description: Optional[str] = None

class PredictResponse(BaseModel):
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
