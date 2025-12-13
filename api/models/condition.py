from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from api.db import Base

class ItemCondition(Base):
    __tablename__ = "item_conditions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)  
    sort_order = Column(Integer, nullable=False)

    items = relationship("Item", back_populates="condition")