from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from api.db import Base

class ItemImage(Base):
    __tablename__ = "item_images"

    id = Column(String(36), primary_key=True)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    image_url = Column(String(2048), nullable=False)
    
    created_at = Column(DateTime, nullable=False)

    item = relationship("Item", back_populates="images")