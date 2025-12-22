from pydantic import BaseModel

class Brand(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
