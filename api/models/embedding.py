from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from api.db import Base

class ItemVector(Base):
    __tablename__ = "item_vectors"

    item_id = Column(String(36), ForeignKey("items.id"), primary_key=True)
    
    embedding = Column(JSON, nullable=False)

    item = relationship("Item", back_populates="vector")