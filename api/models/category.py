from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from api.db import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    depth = Column(Integer, nullable=False) 

    items = relationship("Item", back_populates="category")
    
    children = relationship("Category", back_populates="parent")
    parent = relationship("Category", remote_side=[id], back_populates="children")